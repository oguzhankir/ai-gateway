"""Gateway service for orchestrating request processing."""

import time
import asyncio
from typing import List, Dict, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from datetime import datetime, timedelta

from app.core.rate_limiter import rate_limiter
from app.core.exceptions import GuardrailViolationException, BudgetExceededException
from app.pii.detector import pii_detector
from app.pii.masker import pii_masker
from app.guardrails.engine import guardrail_engine
from app.cache.semantic_cache import semantic_cache
from app.providers.fallback import fallback_manager
from app.providers.router import ab_router
from app.providers.factory import provider_factory
from app.config import config_manager
from app.services.audit_service import AuditService
from app.services.budget_service import BudgetService
from app.services.webhook_service import WebhookService
from app.db.repositories.guardrail_repo import GuardrailRepository
from app.db.session import AsyncSessionLocal
from app.schemas.gateway import GatewayResponse
from app.utils.logger import get_logger
from app.core.metrics import total_requests, cache_hits, pii_detections, request_duration, tokens_per_request, cost_per_request, errors

logger = get_logger(__name__)


class GatewayService:
    """Service for processing gateway requests."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_service = AuditService(db)
        self.budget_service = BudgetService(db)
        self.webhook_service = WebhookService(db)

    async def process_request(
        self,
        user_id: UUID,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        detection_mode: str = "fast",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> GatewayResponse:
        """
        Process a gateway request.

        Args:
            user_id: User ID
            messages: List of messages
            model: Model name
            provider: Provider name
            detection_mode: PII detection mode
            max_tokens: Maximum tokens
            temperature: Sampling temperature

        Returns:
            GatewayResponse
        """
        start_time = time.time()
        request_id = None
        cache_hit = False
        pii_detected = False
        pii_entities = []
        guardrail_violations = None

        try:
            # 1. Rate limit check
            await rate_limiter.check_rate_limit(str(user_id))

            # 2. Extract text from messages for PII detection
            text_content = " ".join([msg.get("content", "") for msg in messages])

            # 3. PII detection on input
            pii_result = pii_detector.detect(text_content, detection_mode)
            pii_detected = len(pii_result.entities) > 0
            pii_entities = pii_result.entities

            if pii_detected:
                pii_detections.labels(pii_type="input").inc()

            # 4. Guardrails check on input
            guardrail_result = guardrail_engine.check(
                text=text_content,
                pii_entities=pii_entities,
            )

            if not guardrail_result.passed:
                guardrail_violations = [v.__dict__ for v in guardrail_result.violations]
                # Log guardrail violations to database
                asyncio.create_task(
                    self._log_guardrail_violations(
                        user_id=user_id,
                        violations=guardrail_result.violations,
                        request_id=None,  # Will be set after request is logged
                    )
                )
                if guardrail_result.should_block:
                    raise GuardrailViolationException(
                        "Guardrail violation",
                        guardrail_result.violations,
                    )

            # 5. Masking
            masked_text = text_content
            session_id = ""
            if pii_detected and config_manager.get("pii.masking.enabled", True):
                masked_text, session_id = await pii_masker.mask(text_content, pii_entities)
                # Update messages with masked content
                messages = [
                    {**msg, "content": masked_text if i == len(messages) - 1 else msg.get("content", "")}
                    for i, msg in enumerate(messages)
                ]

            # 6. Cache lookup
            cached_response = None
            if config_manager.get("cache.enabled", True):
                cached_response = await semantic_cache.get(text_content)
                if cached_response:
                    cache_hit = True
                    cache_hits.inc()
                    logger.info(f"Cache hit for request {request_id}")

            # 7. Budget check (only if not cache hit)
            if not cache_hit:
                # Estimate cost (rough estimate)
                estimated_tokens = len(text_content.split()) * 1.3  # Rough estimate
                estimated_cost = estimated_tokens * 0.000002  # Rough estimate
                await self.budget_service.check_budget(user_id, estimated_cost)

            # 8. Provider call with fallback
            if cache_hit:
                # Convert cached response dict to ProviderResponse-like object
                # Cache hit means no cost - set cost to 0
                from app.providers.base import ProviderResponse
                provider_response = ProviderResponse(
                    completion=cached_response.get("completion", ""),
                    prompt_tokens=cached_response.get("prompt_tokens", 0),
                    completion_tokens=cached_response.get("completion_tokens", 0),
                    total_tokens=cached_response.get("total_tokens", 0),
                    cost_usd=0.0,  # Cache hit = no cost
                    model=cached_response.get("model", model or "unknown"),
                    provider=cached_response.get("provider", provider or "unknown"),
                )
            else:
                # Determine provider and model
                if not provider:
                    provider, model = ab_router.route_request()

                if not model:
                    model = config_manager.get(f"providers.{provider}.default_model", "gpt-3.5-turbo")

                # Call provider with fallback
                provider_response = await fallback_manager.execute_with_fallback(
                    messages=messages,
                    model=model,
                    provider=provider,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                # 9. Cache set
                if config_manager.get("cache.enabled", True):
                    # Store ProviderResponse as dict for caching
                    cache_data = {
                        "completion": provider_response.completion,
                        "prompt_tokens": provider_response.prompt_tokens,
                        "completion_tokens": provider_response.completion_tokens,
                        "total_tokens": provider_response.total_tokens,
                        "cost_usd": provider_response.cost_usd,
                        "model": provider_response.model,
                        "provider": provider_response.provider,
                    }
                    await semantic_cache.set(text_content, cache_data)

            # 10. Guardrails check on output
            completion_text = provider_response.completion
            pii_result_output = pii_detector.detect(completion_text, detection_mode)
            
            if len(pii_result_output.entities) > 0:
                guardrail_result_output = guardrail_engine.check(
                    text=completion_text,
                    pii_entities=pii_result_output.entities,
                )
                if not guardrail_result_output.passed:
                    # Log guardrail violations to database
                    asyncio.create_task(
                        self._log_guardrail_violations(
                            user_id=user_id,
                            violations=guardrail_result_output.violations,
                            request_id=None,  # Will be set after request is logged
                        )
                    )
                    if guardrail_result_output.should_block:
                        raise GuardrailViolationException(
                            "PII detected in output",
                            guardrail_result_output.violations,
                        )

            # 11. Unmasking
            if session_id:
                completion_text = await pii_masker.unmask(completion_text, session_id)

            # 12. Calculate metrics
            duration_ms = int((time.time() - start_time) * 1000)
            prompt_tokens = provider_response.prompt_tokens
            completion_tokens = provider_response.completion_tokens
            total_tokens = provider_response.total_tokens
            cost = provider_response.cost_usd
            model_used = provider_response.model
            provider_used = provider_response.provider

            # Update metrics
            total_requests.labels(provider=provider_used, model=model_used, status="completed").inc()
            request_duration.labels(provider=provider_used, model=model_used).observe(duration_ms / 1000)
            tokens_per_request.labels(token_type="prompt").observe(prompt_tokens)
            tokens_per_request.labels(token_type="completion").observe(completion_tokens)
            cost_per_request.labels(provider=provider_used, model=model_used).observe(cost)

            # 13. Track spend
            if not cache_hit:
                await self.budget_service.track_spend(user_id, cost)

            # 14. Audit logging (async, don't wait)
            # Store request_id for guardrail logging
            logged_request_id = None
            async def log_and_get_id():
                nonlocal logged_request_id
                request_log = await self.audit_service.log_request(
                    user_id=user_id,
                    provider=provider_used,
                    model=model_used,
                    messages=messages,
                    completion=completion_text,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    cost_usd=cost,
                    duration_ms=duration_ms,
                    cache_hit=cache_hit,
                    pii_detected=pii_detected,
                    pii_entities=pii_entities,
                    status="completed",
                    guardrail_violations=guardrail_violations,
                )
                if request_log:
                    logged_request_id = request_log.id
                    # Update guardrail logs with request_id if violations exist
                    if guardrail_violations:
                        await self._update_guardrail_logs_request_id(
                            user_id=user_id,
                            request_id=logged_request_id,
                        )
            
            asyncio.create_task(log_and_get_id())

            # 15. Webhook trigger
            asyncio.create_task(
                self.webhook_service.trigger_event(
                    "request.completed",
                    {
                        "request_id": str(request_id) if request_id else None,
                        "user_id": str(user_id),
                        "provider": provider_used,
                        "model": model_used,
                        "tokens": total_tokens,
                        "cost": cost,
                        "timestamp": time.time(),
                    },
                )
            )

            return GatewayResponse(
                completion=completion_text,
                tokens={
                    "prompt": prompt_tokens,
                    "completion": completion_tokens,
                    "total": total_tokens,
                },
                cost=cost,
                cache_hit=cache_hit,
                pii_detected=pii_detected,
                pii_entities=[e.to_dict() for e in pii_entities] if pii_entities else None,
                duration_ms=duration_ms,
                model=model_used,
                provider=provider_used,
                request_id=str(request_id) if request_id else None,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_status = "failed"
            
            if isinstance(e, GuardrailViolationException):
                error_status = "blocked"
            elif isinstance(e, BudgetExceededException):
                error_status = "budget_exceeded"

            total_requests.labels(provider=provider or "unknown", model=model or "unknown", status=error_status).inc()
            errors.labels(error_type=type(e).__name__, provider=provider or "unknown").inc()

            # Log guardrail violations if this is a guardrail exception
            if isinstance(e, GuardrailViolationException):
                asyncio.create_task(
                    self._log_guardrail_violations(
                        user_id=user_id,
                        violations=e.violations,
                        request_id=None,  # Will be set after request is logged
                    )
                )

            # Log error
            async def log_error_and_update():
                request_log = await self.audit_service.log_request(
                    user_id=user_id,
                    provider=provider or "unknown",
                    model=model or "unknown",
                    messages=messages,
                    completion="",
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    cost_usd=0.0,
                    duration_ms=duration_ms,
                    status=error_status,
                    error_message=str(e),
                    guardrail_violations=guardrail_violations,
                )
                # Update guardrail logs with request_id if violations exist
                if request_log and guardrail_violations:
                    await self._update_guardrail_logs_request_id(
                        user_id=user_id,
                        request_id=request_log.id,
                    )
            
            asyncio.create_task(log_error_and_update())

            # Trigger webhook
            asyncio.create_task(
                self.webhook_service.trigger_event(
                    "request.failed",
                    {
                        "user_id": str(user_id),
                        "error": str(e),
                        "timestamp": time.time(),
                    },
                )
            )

            raise

    async def _log_guardrail_violations(
        self,
        user_id: UUID,
        violations: List,
        request_id: Optional[UUID] = None,
    ):
        """
        Log guardrail violations to database.

        Args:
            user_id: User ID
            violations: List of GuardrailViolation objects
            request_id: Request ID (optional, can be set later)
        """
        if not violations:
            return

        async with AsyncSessionLocal() as db:
            try:
                guardrail_repo = GuardrailRepository(db)
                for violation in violations:
                    # Get action from rule if available, otherwise use default
                    action = 'log'
                    if hasattr(violation, 'action'):
                        action = violation.action
                    elif hasattr(violation, '__dict__'):
                        violation_dict = violation.__dict__
                        action = violation_dict.get('action', 'log')
                    
                    await guardrail_repo.create(
                        user_id=user_id,
                        rule_name=violation.rule_name,
                        severity=violation.severity,
                        action=action,
                        request_id=request_id,
                        details={
                            "message": violation.message,
                            **(violation.details or {}),
                        },
                    )
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to log guardrail violations: {e}")
                await db.rollback()

    async def _update_guardrail_logs_request_id(
        self,
        user_id: UUID,
        request_id: UUID,
    ):
        """
        Update guardrail logs with request_id for recently created violations.

        Args:
            user_id: User ID
            request_id: Request ID to set
        """
        async with AsyncSessionLocal() as db:
            try:
                from app.db.models.guardrail_log import GuardrailLog
                
                # Update violations from last minute without request_id
                cutoff_time = datetime.utcnow() - timedelta(seconds=60)
                await db.execute(
                    update(GuardrailLog)
                    .where(
                        GuardrailLog.user_id == user_id,
                        GuardrailLog.request_id.is_(None),
                        GuardrailLog.timestamp >= cutoff_time,
                    )
                    .values(request_id=request_id)
                )
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to update guardrail logs request_id: {e}")
                await db.rollback()


"""PII masking and unmasking utilities."""

import re
import secrets
import asyncio
from typing import Dict, Optional
import redis.asyncio as aioredis
import json

from app.config import config_manager, settings
from app.pii.entities import PIIEntity


class PIIMasker:
    """PII masker for masking and unmasking PII in text."""

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._lock = asyncio.Lock()
        self._ttl = config_manager.get("pii.masking.session_ttl", 3600)

    async def initialize(self):
        """Initialize Redis connection."""
        self.redis = await aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.aclose()

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return f"session_{secrets.token_urlsafe(16)}"

    async def mask(self, text: str, entities: list[PIIEntity]) -> tuple[str, str]:
        """
        Mask PII entities in text.

        Args:
            text: Text containing PII
            entities: List of PII entities to mask

        Returns:
            Tuple of (masked_text, session_id)
        """
        if not entities:
            return text, ""

        async with self._lock:
            session_id = self._generate_session_id()
            mapping: Dict[str, str] = {}

            # Sort entities by start position (reverse to maintain indices)
            sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)

            masked_text = text
            for idx, entity in enumerate(sorted_entities):
                entity_id = f"{entity.type.value}_{idx}"
                mask = f"<{entity.type.value}:{session_id}:{entity_id}>"
                
                # Replace in text
                masked_text = (
                    masked_text[:entity.start] + mask + masked_text[entity.end:]
                )
                
                # Store mapping
                mapping[entity_id] = entity.text

            # Store mapping in Redis
            if self.redis:
                await self.redis.setex(
                    f"mask:{session_id}",
                    self._ttl,
                    json.dumps(mapping),
                )

            return masked_text, session_id

    async def unmask(self, text: str, session_id: str) -> str:
        """
        Unmask PII entities in text.

        Args:
            text: Text with masked PII
            session_id: Session ID for mapping

        Returns:
            Unmasked text
        """
        if not session_id or not self.redis:
            return text

        async with self._lock:
            # Retrieve mapping from Redis
            mapping_data = await self.redis.get(f"mask:{session_id}")
            if not mapping_data:
                return text  # Mapping expired or not found

            mapping = json.loads(mapping_data)

            # Find all masked patterns
            pattern = re.compile(
                rf"<([A-Z_]+):{re.escape(session_id)}:([A-Z_]+_\d+)>"
            )

            def replace_match(match):
                entity_type = match.group(1)
                entity_id = match.group(2)
                if entity_id in mapping:
                    return mapping[entity_id]
                return match.group(0)  # Return original if not found

            unmasked_text = pattern.sub(replace_match, text)

            # Delete mapping after unmasking
            await self.redis.delete(f"mask:{session_id}")

            return unmasked_text


# Singleton instance
pii_masker = PIIMasker()


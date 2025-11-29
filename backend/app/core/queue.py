"""Redis Streams-based queue for async request processing."""

import asyncio
import json
from typing import Optional, Dict, Any
import redis.asyncio as aioredis

from app.config import config_manager, settings
from app.core.exceptions import DatabaseException


class Queue:
    """Redis Streams-based queue."""

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._enabled = config_manager.get("queue.enabled", False)
        self._stream_name = config_manager.get("queue.stream_name", "requests")
        self._consumer_group = config_manager.get("queue.consumer_group", "workers")
        self._workers = config_manager.get("queue.workers", 2)
        self._batch_size = config_manager.get("queue.batch_size", 10)
        self._running = False
        self._tasks: list = []

    async def initialize(self):
        """Initialize Redis connection and create consumer group."""
        if not self._enabled:
            return

        self.redis = await aioredis.from_url(
            settings.redis_url,
            decode_responses=False,
        )

        # Create consumer group if it doesn't exist
        try:
            await self.redis.xgroup_create(
                name=self._stream_name,
                groupname=self._consumer_group,
                id="0",
                mkstream=True,
            )
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def close(self):
        """Close Redis connection and stop workers."""
        self._running = False
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        if self.redis:
            await self.redis.aclose()

    async def enqueue(self, data: Dict[str, Any]) -> str:
        """
        Enqueue a request.

        Args:
            data: Request data to enqueue

        Returns:
            Message ID
        """
        if not self._enabled or not self.redis:
            raise DatabaseException("Queue is not enabled or not initialized")

        message_id = await self.redis.xadd(
            self._stream_name,
            {"data": json.dumps(data)},
        )
        return message_id.decode() if isinstance(message_id, bytes) else message_id

    async def start_workers(self, process_request_func):
        """
        Start worker tasks.

        Args:
            process_request_func: Function to process requests
        """
        if not self._enabled:
            return

        self._running = True
        for i in range(self._workers):
            task = asyncio.create_task(self._worker(f"worker-{i}", process_request_func))
            self._tasks.append(task)

    async def _worker(self, worker_id: str, process_request_func):
        """
        Worker loop to process requests from stream.

        Args:
            worker_id: Worker identifier
            process_request_func: Function to process requests
        """
        while self._running:
            try:
                # Read messages from stream
                messages = await self.redis.xreadgroup(
                    groupname=self._consumer_group,
                    consumername=worker_id,
                    streams={self._stream_name: ">"},
                    count=self._batch_size,
                    block=1000,  # Block for 1 second
                )

                if not messages:
                    continue

                for stream, message_list in messages:
                    for message_id, fields in message_list:
                        try:
                            # Parse message data
                            data_str = fields.get(b"data", b"{}").decode()
                            data = json.loads(data_str)

                            # Process request
                            await process_request_func(data)

                            # Acknowledge message
                            await self.redis.xack(
                                self._stream_name,
                                self._consumer_group,
                                message_id,
                            )
                        except Exception as e:
                            # Log error and continue
                            print(f"Error processing message {message_id}: {e}")
                            # Optionally, move to dead letter queue
                            continue

            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)


# Singleton instance
queue = Queue()


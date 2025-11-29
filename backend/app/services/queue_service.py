"""Queue service wrapper."""

from app.core.queue import queue


class QueueService:
    """Service wrapper for queue operations."""

    @staticmethod
    async def enqueue(data: dict) -> str:
        """
        Enqueue a request.

        Args:
            data: Request data

        Returns:
            Message ID
        """
        return await queue.enqueue(data)


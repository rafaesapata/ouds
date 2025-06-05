"""Memory module for agent."""
from typing import List, Optional

from app.schema import Message


class Memory:
    """Memory for agent."""

    def __init__(self):
        """Initialize memory."""
        self.messages: List[Message] = []

    def add_message(self, message: Message) -> None:
        """Add message to memory."""
        self.messages.append(message)

    def get_messages(self) -> List[Message]:
        """Get all messages."""
        return self.messages

    def clear(self) -> None:
        """Clear memory."""
        self.messages = []

    def get_last_message(self) -> Optional[Message]:
        """Get last message."""
        if not self.messages:
            return None
        return self.messages[-1]


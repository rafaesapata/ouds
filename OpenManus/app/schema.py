from enum import Enum
from enum import Enum
from typing import Any, List, Literal, Optional, Union, Dict

from pydantic import BaseModel, Field


class Role(str, Enum):
    """Message role options"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


ROLE_VALUES = tuple(role.value for role in Role)
ROLE_TYPE = Literal[ROLE_VALUES]  # type: ignore


class ToolChoice(str, Enum):
    """Tool choice options"""

    NONE = "none"
    AUTO = "auto"
    REQUIRED = "required"


TOOL_CHOICE_VALUES = tuple(choice.value for choice in ToolChoice)
TOOL_CHOICE_TYPE = Literal[TOOL_CHOICE_VALUES]  # type: ignore


class AgentState(str, Enum):
    """Agent execution states"""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"


class Function(BaseModel):
    name: str
    arguments: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Function":
        """Create Function from dictionary.
        
        Args:
            data: Dictionary containing function data
            
        Returns:
            Function instance
        """
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data)}")
        
        return cls(
            name=data.get("name", ""),
            arguments=data.get("arguments", "")
        )
    
    def model_dump(self) -> Dict[str, Any]:
        """Convert to dictionary format.
        
        Returns:
            Dictionary representation of the function
        """
        return {
            "name": self.name,
            "arguments": self.arguments
        }


class ToolCall(BaseModel):
    """Represents a tool/function call in a message"""

    id: str
    type: str = "function"
    function: Function
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        """Create ToolCall from dictionary.
        
        Args:
            data: Dictionary containing tool call data
            
        Returns:
            ToolCall instance
        """
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data)}")
        
        function_data = data.get("function", {})
        if not isinstance(function_data, dict):
            function_data = {}
        
        function = Function.from_dict(function_data)
        
        return cls(
            id=data.get("id", ""),
            type=data.get("type", "function"),
            function=function
        )


class Message(BaseModel):
    """Represents a chat message in the conversation"""

    role: ROLE_TYPE = Field(...)  # type: ignore
    content: Optional[str] = Field(default=None)
    tool_calls: Optional[List[ToolCall]] = Field(default=None)
    name: Optional[str] = Field(default=None)
    tool_call_id: Optional[str] = Field(default=None)
    base64_image: Optional[str] = Field(default=None)

    def __add__(self, other) -> List["Message"]:
        """支持 Message + list 或 Message + Message 的操作"""
        if isinstance(other, list):
            return [self] + other
        elif isinstance(other, Message):
            return [self, other]
        else:
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'"
            )

    def __radd__(self, other) -> List["Message"]:
        """支持 list + Message 的操作"""
        if isinstance(other, list):
            return other + [self]
        else:
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(other).__name__}' and '{type(self).__name__}'"
            )

    def to_dict(self) -> dict:
        """Convert message to dictionary format"""
        message = {"role": self.role}
        if self.content is not None:
            message["content"] = self.content
        if self.tool_calls is not None:
            message["tool_calls"] = [tool_call.dict() for tool_call in self.tool_calls]
        if self.name is not None:
            message["name"] = self.name
        if self.tool_call_id is not None:
            message["tool_call_id"] = self.tool_call_id
        if self.base64_image is not None:
            message["base64_image"] = self.base64_image
        return message

    @classmethod
    def user_message(
        cls, content: str, base64_image: Optional[str] = None
    ) -> "Message":
        """Create a user message"""
        return cls(role=Role.USER, content=content, base64_image=base64_image)

    @classmethod
    def system_message(cls, content: str) -> "Message":
        """Create a system message"""
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def assistant_message(
        cls, content: Optional[str] = None, base64_image: Optional[str] = None
    ) -> "Message":
        """Create an assistant message"""
        return cls(role=Role.ASSISTANT, content=content, base64_image=base64_image)

    @classmethod
    def tool_message(
        cls, content: str, name, tool_call_id: str, base64_image: Optional[str] = None
    ) -> "Message":
        """Create a tool message"""
        return cls(
            role=Role.TOOL,
            content=content,
            name=name,
            tool_call_id=tool_call_id,
            base64_image=base64_image,
        )

    @classmethod
    def from_tool_calls(
        cls,
        tool_calls: List[Any],
        content: Union[str, List[str]] = "",
        base64_image: Optional[str] = None,
        **kwargs,
    ):
        """Create ToolCallsMessage from raw tool calls.

        Args:
            tool_calls: Raw tool calls from LLM
            content: Optional message content
            base64_image: Optional base64 encoded image
        """
        formatted_calls = []
        
        for call in tool_calls:
            try:
                # Handle different types of tool calls
                if hasattr(call, "function") and hasattr(call.function, "model_dump"):
                    # Case 1: call is a pydantic model with model_dump method
                    formatted_calls.append({
                        "id": call.id,
                        "function": call.function.model_dump(),
                        "type": "function"
                    })
                elif hasattr(call, "function") and hasattr(call.function, "dict"):
                    # Case 2: call is a pydantic model with dict method
                    formatted_calls.append({
                        "id": call.id,
                        "function": call.function.dict(),
                        "type": "function"
                    })
                elif isinstance(call, dict) and "function" in call:
                    # Case 3: call is a dictionary
                    function_data = call["function"]
                    if isinstance(function_data, dict):
                        # Function is already a dictionary
                        formatted_calls.append({
                            "id": call.get("id", ""),
                            "function": {
                                "name": function_data.get("name", ""),
                                "arguments": function_data.get("arguments", "")
                            },
                            "type": call.get("type", "function")
                        })
                    elif hasattr(function_data, "model_dump"):
                        # Function has model_dump method
                        formatted_calls.append({
                            "id": call.get("id", ""),
                            "function": function_data.model_dump(),
                            "type": call.get("type", "function")
                        })
                    elif hasattr(function_data, "dict"):
                        # Function has dict method
                        formatted_calls.append({
                            "id": call.get("id", ""),
                            "function": function_data.dict(),
                            "type": call.get("type", "function")
                        })
                    else:
                        # Function is an object with name and arguments attributes
                        formatted_calls.append({
                            "id": call.get("id", ""),
                            "function": {
                                "name": getattr(function_data, "name", ""),
                                "arguments": getattr(function_data, "arguments", "")
                            },
                            "type": call.get("type", "function")
                        })
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Error formatting tool call: {e}")
                continue
        
        return cls(
            role=Role.ASSISTANT,
            content=content,
            tool_calls=formatted_calls,
            base64_image=base64_image,
            **kwargs,
        )


class Memory(BaseModel):
    messages: List[Message] = Field(default_factory=list)
    max_messages: int = Field(default=100)

    def add_message(self, message: Message) -> None:
        """Add a message to memory"""
        self.messages.append(message)
        # Optional: Implement message limit
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def add_messages(self, messages: List[Message]) -> None:
        """Add multiple messages to memory"""
        self.messages.extend(messages)
        # Optional: Implement message limit
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def clear(self) -> None:
        """Clear all messages"""
        self.messages.clear()

    def get_recent_messages(self, n: int) -> List[Message]:
        """Get n most recent messages"""
        return self.messages[-n:]

    def to_dict_list(self) -> List[dict]:
        """Convert messages to list of dicts"""
        return [msg.to_dict() for msg in self.messages]


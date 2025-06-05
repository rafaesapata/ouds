import math
import asyncio
import json
from typing import Dict, List, Optional, Union, Any, AsyncGenerator

import tiktoken
from openai import (
    APIError,
    AsyncAzureOpenAI,
    AsyncOpenAI,
    AuthenticationError,
    OpenAIError,
    RateLimitError,
)
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from app.bedrock import BedrockClient
from app.config import LLMSettings, config
from app.exceptions import TokenLimitExceeded
from app.logger import logger  # Assuming a logger is set up in your app
from app.schema import (
    ROLE_VALUES,
    TOOL_CHOICE_TYPE,
    TOOL_CHOICE_VALUES,
    Message,
    ToolChoice,
)


REASONING_MODELS = ["o1", "o3-mini"]
MULTIMODAL_MODELS = [
    "gpt-4-vision-preview",
    "gpt-4o",
    "gpt-4o-mini",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
]


class TokenCounter:
    # Token constants
    BASE_MESSAGE_TOKENS = 4
    FORMAT_TOKENS = 2
    LOW_DETAIL_IMAGE_TOKENS = 85
    HIGH_DETAIL_TILE_TOKENS = 170

    def __init__(self, model: str):
        self.model = model
        self.encoding = self._get_encoding()

    def _get_encoding(self):
        """Get the appropriate encoding for the model."""
        try:
            if "gpt-4" in self.model or "gpt-3.5" in self.model:
                return tiktoken.encoding_for_model(self.model)
            else:
                # Default to cl100k_base for newer models
                return tiktoken.get_encoding("cl100k_base")
        except Exception:
            # Fallback to cl100k_base if model-specific encoding not found
            return tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        if not text:
            return 0
        return len(self.encoding.encode(text))

    def count_message_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Count the number of tokens in a list of messages.
        
        Format: {
            "role": "user" | "assistant" | "system",
            "content": str | List[Dict],
            "name": Optional[str],
            "tool_calls": Optional[List[Dict]]
        }
        """
        num_tokens = 0
        
        for message in messages:
            # Base tokens for each message
            num_tokens += self.BASE_MESSAGE_TOKENS
            
            # Count tokens for each field
            for key, value in message.items():
                if key == "content":
                    if isinstance(value, str):
                        num_tokens += self.count_tokens(value)
                    elif isinstance(value, list):
                        # Handle multimodal content
                        for item in value:
                            if isinstance(item, dict):
                                if item.get("type") == "text":
                                    num_tokens += self.count_tokens(item.get("text", ""))
                                elif item.get("type") == "image_url":
                                    # Estimate image tokens based on detail level
                                    detail = item.get("image_url", {}).get("detail", "auto")
                                    if detail == "low":
                                        num_tokens += self.LOW_DETAIL_IMAGE_TOKENS
                                    else:
                                        # For high detail or auto, estimate higher token count
                                        num_tokens += self.HIGH_DETAIL_TILE_TOKENS
                elif key == "name":
                    num_tokens += self.count_tokens(str(value))
                elif key == "tool_calls":
                    if isinstance(value, list):
                        for tool_call in value:
                            if isinstance(tool_call, dict):
                                # Count tokens for function name and arguments
                                function = tool_call.get("function", {})
                                num_tokens += self.count_tokens(function.get("name", ""))
                                num_tokens += self.count_tokens(function.get("arguments", ""))
        
        # Add format tokens
        num_tokens += self.FORMAT_TOKENS
        
        return num_tokens


class LLM:
    """LLM client for interacting with language models."""

    def __init__(self, settings: Optional[LLMSettings] = None):
        """Initialize the LLM client with settings."""
        self.settings = settings or config.llm
        self.model = self.settings.model
        self.token_counter = TokenCounter(self.model)
        self.client = self._get_client()

    def _get_client(self):
        """Get the appropriate client based on settings."""
        if self.settings.provider == "openai":
            return AsyncOpenAI(
                api_key=self.settings.api_key,
                base_url=self.settings.api_base,
                timeout=self.settings.timeout,
            )
        elif self.settings.provider == "azure":
            return AsyncAzureOpenAI(
                api_key=self.settings.api_key,
                api_version=self.settings.api_version,
                azure_endpoint=self.settings.api_base,
                timeout=self.settings.timeout,
            )
        elif self.settings.provider == "bedrock":
            return BedrockClient(
                model=self.model,
                region=self.settings.region,
                access_key=self.settings.access_key,
                secret_key=self.settings.secret_key,
            )
        else:
            raise ValueError(f"Unsupported provider: {self.settings.provider}")

    def count_message_tokens(self, messages: List[Union[dict, Message]]) -> int:
        """Count the number of tokens in a list of messages."""
        # Format messages for token counting
        formatted_messages = self.format_messages(messages)
        return self.token_counter.count_message_tokens(formatted_messages)

    def format_messages(
        self, messages: List[Union[dict, Message]], supports_images: bool = False
    ) -> List[Dict[str, Any]]:
        """Format messages for the API call."""
        formatted_messages = []

        for message in messages:
            if isinstance(message, Message):
                # Convert Message object to dict
                message_dict = message.to_dict()
                
                # Process base64 images if present and model supports images
                if supports_images and message.base64_image:
                    # Initialize or convert content to appropriate format
                    if not message_dict.get("content"):
                        message_dict["content"] = []
                    elif isinstance(message_dict["content"], str):
                        message_dict["content"] = [
                            {"type": "text", "text": message_dict["content"]}
                        ]
                    
                    # Add the image to content
                    message_dict["content"].append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{message.base64_image}"
                            },
                        }
                    )
                
                formatted_messages.append(message_dict)
            elif isinstance(message, dict):
                if "role" not in message:
                    raise ValueError("Message dict must contain 'role' field")

                # Process base64 images if present and model supports images
                if supports_images and message.get("base64_image"):
                    # Initialize or convert content to appropriate format
                    if not message.get("content"):
                        message["content"] = []
                    elif isinstance(message["content"], str):
                        message["content"] = [
                            {"type": "text", "text": message["content"]}
                        ]
                    elif isinstance(message["content"], list):
                        # Convert string items to proper text objects
                        message["content"] = [
                            (
                                {"type": "text", "text": item}
                                if isinstance(item, str)
                                else item
                            )
                            for item in message["content"]
                        ]

                    # Add the image to content
                    message["content"].append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{message['base64_image']}"
                            },
                        }
                    )

                    # Remove the base64_image field
                    del message["base64_image"]
                # If model doesn't support images but message has base64_image, handle gracefully
                elif not supports_images and message.get("base64_image"):
                    # Just remove the base64_image field and keep the text content
                    del message["base64_image"]

                if "content" in message or "tool_calls" in message:
                    formatted_messages.append(message)
                # else: do not include the message
            else:
                raise TypeError(f"Unsupported message type: {type(message)}")

        # Validate all messages have required fields
        for msg in formatted_messages:
            if msg["role"] not in ROLE_VALUES:
                raise ValueError(f"Invalid role: {msg['role']}")

        return formatted_messages

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type(
            (OpenAIError, Exception, ValueError)
        ),  # Don't retry TokenLimitExceeded
    )
    async def ask(
        self,
        messages: List[Union[dict, Message]],
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        stream: bool = True,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Send a prompt to the LLM and get the response.

        Args:
            messages: List of conversation messages
            system_msgs: Optional system messages to prepend
            stream (bool): Whether to stream the response
            temperature (float): Sampling temperature for the response

        Returns:
            str: The generated response

        Raises:
            TokenLimitExceeded: If token limits are exceeded
            ValueError: If messages are invalid or response is empty
            OpenAIError: If API call fails after retries
            Exception: For unexpected errors
        """
        try:
            # Check if the model supports images
            supports_images = self.model in MULTIMODAL_MODELS

            # Format system and user messages with image support check
            if system_msgs:
                system_msgs = self.format_messages(system_msgs, supports_images)
                messages = system_msgs + self.format_messages(messages, supports_images)
            else:
                messages = self.format_messages(messages, supports_images)

            # Calculate input token count
            input_tokens = self.count_message_tokens(messages)

            # Check if token limits are exceeded
            if input_tokens > self.settings.max_input_tokens:
                raise TokenLimitExceeded(
                    f"Input tokens ({input_tokens}) exceed limit ({self.settings.max_input_tokens})"
                )

            # Set up API call parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self.settings.temperature,
                "max_tokens": self.settings.max_output_tokens,
            }

            # Add reasoning parameters for supported models
            if any(model_name in self.model for model_name in REASONING_MODELS):
                params["top_p"] = 0.1
                params["frequency_penalty"] = 0.0
                params["presence_penalty"] = 0.0

            # Make the API call
            if stream:
                response_text = ""
                async for chunk in await self.client.chat.completions.create(
                    **params, stream=True
                ):
                    if chunk.choices and chunk.choices[0].delta.content:
                        response_text += chunk.choices[0].delta.content
                return response_text
            else:
                response = await self.client.chat.completions.create(**params)
                if not response.choices or not response.choices[0].message.content:
                    raise ValueError("Empty response from LLM")
                return response.choices[0].message.content

        except TokenLimitExceeded as e:
            # Re-raise token limit exceptions
            raise e
        except (AuthenticationError, APIError, RateLimitError) as e:
            # Log and re-raise OpenAI errors for retry
            logger.error(f"OpenAI API error: {str(e)}")
            raise e
        except Exception as e:
            # Log and re-raise other exceptions
            logger.error(f"Unexpected error in LLM.ask: {str(e)}")
            raise e

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type(
            (OpenAIError, Exception, ValueError)
        ),  # Don't retry TokenLimitExceeded
    )
    async def ask_tool(
        self,
        messages: List[Union[dict, Message]],
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: TOOL_CHOICE_TYPE = ToolChoice.AUTO,  # type: ignore
        temperature: Optional[float] = None,
        base64_image: Optional[str] = None,
    ) -> Message:
        """
        Send a prompt to the LLM with tool options and get the response.

        Args:
            messages: List of conversation messages
            system_msgs: Optional system messages to prepend
            tools: List of tool definitions
            tool_choice: Tool choice strategy
            temperature: Sampling temperature for the response
            base64_image: Optional base64-encoded image to include

        Returns:
            Message: The generated response as a Message object

        Raises:
            TokenLimitExceeded: If token limits are exceeded
            ValueError: If messages are invalid or response is empty
            OpenAIError: If API call fails after retries
            Exception: For unexpected errors
        """
        try:
            # Check if the model supports images
            supports_images = self.model in MULTIMODAL_MODELS

            # Add base64 image to the last user message if provided
            if base64_image and supports_images:
                for i in range(len(messages) - 1, -1, -1):
                    if isinstance(messages[i], Message) and messages[i].role == "user":
                        messages[i].base64_image = base64_image
                        break
                    elif isinstance(messages[i], dict) and messages[i].get("role") == "user":
                        messages[i]["base64_image"] = base64_image
                        break

            # Format system and user messages with image support check
            if system_msgs:
                system_msgs = self.format_messages(system_msgs, supports_images)
                messages = system_msgs + self.format_messages(messages, supports_images)
            else:
                messages = self.format_messages(messages, supports_images)

            # Calculate input token count
            input_tokens = self.count_message_tokens(messages)

            # Check if token limits are exceeded
            if input_tokens > self.settings.max_input_tokens:
                raise TokenLimitExceeded(
                    f"Input tokens ({input_tokens}) exceed limit ({self.settings.max_input_tokens})"
                )

            # Set up API call parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self.settings.temperature,
                "max_tokens": self.settings.max_output_tokens,
            }

            # Add tools if provided
            if tools:
                params["tools"] = tools
                if tool_choice and tool_choice != ToolChoice.AUTO:
                    params["tool_choice"] = tool_choice

            # Add reasoning parameters for supported models
            if any(model_name in self.model for model_name in REASONING_MODELS):
                params["top_p"] = 0.1
                params["frequency_penalty"] = 0.0
                params["presence_penalty"] = 0.0

            # Make the API call
            response = await self.client.chat.completions.create(**params)

            if not response.choices:
                raise ValueError("Empty response from LLM")

            # Convert the response to a Message object
            message = response.choices[0].message
            result = Message(
                role="assistant",
                content=message.content,
                tool_calls=message.tool_calls,
            )

            return result

        except TokenLimitExceeded as e:
            # Re-raise token limit exceptions
            raise e
        except (AuthenticationError, APIError, RateLimitError) as e:
            # Log and re-raise OpenAI errors for retry
            logger.error(f"OpenAI API error: {str(e)}")
            raise e
        except Exception as e:
            # Log and re-raise other exceptions
            logger.error(f"Unexpected error in LLM.ask_tool: {str(e)}")
            raise e

    async def ask_tool_streaming(
        self,
        messages: List[Union[dict, Message]],
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: TOOL_CHOICE_TYPE = ToolChoice.AUTO,  # type: ignore
        temperature: Optional[float] = None,
        base64_image: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send a prompt to the LLM with tool options and stream the response.

        Args:
            messages: List of conversation messages
            system_msgs: Optional system messages to prepend
            tools: List of tool definitions
            tool_choice: Tool choice strategy
            temperature: Sampling temperature for the response
            base64_image: Optional base64-encoded image to include

        Yields:
            Dict[str, Any]: Chunks of the generated response

        Raises:
            TokenLimitExceeded: If token limits are exceeded
            ValueError: If messages are invalid
            OpenAIError: If API call fails
            Exception: For unexpected errors
        """
        try:
            # Check if the model supports images
            supports_images = self.model in MULTIMODAL_MODELS

            # Add base64 image to the last user message if provided
            if base64_image and supports_images:
                for i in range(len(messages) - 1, -1, -1):
                    if isinstance(messages[i], Message) and messages[i].role == "user":
                        messages[i].base64_image = base64_image
                        break
                    elif isinstance(messages[i], dict) and messages[i].get("role") == "user":
                        messages[i]["base64_image"] = base64_image
                        break

            # Format system and user messages with image support check
            if system_msgs:
                system_msgs = self.format_messages(system_msgs, supports_images)
                messages = system_msgs + self.format_messages(messages, supports_images)
            else:
                messages = self.format_messages(messages, supports_images)

            # Calculate input token count
            input_tokens = self.count_message_tokens(messages)

            # Check if token limits are exceeded
            if input_tokens > self.settings.max_input_tokens:
                raise TokenLimitExceeded(
                    f"Input tokens ({input_tokens}) exceed limit ({self.settings.max_input_tokens})"
                )

            # Set up API call parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self.settings.temperature,
                "max_tokens": self.settings.max_output_tokens,
                "stream": True,
            }

            # Add tools if provided
            if tools:
                params["tools"] = tools
                if tool_choice and tool_choice != ToolChoice.AUTO:
                    params["tool_choice"] = tool_choice

            # Add reasoning parameters for supported models
            if any(model_name in self.model for model_name in REASONING_MODELS):
                params["top_p"] = 0.1
                params["frequency_penalty"] = 0.0
                params["presence_penalty"] = 0.0

            # Make the API call with streaming
            stream = await self.client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta
                    result = {}
                    
                    if delta.content:
                        result["content"] = delta.content
                    
                    if delta.tool_calls:
                        result["tool_calls"] = [
                            {
                                "id": tool_call.id,
                                "type": tool_call.type,
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments,
                                }
                            }
                            for tool_call in delta.tool_calls
                        ]
                    
                    if result:
                        yield result

        except TokenLimitExceeded as e:
            # Re-raise token limit exceptions
            raise e
        except (AuthenticationError, APIError, RateLimitError) as e:
            # Log and re-raise OpenAI errors
            logger.error(f"OpenAI API error: {str(e)}")
            raise e
        except Exception as e:
            # Log and re-raise other exceptions
            logger.error(f"Unexpected error in LLM.ask_tool_streaming: {str(e)}")
            raise e


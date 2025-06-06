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

# Constants for model capabilities
MULTIMODAL_MODELS = [
    "gpt-4-vision-preview",
    "gpt-4-vision",
    "gpt-4o",
    "claude-3-opus",
    "claude-3-sonnet",
    "claude-3-haiku",
]

REASONING_MODELS = [
    "gpt-4",
    "gpt-4-turbo",
    "gpt-4o",
    "claude-3-opus",
    "claude-3-sonnet",
]

# Retry configuration for API calls
MAX_RETRIES = 3
MIN_RETRY_WAIT = 1  # seconds
MAX_RETRY_WAIT = 10  # seconds


class LLM:
    """LLM client for interacting with various language model providers"""

    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        settings: Optional[LLMSettings] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
        organization: Optional[str] = None,
    ):
        """
        Initialize the LLM client.

        Args:
            model: Model identifier to use
            settings: LLM settings
            api_key: API key for the provider
            api_base: Base URL for the API
            api_version: API version
            organization: Organization ID for the API
        """
        self.model = model
        
        # Criar LLMSettings com valores padrão para evitar erro de validação
        if settings is None:
            self.settings = LLMSettings(
                model=model,
                base_url=api_base or "https://api.openai.com/v1",
                api_key=api_key or "default_key",
                api_type="openai",
                api_version=api_version or "2023-05-15",
                max_tokens=4096,
                temperature=1.0
            )
        else:
            self.settings = settings

        # Set up the appropriate client based on the model
        if model.startswith("anthropic."):
            # Bedrock Claude models
            self.client = BedrockClient(
                model_id=model,
                api_key=api_key,
                region=config.aws_region,
            )
        elif model.startswith("claude-"):
            # Direct Anthropic API
            from anthropic import AsyncAnthropic

            self.client = AsyncAnthropic(api_key=api_key or config.anthropic_api_key)
        elif "azure" in (api_base or "").lower():
            # Azure OpenAI
            self.client = AsyncAzureOpenAI(
                api_key=api_key or config.azure_api_key,
                api_version=api_version or config.azure_api_version,
                azure_endpoint=api_base or config.azure_api_base,
            )
        else:
            # OpenAI
            self.client = AsyncOpenAI(
                api_key=api_key or config.openai_api_key,
                base_url=api_base or config.openai_api_base,
                organization=organization or config.openai_organization,
            )

        # Set up tokenizer for the model
        try:
            if model.startswith("gpt-"):
                # OpenAI models
                if model == "gpt-4o":
                    self.tokenizer = tiktoken.encoding_for_model("gpt-4")
                else:
                    self.tokenizer = tiktoken.encoding_for_model(model)
            elif model.startswith("text-embedding-"):
                # OpenAI embedding models
                self.tokenizer = tiktoken.encoding_for_model("text-embedding-ada-002")
            else:
                # Default to cl100k_base for other models
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Failed to load tokenizer for {model}: {e}")
            # Fall back to cl100k_base
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.

        Args:
            text: Text to count tokens for

        Returns:
            int: Number of tokens
        """
        if not text:
            return 0
        return len(self.tokenizer.encode(text))

    def count_message_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Count the number of tokens in a list of messages.

        Args:
            messages: List of messages to count tokens for

        Returns:
            int: Number of tokens
        """
        if not messages:
            return 0

        # Simple token counting for messages
        token_count = 0
        for message in messages:
            # Count role tokens
            if "role" in message:
                token_count += self.count_tokens(message["role"])

            # Count content tokens
            if "content" in message:
                if isinstance(message["content"], str):
                    token_count += self.count_tokens(message["content"])
                elif isinstance(message["content"], list):
                    for item in message["content"]:
                        if isinstance(item, str):
                            token_count += self.count_tokens(item)
                        elif isinstance(item, dict) and "text" in item:
                            token_count += self.count_tokens(item["text"])

            # Count name tokens if present
            if "name" in message:
                token_count += self.count_tokens(message["name"])

            # Add per-message overhead
            token_count += 4  # Approximate overhead per message

        # Add base overhead
        token_count += 2  # Base overhead

        return token_count

    def format_messages(
        self, messages: List[Union[dict, Message]], supports_images: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Format messages for the LLM API.

        Args:
            messages: List of messages to format
            supports_images: Whether the model supports images

        Returns:
            List[Dict[str, Any]]: Formatted messages

        Raises:
            ValueError: If messages are invalid
        """
        formatted_messages = []

        for message in messages:
            if isinstance(message, Message):
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

                    # Remove the base64_image field
                    if "base64_image" in message_dict:
                        del message_dict["base64_image"]

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
            if "role" not in msg or msg["role"] not in ROLE_VALUES:
                raise ValueError(f"Invalid message role: {msg.get('role')}")

        return formatted_messages

    @retry(
        retry=retry_if_exception_type((APIError, RateLimitError)),
        wait=wait_random_exponential(min=MIN_RETRY_WAIT, max=MAX_RETRY_WAIT),
        stop=stop_after_attempt(MAX_RETRIES),
    )
    async def ask(
        self,
        messages: List[Union[dict, Message]],
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        temperature: Optional[float] = None,
        base64_image: Optional[str] = None,
    ) -> ChatCompletionMessage:
        """
        Send a prompt to the LLM and get a response.

        Args:
            messages: List of conversation messages
            system_msgs: Optional system messages to prepend
            temperature: Sampling temperature for the response
            base64_image: Optional base64-encoded image to include

        Returns:
            ChatCompletionMessage: The generated response

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
                "max_tokens": self.settings.max_tokens,
            }

            # Add reasoning parameters for supported models
            if any(model_name in self.model for model_name in REASONING_MODELS):
                params["top_p"] = 0.1
                params["frequency_penalty"] = 0.0
                params["presence_penalty"] = 0.0

            # Make the API call
            response = await self.client.chat.completions.create(**params)
            return response.choices[0].message

        except TokenLimitExceeded as e:
            # Re-raise token limit exceptions
            raise e
        except (AuthenticationError, APIError, RateLimitError) as e:
            # Log and re-raise OpenAI errors
            logger.error(f"OpenAI API error: {str(e)}")
            raise e
        except Exception as e:
            # Log and re-raise other exceptions
            logger.error(f"Unexpected error in LLM.ask: {str(e)}")
            raise e

    @retry(
        retry=retry_if_exception_type((APIError, RateLimitError)),
        wait=wait_random_exponential(min=MIN_RETRY_WAIT, max=MAX_RETRY_WAIT),
        stop=stop_after_attempt(MAX_RETRIES),
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
        Send a prompt to the LLM with tool options.

        Args:
            messages: List of conversation messages
            system_msgs: Optional system messages to prepend
            tools: List of tool definitions
            tool_choice: Tool choice strategy
            temperature: Sampling temperature for the response
            base64_image: Optional base64-encoded image to include

        Returns:
            Message: The generated response

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
                "max_tokens": self.settings.max_tokens,
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
            message = response.choices[0].message

            # Convert to Message object
            from app.schema import Function, ToolCall

            content = message.content
            tool_calls = None

            if message.tool_calls:
                tool_calls = []
                for tc in message.tool_calls:
                    tool_calls.append(
                        ToolCall(
                            id=tc.id,
                            type=tc.type,
                            function=Function(
                                name=tc.function.name,
                                arguments=tc.function.arguments,
                            ),
                        )
                    )

            return Message(
                role="assistant",
                content=content,
                tool_calls=tool_calls,
            )

        except TokenLimitExceeded as e:
            # Re-raise token limit exceptions
            raise e
        except (AuthenticationError, APIError, RateLimitError) as e:
            # Log and re-raise OpenAI errors
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
                "max_tokens": self.settings.max_tokens,
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
                        try:
                            result["tool_calls"] = []
                            for tool_call in delta.tool_calls:
                                try:
                                    # Verificar se tool_call tem os atributos necessários
                                    if not hasattr(tool_call, "id") or not hasattr(tool_call, "type"):
                                        logger.warning(f"Tool call missing required attributes: {tool_call}")
                                        continue
                                        
                                    # Verificar se function existe e tem os atributos necessários
                                    if not hasattr(tool_call, "function"):
                                        logger.warning(f"Tool call missing function attribute: {tool_call}")
                                        continue
                                        
                                    # Verificar se function tem os atributos name e arguments
                                    function = tool_call.function
                                    if not hasattr(function, "name") or not hasattr(function, "arguments"):
                                        logger.warning(f"Function missing required attributes: {function}")
                                        continue
                                    
                                    # Adicionar o tool call ao resultado com verificações de segurança
                                    result["tool_calls"].append({
                                        "id": getattr(tool_call, "id", ""),
                                        "type": getattr(tool_call, "type", "function"),
                                        "function": {
                                            "name": getattr(function, "name", ""),
                                            "arguments": getattr(function, "arguments", "{}"),
                                        }
                                    })
                                except Exception as tc_error:
                                    logger.warning(f"Error processing individual tool call: {tc_error}")
                                    continue
                        except Exception as tc_list_error:
                            logger.warning(f"Error processing tool calls list: {tc_list_error}")
                    
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


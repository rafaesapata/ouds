"""
OUDS - LLM Module with Admin Configuration Support
==================================================

Módulo LLM que utiliza as configurações administrativas dinâmicas.
"""

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

from app.admin_config import admin_config_manager
from app.admin_schema import LLMType, LLMStatus
from app.exceptions import TokenLimitExceeded
from app.logger import logger
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


class AdminLLM:
    """LLM client que utiliza configurações administrativas dinâmicas"""

    def __init__(
        self,
        llm_type: LLMType = LLMType.TEXT,
        llm_id: Optional[str] = None,
    ):
        """
        Initialize the Admin LLM client.

        Args:
            llm_type: Tipo de LLM (TEXT ou VISION)
            llm_id: ID específico da configuração LLM (opcional)
        """
        self.llm_type = llm_type
        self.llm_id = llm_id
        self._config = None
        self._client = None
        self._tokenizer = None
        
        # Carregar configuração
        self._load_config()
        
        # Configurar cliente
        self._setup_client()
        
        # Configurar tokenizer
        self._setup_tokenizer()

    def _load_config(self):
        """Carrega configuração do admin_config_manager."""
        try:
            if self.llm_id:
                # Usar configuração específica
                self._config = admin_config_manager.get_llm_configuration(self.llm_id)
            else:
                # Usar configuração padrão para o tipo
                self._config = admin_config_manager.get_default_llm(self.llm_type)
            
            if not self._config:
                raise ValueError(f"Nenhuma configuração LLM encontrada para tipo {self.llm_type}")
            
            if self._config.status != LLMStatus.ACTIVE:
                logger.warning(f"LLM {self._config.id} não está ativo (status: {self._config.status})")
            
            logger.info(f"Configuração LLM carregada: {self._config.id} - {self._config.model}")
            
        except Exception as e:
            logger.error(f"Erro ao carregar configuração LLM: {e}")
            raise

    def _setup_client(self):
        """Configura o cliente baseado na configuração."""
        try:
            if not self._config:
                raise ValueError("Configuração LLM não carregada")
            
            # Verificar se é Azure OpenAI
            if "azure" in self._config.base_url.lower():
                self._client = AsyncAzureOpenAI(
                    api_key=self._config.api_key,
                    api_version=self._config.api_type or "2023-05-15",
                    azure_endpoint=self._config.base_url,
                )
                logger.info(f"Cliente Azure OpenAI configurado: {self._config.base_url}")
            else:
                # OpenAI padrão ou compatível
                self._client = AsyncOpenAI(
                    api_key=self._config.api_key,
                    base_url=self._config.base_url,
                )
                logger.info(f"Cliente OpenAI configurado: {self._config.base_url}")
                
        except Exception as e:
            logger.error(f"Erro ao configurar cliente LLM: {e}")
            raise

    def _setup_tokenizer(self):
        """Configura o tokenizer baseado no modelo."""
        try:
            if not self._config:
                raise ValueError("Configuração LLM não carregada")
            
            model = self._config.model
            
            if model.startswith("gpt-"):
                # Modelos OpenAI
                if model == "gpt-4o":
                    self._tokenizer = tiktoken.encoding_for_model("gpt-4")
                else:
                    self._tokenizer = tiktoken.encoding_for_model(model)
            elif model.startswith("text-embedding-"):
                # Modelos de embedding OpenAI
                self._tokenizer = tiktoken.encoding_for_model("text-embedding-ada-002")
            else:
                # Fallback para cl100k_base
                self._tokenizer = tiktoken.get_encoding("cl100k_base")
                
            logger.info(f"Tokenizer configurado para modelo: {model}")
            
        except Exception as e:
            logger.warning(f"Falha ao carregar tokenizer para {self._config.model}: {e}")
            # Fallback para cl100k_base
            self._tokenizer = tiktoken.get_encoding("cl100k_base")

    @property
    def model(self) -> str:
        """Retorna o nome do modelo."""
        return self._config.model if self._config else "unknown"

    @property
    def config(self):
        """Retorna a configuração atual."""
        return self._config

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.

        Args:
            text: Text to count tokens for

        Returns:
            int: Number of tokens
        """
        if not text or not self._tokenizer:
            return 0
        return len(self._tokenizer.encode(text))

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
            if not self._config or not self._client:
                raise ValueError("LLM não configurado corretamente")

            # Check if the model supports images
            supports_images = self._config.model in MULTIMODAL_MODELS

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
            if input_tokens > self._config.max_tokens:
                raise TokenLimitExceeded(
                    f"Input tokens ({input_tokens}) exceed limit ({self._config.max_tokens})"
                )

            # Set up API call parameters
            params = {
                "model": self._config.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self._config.temperature,
                "max_tokens": self._config.max_tokens,
            }

            # Add reasoning parameters for supported models
            if any(model_name in self._config.model for model_name in REASONING_MODELS):
                params["top_p"] = 0.1
                params["frequency_penalty"] = 0.0
                params["presence_penalty"] = 0.0

            logger.info(f"Fazendo chamada para LLM: {self._config.model} com {input_tokens} tokens")

            # Make the API call
            response = await self._client.chat.completions.create(**params)
            
            logger.info(f"Resposta recebida do LLM: {self._config.model}")
            
            return response.choices[0].message

        except TokenLimitExceeded as e:
            # Re-raise token limit exceptions
            logger.error(f"Limite de tokens excedido: {e}")
            raise e
        except (AuthenticationError, APIError, RateLimitError) as e:
            # Log and re-raise OpenAI errors
            logger.error(f"Erro da API OpenAI: {str(e)}")
            raise e
        except Exception as e:
            # Log and re-raise other exceptions
            logger.error(f"Erro inesperado no AdminLLM.ask: {str(e)}")
            raise e

    async def ask_stream(
        self,
        messages: List[Union[dict, Message]],
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        temperature: Optional[float] = None,
        base64_image: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Send a prompt to the LLM and get a streaming response.

        Args:
            messages: List of conversation messages
            system_msgs: Optional system messages to prepend
            temperature: Sampling temperature for the response
            base64_image: Optional base64-encoded image to include

        Yields:
            str: Chunks of the generated response
        """
        try:
            if not self._config or not self._client:
                raise ValueError("LLM não configurado corretamente")

            # Check if the model supports images
            supports_images = self._config.model in MULTIMODAL_MODELS

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
            if input_tokens > self._config.max_tokens:
                raise TokenLimitExceeded(
                    f"Input tokens ({input_tokens}) exceed limit ({self._config.max_tokens})"
                )

            # Set up API call parameters
            params = {
                "model": self._config.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self._config.temperature,
                "max_tokens": self._config.max_tokens,
                "stream": True,
            }

            logger.info(f"Iniciando streaming do LLM: {self._config.model} com {input_tokens} tokens")

            # Make the streaming API call
            async for chunk in await self._client.chat.completions.create(**params):
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Erro no streaming do AdminLLM: {str(e)}")
            raise e

    def reload_config(self):
        """Recarrega a configuração do admin_config_manager."""
        try:
            logger.info(f"Recarregando configuração LLM: {self.llm_type}")
            self._load_config()
            self._setup_client()
            self._setup_tokenizer()
            logger.info(f"Configuração LLM recarregada com sucesso: {self._config.id}")
        except Exception as e:
            logger.error(f"Erro ao recarregar configuração LLM: {e}")
            raise


def get_llm(llm_type: LLMType = LLMType.TEXT, llm_id: Optional[str] = None) -> AdminLLM:
    """
    Factory function para criar instância AdminLLM.
    
    Args:
        llm_type: Tipo de LLM (TEXT ou VISION)
        llm_id: ID específico da configuração (opcional)
    
    Returns:
        AdminLLM: Instância configurada do LLM
    """
    return AdminLLM(llm_type=llm_type, llm_id=llm_id)


def get_text_llm(llm_id: Optional[str] = None) -> AdminLLM:
    """Conveniência para obter LLM de texto."""
    return get_llm(LLMType.TEXT, llm_id)


def get_vision_llm(llm_id: Optional[str] = None) -> AdminLLM:
    """Conveniência para obter LLM de visão."""
    return get_llm(LLMType.VISION, llm_id)


    async def ask_tool_streaming(
        self,
        messages: List[Union[dict, Message]],
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        base64_image: Optional[str] = None,
    ) -> AsyncGenerator[Union[str, Dict[str, Any]], None]:
        """
        Send a prompt to the LLM with tools and get a streaming response.

        Args:
            messages: List of conversation messages
            system_msgs: Optional system messages to prepend
            tools: List of available tools
            tool_choice: Tool choice strategy
            temperature: Sampling temperature for the response
            base64_image: Optional base64-encoded image to include

        Yields:
            Union[str, Dict[str, Any]]: Chunks of the generated response or tool calls
        """
        try:
            if not self._config or not self._client:
                raise ValueError("LLM não configurado corretamente")

            # Check if the model supports images
            supports_images = self._config.model in MULTIMODAL_MODELS

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
            if input_tokens > self._config.max_tokens:
                raise TokenLimitExceeded(
                    f"Input tokens ({input_tokens}) exceed limit ({self._config.max_tokens})"
                )

            # Set up API call parameters
            params = {
                "model": self._config.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self._config.temperature,
                "max_tokens": self._config.max_tokens,
                "stream": True,
            }

            # Add tools if provided
            if tools:
                params["tools"] = tools
                if tool_choice:
                    params["tool_choice"] = tool_choice

            logger.info(f"Iniciando streaming com tools do LLM: {self._config.model} com {input_tokens} tokens")

            # Make the streaming API call
            stream = await self._client.chat.completions.create(**params)
            
            current_tool_call = None
            tool_calls = []
            
            async for chunk in stream:
                if not chunk.choices:
                    continue
                    
                choice = chunk.choices[0]
                delta = choice.delta
                
                # Handle content streaming
                if delta.content:
                    yield delta.content
                
                # Handle tool calls
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        # Initialize or update tool call
                        if tool_call_delta.index is not None:
                            # Ensure we have enough tool calls in our list
                            while len(tool_calls) <= tool_call_delta.index:
                                tool_calls.append({
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                })
                            
                            current_tool_call = tool_calls[tool_call_delta.index]
                            
                            # Update tool call fields
                            if tool_call_delta.id:
                                current_tool_call["id"] = tool_call_delta.id
                            
                            if tool_call_delta.function:
                                if tool_call_delta.function.name:
                                    current_tool_call["function"]["name"] = tool_call_delta.function.name
                                if tool_call_delta.function.arguments:
                                    current_tool_call["function"]["arguments"] += tool_call_delta.function.arguments
                
                # Check if streaming is finished
                if choice.finish_reason:
                    if tool_calls:
                        # Yield tool calls as a structured response
                        yield {
                            "tool_calls": tool_calls,
                            "finish_reason": choice.finish_reason
                        }
                    break

        except Exception as e:
            logger.error(f"Erro no streaming com tools do AdminLLM: {str(e)}")
            raise e

    async def ask_tool(
        self,
        messages: List[Union[dict, Message]],
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        base64_image: Optional[str] = None,
    ) -> Any:
        """
        Send a prompt to the LLM with tools and get a response.

        Args:
            messages: List of conversation messages
            system_msgs: Optional system messages to prepend
            tools: List of available tools
            tool_choice: Tool choice strategy
            temperature: Sampling temperature for the response
            base64_image: Optional base64-encoded image to include

        Returns:
            ChatCompletionMessage: The generated response with potential tool calls
        """
        try:
            if not self._config or not self._client:
                raise ValueError("LLM não configurado corretamente")

            # Check if the model supports images
            supports_images = self._config.model in MULTIMODAL_MODELS

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
            if input_tokens > self._config.max_tokens:
                raise TokenLimitExceeded(
                    f"Input tokens ({input_tokens}) exceed limit ({self._config.max_tokens})"
                )

            # Set up API call parameters
            params = {
                "model": self._config.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self._config.temperature,
                "max_tokens": self._config.max_tokens,
            }

            # Add tools if provided
            if tools:
                params["tools"] = tools
                if tool_choice:
                    params["tool_choice"] = tool_choice

            logger.info(f"Fazendo chamada com tools para LLM: {self._config.model} com {input_tokens} tokens")

            # Make the API call
            response = await self._client.chat.completions.create(**params)
            
            logger.info(f"Resposta com tools recebida do LLM: {self._config.model}")
            
            return response.choices[0].message

        except TokenLimitExceeded as e:
            # Re-raise token limit exceptions
            logger.error(f"Limite de tokens excedido: {e}")
            raise e
        except (AuthenticationError, APIError, RateLimitError) as e:
            # Log and re-raise OpenAI errors
            logger.error(f"Erro da API OpenAI: {str(e)}")
            raise e
        except Exception as e:
            # Log and re-raise other exceptions
            logger.error(f"Erro inesperado no AdminLLM.ask_tool: {str(e)}")
            raise e


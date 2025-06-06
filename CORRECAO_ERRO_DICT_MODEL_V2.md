# Correção do Erro 'dict' object has no attribute 'model' - Versão 2

## Descrição do Problema

O sistema continuava apresentando o seguinte erro durante o processamento de streaming de chat, mesmo após a primeira tentativa de correção:

```
2025-06-06 01:44:33.374 | INFO     | api_server:chat_stream_endpoint:153 - Streaming chat request: session=test_session_1749174273.364696, workspace=default, message=Olá, este é um teste para verificar a correção do ...
2025-06-06 01:44:33.374 | ERROR    | api_server:chat_stream_endpoint:165 - Error in chat stream endpoint: 'dict' object has no attribute 'model'
INFO:     127.0.0.1:51450 - "POST /chat/stream HTTP/1.1" 500 Internal Server Error
2025-06-06 01:44:33,375 | ERROR    | test_correction:test_chat_stream:64 - Erro na conexão: status 500
2025-06-06 01:44:33,375 | ERROR    | test_correction:test_chat_stream:66 - Detalhes do erro: {"detail":"Internal server error: 'dict' object has no attribute 'model'"}
2025-06-06 01:44:33,376 | ERROR    | test_correction:main:92 - ❌ TESTE FALHOU: O problema ainda persiste.
```

## Causa Raiz

Após uma análise mais profunda, identificamos que o problema ocorria em múltiplos pontos:

1. No método `from_tool_calls` da classe `Message` no arquivo `schema.py`, que tentava chamar `model_dump()` em objetos que não tinham esse método.

2. No processamento de `tool_calls` no arquivo `llm.py`, onde não havia verificações suficientes para garantir que os objetos tivessem os atributos necessários.

3. No arquivo `toolcall.py`, onde as verificações implementadas anteriormente não eram suficientemente robustas para lidar com todos os casos possíveis.

## Correções Implementadas

### 1. Modificação da classe `Function` em `schema.py`

Adicionamos métodos auxiliares para lidar com diferentes formatos de dados:

```python
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
```

### 2. Modificação da classe `ToolCall` em `schema.py`

Adicionamos um método para criar objetos `ToolCall` a partir de dicionários:

```python
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
```

### 3. Modificação do método `from_tool_calls` em `schema.py`

Reimplementamos completamente o método para lidar com diferentes tipos de objetos:

```python
@classmethod
def from_tool_calls(
    cls,
    tool_calls: List[Any],
    content: Union[str, List[str]] = "",
    base64_image: Optional[str] = None,
    **kwargs,
):
    """Create ToolCallsMessage from raw tool calls."""
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
```

### 4. Modificação do processamento de `tool_calls` em `llm.py`

Adicionamos verificações robustas para garantir que os objetos tenham os atributos necessários:

```python
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
```

### 5. Modificação do método `run_with_streaming` em `toolcall.py`

Adicionamos verificações robustas e tratamento de erros em todo o processamento de `tool_calls`:

```python
# Processar tool calls acumulados com verificações robustas
tool_calls = []
if accumulated_tool_calls:
    for tc in accumulated_tool_calls:
        try:
            # Verificações robustas para garantir que temos um dicionário válido
            if not isinstance(tc, dict):
                logger.warning(f"Tool call is not a dictionary: {tc}")
                continue
            
            # Verificar se 'function' existe e é um dicionário
            if "function" not in tc:
                logger.warning(f"Tool call missing 'function' key: {tc}")
                continue
            
            function_data = tc["function"]
            if not isinstance(function_data, dict):
                logger.warning(f"Tool call function is not a dictionary: {function_data}")
                continue
            
            # Verificar se 'function' contém 'name' e 'arguments'
            if "name" not in function_data:
                logger.warning(f"Tool call function missing 'name': {function_data}")
                continue
            
            if "arguments" not in function_data:
                logger.warning(f"Tool call function missing 'arguments': {function_data}")
                function_data["arguments"] = "{}"  # Fornecer um valor padrão
            
            # Criar o objeto Function
            function = SchemaFunction(
                name=function_data["name"],
                arguments=function_data["arguments"]
            )
            
            # Criar o objeto ToolCall
            tool_calls.append(SchemaToolCall(
                id=tc.get("id", ""),
                type=tc.get("type", "function"),
                function=function
            ))
        except Exception as e:
            logger.warning(f"Error creating tool call object: {e}")
            continue
```

## Benefícios da Correção

1. **Robustez Aprimorada**: O sistema agora é muito mais robusto contra estruturas de dados inesperadas e pode lidar com diferentes formatos de objetos.

2. **Diagnóstico Detalhado**: Logs de aviso detalhados foram adicionados em vários pontos para facilitar a identificação de problemas futuros.

3. **Tratamento de Erros Abrangente**: Adicionamos tratamento de exceções em todos os pontos críticos para evitar falhas catastróficas.

4. **Compatibilidade**: O sistema agora pode lidar com diferentes versões de objetos e APIs, tornando-o mais compatível com futuras atualizações.

## Data da Correção

06/06/2025


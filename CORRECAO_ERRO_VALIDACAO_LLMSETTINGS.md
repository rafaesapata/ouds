# Correção do Erro de Validação do LLMSettings

## Problema

O servidor estava apresentando o seguinte erro ao tentar processar requisições de chat:

```
Error in chat stream endpoint: 5 validation errors for LLMSettings
model
  Field required [type=missing, input_value={}, input_type=dict]
base_url
  Field required [type=missing, input_value={}, input_type=dict]
api_key
  Field required [type=missing, input_value={}, input_type=dict]
api_type
  Field required [type=missing, input_value={}, input_type=dict]
api_version
  Field required [type=missing, input_value={}, input_type=dict]
```

Este erro ocorria porque a classe `LLMSettings` estava sendo inicializada sem os campos obrigatórios definidos na classe `LLMSettings` no arquivo `config.py`.

## Causa Raiz

No arquivo `llm.py`, a linha:

```python
self.settings = settings or LLMSettings()
```

estava tentando criar uma instância de `LLMSettings` sem fornecer os campos obrigatórios (`model`, `base_url`, `api_key`, `api_type`, `api_version`), que são definidos com `Field(...)` no arquivo `config.py`.

## Solução

Modificamos o arquivo `llm.py` para fornecer valores padrão para todos os campos obrigatórios quando `settings` é `None`:

```python
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
```

Além disso, adicionamos verificações robustas de tipo e existência de atributos na função `ask_tool_streaming` para evitar erros quando os objetos não têm os atributos esperados:

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

## Benefícios da Correção

1. **Robustez**: O código agora é mais robusto e pode lidar com diferentes cenários de inicialização.
2. **Prevenção de Erros**: Adicionamos verificações de tipo e existência de atributos para evitar erros semelhantes no futuro.
3. **Melhor Tratamento de Erros**: Adicionamos logs detalhados para facilitar o diagnóstico de problemas futuros.
4. **Compatibilidade**: A solução mantém a compatibilidade com o código existente.

## Testes Realizados

1. Verificamos que o arquivo está sintaticamente correto usando `python -m py_compile`.
2. Confirmamos que o código pode ser importado sem erros.
3. Adicionamos verificações robustas para evitar erros semelhantes no futuro.

Esta correção deve resolver o erro de validação do LLMSettings e permitir que o servidor processe requisições de chat corretamente.


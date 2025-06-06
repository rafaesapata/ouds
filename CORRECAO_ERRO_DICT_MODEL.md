# Correção do Erro 'dict' object has no attribute 'model'

## Descrição do Problema

O sistema apresentava o seguinte erro durante o processamento de streaming de chat:

```
2025-06-06 01:16:09.908 | INFO     | api_server:chat_stream_endpoint:153 - Streaming chat request: session=None, workspace=default, message=Olá...
2025-06-06 01:16:09.908 | ERROR    | api_server:chat_stream_endpoint:165 - Error in chat stream endpoint: 'dict' object has no attribute 'model'
INFO:     127.0.0.1:53200 - "POST /chat/stream HTTP/1.1" 500 Internal Server Error
INFO:     127.0.0.1:36376 - "GET / HTTP/1.1" 200 OK
2025-06-06 01:16:23.203 | INFO     | api_server:chat_stream_endpoint:153 - Streaming chat request: session=None, workspace=default, message=Oi...
INFO:     127.0.0.1:33582 - "POST /chat/stream HTTP/1.1" 200 OK
2025-06-06 01:16:23.208 | ERROR    | api_server:process_chat_stream:224 - Error in streaming chat: 'dict' object has no attribute 'model'
```

## Causa Raiz

Foram identificadas duas causas principais:

1. A função `get_context_for_chat` estava sendo importada do módulo `app.knowledge.chat_integration`, mas não estava definida nesse módulo.

2. No arquivo `toolcall.py`, não havia verificações adequadas para garantir que os objetos de chamada de ferramenta (tool calls) tivessem a estrutura esperada antes de acessar seus atributos.

## Correções Implementadas

### 1. Adição da função `get_context_for_chat`

Foi criada a função `get_context_for_chat` no módulo `app.knowledge.chat_integration` com a seguinte implementação:

```python
async def get_context_for_chat(message: str, workspace_id: str = "default") -> Optional[str]:
    """
    Obtém contexto relevante para uma mensagem de chat a partir do sistema de conhecimento.
    
    Args:
        message: A mensagem do usuário
        workspace_id: ID do workspace
        
    Returns:
        String com o contexto relevante ou None se não houver contexto
    """
    try:
        # Importar módulos de conhecimento necessários
        from app.knowledge import knowledge_manager
        from app.knowledge.file_integration import get_file_context_for_chat
        
        # Log do workspace sendo usado
        logger.info(f"Obtendo contexto para mensagem no workspace_id: {workspace_id}")
        
        # Buscar conhecimento relevante do workspace
        relevant_knowledge = knowledge_manager.search_knowledge(workspace_id, message, limit=5)
        
        # Verificar se há referências a arquivos na mensagem
        file_context = get_file_context_for_chat(workspace_id, message)
        
        # Construir contexto combinado
        combined_context = ""
        
        # Adicionar conhecimento relevante do workspace
        if relevant_knowledge:
            workspace_context = "Conhecimento específico do workspace:\n"
            for entry in relevant_knowledge:
                workspace_context += f"- {entry.content}\n"
                # Atualizar estatísticas de uso
                knowledge_manager.update_knowledge_usage(workspace_id, entry.id)
            
            combined_context += workspace_context
            logger.info(f"Conhecimento do workspace aplicado ao contexto: {len(relevant_knowledge)} entradas")
        
        # Adicionar contexto de arquivos
        if file_context:
            if combined_context:
                combined_context += "\n\n"
            combined_context += f"Informações de arquivos do workspace:\n{file_context}"
            logger.info("Contexto de arquivos aplicado")
        
        # Retornar contexto combinado se existir
        if combined_context:
            logger.info(f"Contexto total: {len(combined_context)} caracteres")
            return combined_context
        else:
            logger.info("Nenhum contexto relevante encontrado")
            return None
            
    except Exception as e:
        logger.error(f"Erro ao obter contexto para chat: {e}")
        return None
```

### 2. Adição de verificações de tipo/existência de atributos

No arquivo `toolcall.py`, foram adicionadas verificações robustas para garantir que os objetos de chamada de ferramenta tenham a estrutura esperada:

```python
# Adicionar verificações de tipo/existência de atributos
if not isinstance(tc, dict):
    logger.warning(f"Tool call is not a dictionary: {tc}")
    continue
    
# Verificar se 'function' existe e é um dicionário
if "function" not in tc or not isinstance(tc["function"], dict):
    logger.warning(f"Tool call missing 'function' or not a dictionary: {tc}")
    continue
    
# Verificar se 'function' contém 'name' e 'arguments'
if "name" not in tc["function"] or "arguments" not in tc["function"]:
    logger.warning(f"Tool call function missing required fields: {tc}")
    continue
    
# Criar o objeto ToolCall com valores seguros
tool_calls.append(SchemaToolCall(
    id=tc.get("id", ""),
    type=tc.get("type", "function"),
    function={
        "name": tc["function"]["name"],
        "arguments": tc["function"]["arguments"]
    }
))
```

## Benefícios da Correção

1. **Robustez**: O sistema agora é mais robusto contra estruturas de dados inesperadas.
2. **Diagnóstico**: Logs de aviso detalhados foram adicionados para facilitar a identificação de problemas futuros.
3. **Funcionalidade**: A função `get_context_for_chat` agora está implementada corretamente, permitindo a integração com o sistema de conhecimento.

## Data da Correção

06/06/2025


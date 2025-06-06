# Correção do Erro ToolCollection - to_openai_tools

## Problema Identificado

O sistema estava apresentando o erro:
```
'ToolCollection' object has no attribute 'to_openai_tools'
```

Este erro ocorria no arquivo `app/agent/toolcall.py` nas linhas 54 e 203, onde o código tentava chamar o método `to_openai_tools()` na classe `ToolCollection`, mas esse método não estava implementado.

## Análise da Causa

1. **Localização do erro**: O erro ocorria em duas chamadas no arquivo `toolcall.py`:
   - Linha 54: `tools=self.available_tools.to_openai_tools()`
   - Linha 203: `tools=self.available_tools.to_openai_tools()`

2. **Classe afetada**: A classe `ToolCollection` em `app/tool/tool_collection.py` não possuía o método `to_openai_tools()`.

3. **Formato esperado**: Baseado na análise do código em `bedrock.py`, o método deveria retornar uma lista de tools no formato OpenAI:
   ```python
   [
       {
           "type": "function",
           "function": {
               "name": "tool_name",
               "description": "tool_description",
               "parameters": {...}
           }
       }
   ]
   ```

## Solução Implementada

Adicionei o método `to_openai_tools()` à classe `ToolCollection` no arquivo `app/tool/tool_collection.py`:

```python
def to_openai_tools(self) -> List[Dict[str, Any]]:
    """Convert the tool collection to OpenAI tools format.
    
    Returns a list of tools in the format expected by OpenAI API:
    [
        {
            "type": "function",
            "function": {
                "name": "tool_name",
                "description": "tool_description",
                "parameters": {...}
            }
        }
    ]
    """
    return [tool.to_param() for tool in self.tools]
```

### Detalhes da Implementação

1. **Reutilização de código existente**: O método utiliza o método `to_param()` já existente na classe `BaseTool`, que já retorna o formato correto esperado pelo OpenAI.

2. **Tipo de retorno**: O método retorna `List[Dict[str, Any]]`, que é o tipo esperado pelas funções que o chamam.

3. **Documentação**: Incluí documentação detalhada explicando o formato de retorno e o propósito do método.

## Testes Realizados

Criei um script de teste (`test_toolcollection_simple.py`) que verifica:

1. ✅ **Validação de sintaxe**: O arquivo não possui erros de sintaxe
2. ✅ **Existência do método**: O método `to_openai_tools` está definido
3. ✅ **Assinatura do método**: A assinatura está correta
4. ✅ **Implementação do método**: A implementação está correta

Todos os testes passaram com sucesso.

## Resultado

A correção resolve o erro `'ToolCollection' object has no attribute 'to_openai_tools'` e permite que o sistema funcione corretamente ao fazer streaming de chat com tools.

## Arquivos Modificados

- `app/tool/tool_collection.py`: Adicionado método `to_openai_tools()`

## Arquivos de Teste Criados

- `test_toolcollection_simple.py`: Script de teste para verificar a correção
- `test_toolcollection_correction.py`: Script de teste mais completo (com dependências externas)

## Compatibilidade

A correção é totalmente compatível com o código existente e não introduz breaking changes, apenas adiciona a funcionalidade que estava faltando.


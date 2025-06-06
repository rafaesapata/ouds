# Correção do Erro de Comparação int vs NoneType

## Problema Identificado

O sistema estava apresentando o erro:
```
'>' not supported between instances of 'int' and 'NoneType'
```

Este erro ocorria no arquivo `app/llm.py` nas linhas 357, 451 e 572, onde o código tentava comparar `input_tokens` (int) com `self.settings.max_input_tokens` (que pode ser None).

## Análise da Causa

1. **Localização do erro**: O erro ocorria em três métodos no arquivo `llm.py`:
   - Linha 357: método `ask()`
   - Linha 451: método `ask_tool()`
   - Linha 572: método `ask_tool_streaming()`

2. **Causa raiz**: O campo `max_input_tokens` na classe `LLMSettings` é definido como `Optional[int]` com valor padrão `None`:
   ```python
   max_input_tokens: Optional[int] = Field(
       None,
       description="Maximum input tokens to use across all requests (None for unlimited)",
   )
   ```

3. **Problema na comparação**: O código tentava fazer comparações diretas:
   ```python
   if input_tokens > self.settings.max_input_tokens:
   ```
   
   Quando `max_input_tokens` é `None`, Python não consegue comparar um `int` com `NoneType`, resultando no erro.

## Solução Implementada

Adicionei verificações de `None` antes de todas as comparações com `max_input_tokens`:

**Antes:**
```python
if input_tokens > self.settings.max_input_tokens:
```

**Depois:**
```python
if self.settings.max_input_tokens is not None and input_tokens > self.settings.max_input_tokens:
```

### Detalhes da Implementação

1. **Verificação de None primeiro**: A condição `self.settings.max_input_tokens is not None` é avaliada primeiro devido ao operador `and`.

2. **Short-circuit evaluation**: Se `max_input_tokens` for `None`, a segunda parte da condição não é avaliada, evitando o erro de comparação.

3. **Comportamento correto**: 
   - Se `max_input_tokens` é `None` (ilimitado): a verificação é pulada
   - Se `max_input_tokens` tem um valor: a comparação é feita normalmente

4. **Correções aplicadas em 3 locais**:
   - Linha 357: método `ask()`
   - Linha 451: método `ask_tool()`
   - Linha 572: método `ask_tool_streaming()`

## Testes Realizados

Criei um script de teste (`test_int_nonetype_correction.py`) que verifica:

1. ✅ **Validação de sintaxe**: O arquivo não possui erros de sintaxe
2. ✅ **Verificação das comparações corrigidas**: Todas as 3 comparações problemáticas foram corrigidas
3. ✅ **Verificação da lógica das correções**: A lógica está correta (None check primeiro)
4. ✅ **Verificação dos métodos afetados**: As correções foram aplicadas nos métodos corretos

Todos os testes passaram com sucesso.

## Resultado

A correção resolve o erro `'>' not supported between instances of 'int' and 'NoneType'` e permite que o sistema funcione corretamente quando `max_input_tokens` está configurado como `None` (ilimitado).

## Arquivos Modificados

- `app/llm.py`: Adicionadas verificações de None antes das comparações com `max_input_tokens`

## Arquivos de Teste Criados

- `test_int_nonetype_correction.py`: Script de teste para verificar a correção

## Compatibilidade

A correção é totalmente compatível com o código existente e não introduz breaking changes. O comportamento quando `max_input_tokens` tem um valor numérico permanece inalterado, e agora o sistema também funciona corretamente quando o valor é `None`.

## Linhas Corrigidas

- Linha 357: `if self.settings.max_input_tokens is not None and input_tokens > self.settings.max_input_tokens:`
- Linha 451: `if self.settings.max_input_tokens is not None and input_tokens > self.settings.max_input_tokens:`
- Linha 572: `if self.settings.max_input_tokens is not None and input_tokens > self.settings.max_input_tokens:`


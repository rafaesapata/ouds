# Correção do Erro 'Config' object has no attribute 'openai_api_key'

## Problema

O servidor estava apresentando o seguinte erro ao tentar processar requisições de chat:

```
Error in chat stream endpoint: 'Config' object has no attribute 'openai_api_key'
```

Este erro ocorria porque a classe `Config` no arquivo `config.py` não tinha os atributos `openai_api_key`, `openai_api_base` e `openai_organization`, mas o código no arquivo `llm.py` estava tentando acessá-los.

## Causa Raiz

No arquivo `llm.py`, as linhas:

```python
self.client = AsyncOpenAI(
    api_key=api_key or config.openai_api_key,
    base_url=api_base or config.openai_api_base,
    organization=organization or config.openai_organization,
)
```

estavam tentando acessar os atributos `openai_api_key`, `openai_api_base` e `openai_organization` da classe `Config`, mas esses atributos não estavam definidos na classe.

## Solução

Modificamos o arquivo `config.py` para adicionar os atributos `openai_api_key`, `openai_api_base` e `openai_organization` à classe `Config`:

1. Adicionamos variáveis de instância para armazenar os valores:
```python
self._openai_api_key = openai_config.get("api_key", "")
self._openai_api_base = openai_config.get("api_base", "https://api.openai.com/v1")
self._openai_organization = openai_config.get("organization", "")
```

2. Adicionamos propriedades para acessar os valores:
```python
@property
def openai_api_key(self) -> str:
    """Get the OpenAI API key"""
    return self._openai_api_key
    
@property
def openai_api_base(self) -> str:
    """Get the OpenAI API base URL"""
    return self._openai_api_base
    
@property
def openai_organization(self) -> str:
    """Get the OpenAI organization ID"""
    return self._openai_organization
```

3. Extraímos os valores da configuração TOML:
```python
# Extrair valores de OpenAI da configuração para acesso direto
openai_config = raw_config.get("openai", {})
self._openai_api_key = openai_config.get("api_key", "")
self._openai_api_base = openai_config.get("api_base", "https://api.openai.com/v1")
self._openai_organization = openai_config.get("organization", "")
```

## Benefícios da Correção

1. **Robustez**: O código agora é mais robusto e pode lidar com diferentes cenários de configuração.
2. **Prevenção de Erros**: Adicionamos valores padrão para evitar erros quando os valores não estão definidos na configuração.
3. **Melhor Organização**: Separamos a configuração do OpenAI em uma seção específica no arquivo de configuração.
4. **Compatibilidade**: A solução mantém a compatibilidade com o código existente.

## Testes Realizados

1. Verificamos que o arquivo está sintaticamente correto usando `python -m py_compile`.
2. Confirmamos que a classe `Config` agora tem os atributos `openai_api_key`, `openai_api_base` e `openai_organization`.

Esta correção deve resolver o erro 'Config' object has no attribute 'openai_api_key' e permitir que o servidor processe requisições de chat corretamente.


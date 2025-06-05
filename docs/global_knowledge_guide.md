# Base de Conhecimento Global - OUDS

## Visão Geral

A Base de Conhecimento Global é um sistema que fornece diretrizes, fatos e contextos fundamentais para todos os agentes do sistema OUDS. Esta base é aplicada automaticamente a todos os workspaces e integrações de LLM, garantindo consistência comportamental em todo o sistema.

## Características

- **Carregamento na Inicialização**: A base é carregada automaticamente quando o sistema inicia
- **Aplicação Universal**: Aplicada a todos os workspaces e LLMs
- **Edição Manual**: Arquivo JSON editável apenas via terminal para segurança
- **Performance Otimizada**: Sistema de cache e lazy loading para máxima eficiência
- **Recarregamento Automático**: Detecta mudanças no arquivo e recarrega automaticamente

## Estrutura do Arquivo

O arquivo de configuração está localizado em:
```
/home/ubuntu/ouds-project/OpenManus/config/global_knowledge.json
```

### Formato JSON

```json
{
  "version": "1.0.0",
  "created_at": "2025-06-05T12:00:00Z",
  "description": "Base de conhecimento global do sistema OUDS",
  "knowledge_entries": [
    {
      "id": "unique_identifier",
      "type": "directive|fact|preference|context|pattern",
      "content": "Conteúdo da entrada de conhecimento",
      "priority": "high|medium|low",
      "tags": ["tag1", "tag2", "tag3"]
    }
  ]
}
```

### Tipos de Entrada

1. **directive**: Diretrizes comportamentais obrigatórias
2. **fact**: Fatos e informações objetivas
3. **preference**: Preferências e estilos de resposta
4. **context**: Contexto sobre o sistema ou domínio
5. **pattern**: Padrões de comportamento ou resposta

### Níveis de Prioridade

- **high**: Sempre incluído no contexto LLM (máximo 15 entradas)
- **medium**: Incluído quando há espaço disponível
- **low**: Incluído apenas se necessário

## Como Editar

### 1. Acessar o Arquivo

```bash
# Navegar para o diretório
cd /home/ubuntu/ouds-project/OpenManus/config

# Editar o arquivo
nano global_knowledge.json
# ou
vim global_knowledge.json
```

### 2. Validar Sintaxe

Após editar, valide a sintaxe JSON:

```bash
# Validar JSON
python3 -m json.tool global_knowledge.json > /dev/null && echo "JSON válido" || echo "JSON inválido"
```

### 3. Aplicar Mudanças

O sistema detecta automaticamente mudanças no arquivo e recarrega a base de conhecimento. Para forçar o recarregamento:

```bash
# Reiniciar o servidor API
cd /home/ubuntu/ouds-project/OpenManus
pkill -f api_server.py
python3.11 api_server.py &
```

## Exemplos de Entradas

### Diretriz de Alta Prioridade
```json
{
  "id": "core_directive_helpful",
  "type": "directive",
  "content": "Sempre seja útil, preciso e respeitoso em todas as interações. Priorize a clareza e a utilidade das respostas.",
  "priority": "high",
  "tags": ["comportamento", "core", "interacao"]
}
```

### Fato sobre o Sistema
```json
{
  "id": "system_fact_ouds",
  "type": "fact",
  "content": "OUDS (Oráculo UDS) é um sistema de agentes inteligentes desenvolvido para automação e assistência avançada.",
  "priority": "medium",
  "tags": ["sistema", "definicao", "ouds"]
}
```

### Preferência de Resposta
```json
{
  "id": "response_preference_portuguese",
  "type": "preference",
  "content": "Responda sempre em português brasileiro, usando linguagem clara e profissional.",
  "priority": "high",
  "tags": ["idioma", "estilo", "comunicacao"]
}
```

### Contexto Técnico
```json
{
  "id": "tech_context_workspace",
  "type": "context",
  "content": "O sistema utiliza workspaces isolados para organizar sessões e arquivos de diferentes usuários ou projetos.",
  "priority": "medium",
  "tags": ["workspace", "arquitetura", "isolamento"]
}
```

### Padrão de Comportamento
```json
{
  "id": "pattern_error_handling",
  "type": "pattern",
  "content": "Ao encontrar erros, sempre explique o problema de forma clara e ofereça soluções práticas quando possível.",
  "priority": "medium",
  "tags": ["erro", "tratamento", "solucao"]
}
```

## Monitoramento e Estatísticas

### Verificar Status

O sistema fornece estatísticas em tempo real sobre a base de conhecimento:

```bash
# Via API (se disponível)
curl http://localhost:8000/api/knowledge/global/stats

# Via logs do sistema
tail -f /home/ubuntu/ouds-project/OpenManus/logs/*.log | grep "conhecimento global"
```

### Informações Disponíveis

- Total de entradas carregadas
- Distribuição por tipo e prioridade
- Timestamp do último carregamento
- Status do cache
- Tags mais utilizadas

## Otimizações de Performance

### Cache Inteligente
- Cache de contextos LLM por 5 minutos
- Recarregamento apenas quando arquivo é modificado
- Indexação por tipo, prioridade e tags

### Lazy Loading
- Verificação de modificação do arquivo apenas quando necessário
- Carregamento sob demanda para operações específicas

### Thread Safety
- Implementação thread-safe com locks
- Padrão Singleton para única instância

## Troubleshooting

### Arquivo Não Carregado

1. Verificar se o arquivo existe:
```bash
ls -la /home/ubuntu/ouds-project/OpenManus/config/global_knowledge.json
```

2. Verificar permissões:
```bash
chmod 644 /home/ubuntu/ouds-project/OpenManus/config/global_knowledge.json
```

3. Verificar sintaxe JSON:
```bash
python3 -m json.tool global_knowledge.json
```

### Entradas Não Aplicadas

1. Verificar logs do sistema:
```bash
tail -f /home/ubuntu/ouds-project/OpenManus/logs/*.log | grep -i "conhecimento\|knowledge"
```

2. Forçar recarregamento:
```bash
# Tocar o arquivo para atualizar timestamp
touch /home/ubuntu/ouds-project/OpenManus/config/global_knowledge.json
```

### Performance Lenta

1. Verificar tamanho do arquivo:
```bash
wc -l /home/ubuntu/ouds-project/OpenManus/config/global_knowledge.json
```

2. Reduzir número de entradas se necessário (recomendado: máximo 100 entradas)

3. Verificar cache:
```bash
# Logs mostrarão estatísticas de cache
grep "cache" /home/ubuntu/ouds-project/OpenManus/logs/*.log
```

## Backup e Versionamento

### Backup Manual
```bash
# Criar backup com timestamp
cp global_knowledge.json "global_knowledge_backup_$(date +%Y%m%d_%H%M%S).json"
```

### Versionamento Git
```bash
# Adicionar ao controle de versão
cd /home/ubuntu/ouds-project
git add OpenManus/config/global_knowledge.json
git commit -m "Atualização da base de conhecimento global"
```

## Segurança

- **Acesso Restrito**: Arquivo editável apenas via terminal
- **Validação**: Validação automática de estrutura e tipos
- **Logs**: Todas as operações são registradas
- **Backup**: Recomendado backup antes de grandes mudanças

## Integração com LLMs

A base de conhecimento é automaticamente incluída no contexto enviado para todos os LLMs:

1. **Priorização**: Entradas de alta prioridade são sempre incluídas
2. **Limite**: Máximo de 20 entradas por contexto (configurável)
3. **Formatação**: Contexto formatado automaticamente para cada LLM
4. **Cache**: Contextos são cacheados para melhor performance

## Melhores Práticas

1. **Seja Específico**: Entradas claras e objetivas
2. **Use Tags**: Facilita organização e busca
3. **Priorize Corretamente**: Use alta prioridade apenas para o essencial
4. **Teste Mudanças**: Valide o impacto antes de aplicar
5. **Documente**: Mantenha histórico de mudanças importantes
6. **Backup Regular**: Faça backup antes de grandes alterações

---

**Nota**: Este sistema é fundamental para o comportamento consistente do OUDS. Mudanças devem ser feitas com cuidado e sempre testadas em ambiente controlado.


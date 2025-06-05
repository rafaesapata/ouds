# Armazenamento de Conhecimento Individual por Workspace

## 🗂️ Estrutura de Armazenamento

### Organização por Diretórios
```
workspace_knowledge/
├── workspace_001/                    # ID único do workspace
│   ├── knowledge_base.json          # Base principal de conhecimento
│   ├── conversation_history.json    # Histórico completo de conversas
│   ├── learned_patterns.json        # Padrões extraídos automaticamente
│   ├── context_embeddings.db        # Banco SQLite com embeddings
│   ├── llm_preferences.json         # Configurações de LLM específicas
│   ├── evolution_log.json           # Log de evolução do conhecimento
│   └── metadata.json               # Metadados do workspace
├── workspace_002/
│   ├── knowledge_base.json
│   ├── conversation_history.json
│   └── ...
└── workspace_N/
    └── ...
```

## 📋 Formato dos Dados

### 1. Knowledge Base (knowledge_base.json)
```json
{
  "workspace_id": "workspace_001",
  "created_at": "2025-01-15T10:30:00Z",
  "last_updated": "2025-01-15T15:45:00Z",
  "version": "1.2.3",
  "knowledge_entries": [
    {
      "id": "uuid-1234-5678-9abc",
      "type": "fact",                    // fact, pattern, preference, context
      "content": "Python é uma linguagem de programação interpretada",
      "confidence": 0.95,               // 0.0 a 1.0
      "source": "conversation",         // conversation, manual, learned
      "created_at": "2025-01-15T10:30:00Z",
      "last_used": "2025-01-15T15:30:00Z",
      "usage_count": 15,
      "tags": ["python", "programming", "language"],
      "embedding_id": "emb_001"         // Referência para embedding
    },
    {
      "id": "uuid-2345-6789-bcde",
      "type": "preference",
      "content": "Usuário prefere exemplos práticos em explicações",
      "confidence": 0.87,
      "source": "learned",
      "created_at": "2025-01-15T11:00:00Z",
      "last_used": "2025-01-15T15:45:00Z",
      "usage_count": 8,
      "tags": ["user_preference", "teaching_style"],
      "embedding_id": "emb_002"
    }
  ],
  "relationships": [
    {
      "from_id": "uuid-1234-5678-9abc",
      "to_id": "uuid-2345-6789-bcde",
      "type": "related",                // related, contradicts, supports
      "strength": 0.75                  // 0.0 a 1.0
    }
  ]
}
```

### 2. Conversation History (conversation_history.json)
```json
{
  "conversations": [
    {
      "id": "conv_001",
      "timestamp": "2025-01-15T10:30:00Z",
      "user_message": "Como funciona o Python?",
      "assistant_response": "Python é uma linguagem...",
      "llm_used": "anthropic_claude_sonnet",
      "context_retrieved": ["uuid-1234-5678-9abc"],
      "knowledge_learned": ["uuid-2345-6789-bcde"],
      "satisfaction_score": 0.9,
      "processing_time": 2.3
    }
  ]
}
```

### 3. Learned Patterns (learned_patterns.json)
```json
{
  "patterns": [
    {
      "id": "pattern_001",
      "pattern_type": "behavior",
      "content": "Quando usuário pergunta sobre código, sempre incluir exemplo",
      "confidence": 0.82,
      "evidence_count": 12,
      "first_seen": "2025-01-10T09:00:00Z",
      "last_seen": "2025-01-15T15:45:00Z",
      "source_conversations": ["conv_001", "conv_005", "conv_012"]
    }
  ]
}
```

### 4. Context Embeddings (SQLite Database)
```sql
CREATE TABLE embeddings (
    id TEXT PRIMARY KEY,
    knowledge_id TEXT,
    content TEXT,
    embedding BLOB,           -- Vetor de embedding serializado
    created_at TIMESTAMP,
    model_used TEXT          -- Modelo usado para gerar embedding
);

CREATE INDEX idx_knowledge_id ON embeddings(knowledge_id);
CREATE INDEX idx_created_at ON embeddings(created_at);
```

### 5. LLM Preferences (llm_preferences.json)
```json
{
  "workspace_id": "workspace_001",
  "preferences": {
    "code_generation": {
      "preferred_llm": "anthropic_claude_sonnet",
      "temperature": 0.3,
      "max_tokens": 2048,
      "custom_instructions": "Sempre incluir comentários no código"
    },
    "general_chat": {
      "preferred_llm": "openai_gpt4_turbo",
      "temperature": 0.7,
      "max_tokens": 1024,
      "custom_instructions": "Ser conciso mas completo"
    }
  },
  "performance_history": {
    "anthropic_claude_sonnet": {
      "avg_satisfaction": 0.92,
      "total_uses": 45,
      "avg_response_time": 2.1
    }
  }
}
```

## 🔒 Isolamento e Segurança

### Isolamento por Workspace
- **Diretórios separados**: Cada workspace tem seu próprio diretório
- **Acesso controlado**: APIs verificam permissões antes de acessar dados
- **Namespace único**: IDs de conhecimento são únicos por workspace

### Controle de Acesso
```python
def get_workspace_knowledge(workspace_id: str, user_id: str):
    # Verificar se usuário tem acesso ao workspace
    if not has_workspace_access(user_id, workspace_id):
        raise PermissionError("Acesso negado ao workspace")
    
    # Carregar conhecimento apenas do workspace específico
    return load_knowledge_base(workspace_id)
```

## 📊 Versionamento e Backup

### Controle de Versão
- **Versionamento semântico**: Major.Minor.Patch
- **Snapshots automáticos**: Backup diário da base de conhecimento
- **Histórico de mudanças**: Log de todas as alterações

### Estrutura de Backup
```
backups/
├── workspace_001/
│   ├── 2025-01-15/
│   │   ├── knowledge_base.json
│   │   ├── conversation_history.json
│   │   └── metadata.json
│   ├── 2025-01-14/
│   └── ...
```

## 🔍 Busca e Indexação

### Busca Textual
- **Índice invertido**: Para busca rápida por palavras-chave
- **Tags**: Sistema de etiquetas para categorização
- **Busca fuzzy**: Tolerância a erros de digitação

### Busca Semântica
- **Embeddings**: Vetores de representação semântica
- **Similaridade coseno**: Para encontrar conhecimento relacionado
- **Cache de embeddings**: Evitar recálculo desnecessário

## 📈 Métricas e Analytics

### Estatísticas por Workspace
```json
{
  "workspace_id": "workspace_001",
  "stats": {
    "total_knowledge_entries": 156,
    "knowledge_by_type": {
      "fact": 89,
      "preference": 34,
      "context": 23,
      "pattern": 10
    },
    "total_conversations": 234,
    "avg_knowledge_usage": 3.2,
    "learning_rate": 0.15,
    "last_activity": "2025-01-15T15:45:00Z"
  }
}
```

## 🔄 Sincronização e Performance

### Cache em Memória
- **LRU Cache**: Para conhecimento frequentemente acessado
- **Invalidação automática**: Quando conhecimento é atualizado
- **Pré-carregamento**: De conhecimento relevante baseado em padrões

### Otimizações
- **Compressão**: JSON comprimido para reduzir espaço
- **Índices**: Para busca rápida por ID, tipo, tags
- **Lazy loading**: Carregar apenas quando necessário

## 🛠️ APIs de Gerenciamento

### Endpoints Principais
```python
# Conhecimento
POST   /api/workspace/{id}/knowledge/add
GET    /api/workspace/{id}/knowledge/search?q={query}
PUT    /api/workspace/{id}/knowledge/{knowledge_id}
DELETE /api/workspace/{id}/knowledge/{knowledge_id}

# Estatísticas
GET    /api/workspace/{id}/stats
GET    /api/workspace/{id}/evolution/insights

# Configuração
GET    /api/workspace/{id}/llm/preferences
PUT    /api/workspace/{id}/llm/preferences

# Backup/Restore
POST   /api/workspace/{id}/backup
POST   /api/workspace/{id}/restore
```

## 💡 Vantagens desta Abordagem

### Escalabilidade
- **Crescimento independente**: Cada workspace cresce conforme uso
- **Distribuição**: Possibilidade de distribuir workspaces em servidores
- **Paralelização**: Processamento simultâneo de múltiplos workspaces

### Flexibilidade
- **Configuração individual**: Cada workspace pode ter suas preferências
- **Evolução independente**: Conhecimento evolui baseado no contexto específico
- **Personalização**: Adaptação ao estilo e necessidades do usuário

### Manutenibilidade
- **Isolamento de problemas**: Erro em um workspace não afeta outros
- **Backup granular**: Backup e restore por workspace
- **Debugging facilitado**: Logs e métricas específicas por workspace


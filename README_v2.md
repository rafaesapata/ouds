# OpenManus - Correções Adicionais

## Correção do Erro 500 no Endpoint de Streaming (v3.5.0)

O erro `'dict' object has no attribute 'model'` foi corrigido com as seguintes alterações adicionais:

1. **Inicialização da memória do agente no SessionManager:**
   ```python
   # Criar agente para a sessão
   agent = ToolCallAgent(name=f"agent_{session_id}")
   
   # Inicializar memória do agente
   from app.agent.memory import Memory
   agent.memory = Memory()
   
   # Armazenar agente
   self.agents[workspace_id][session_id] = agent
   ```

2. **Verificação adicional no endpoint de streaming:**
   ```python
   # Verify agent has memory
   if workspace_id in session_manager.agents and session_id in session_manager.agents[workspace_id]:
       agent = session_manager.agents[workspace_id][session_id]
       if not hasattr(agent, 'memory') or agent.memory is None:
           from app.agent.memory import Memory
           agent.memory = Memory()
           logger.info(f"Initialized memory for agent in session {session_id}, workspace {workspace_id}")
   ```

## Como Testar

Para testar o endpoint de streaming com múltiplos workspaces, execute:

```bash
python3 test_streaming_v2.py --multi
```

Para testar um workspace específico:

```bash
python3 test_streaming_v2.py http://localhost:8000 rafaelsapata
```

## Versão

v3.5.0


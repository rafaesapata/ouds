# OUDS - Oráculo UDS

Sistema de IA conversacional baseado no OpenManus com interface web moderna.

## 📋 Visão Geral

O OUDS (Oráculo UDS) é uma interface web para o OpenManus que permite interação através de um chat moderno e intuitivo, similar ao ChatGPT. O sistema é composto por:

- **Backend API**: Servidor FastAPI que expõe endpoints REST para comunicação com o agente OpenManus
- **Frontend React**: Interface web moderna com design limpo e responsivo
- **Integração Completa**: Comunicação em tempo real entre frontend e backend

## 🏗️ Arquitetura

```
┌─────────────────┐    HTTP/REST    ┌─────────────────┐    Python    ┌─────────────────┐
│                 │ ──────────────► │                 │ ───────────► │                 │
│  Frontend React │                 │   API FastAPI   │              │  OpenManus Core │
│   (Port 5173)   │ ◄────────────── │   (Port 8000)   │ ◄─────────── │                 │
└─────────────────┘    JSON         └─────────────────┘              └─────────────────┘
```

## 🚀 Funcionalidades

### Frontend (React)
- ✅ Interface de chat moderna similar ao ChatGPT
- ✅ Design responsivo e limpo
- ✅ Indicador de status de conexão
- ✅ Histórico de conversas
- ✅ Feedback visual para carregamento
- ✅ Tratamento de erros
- ✅ Botão para nova conversa

### Backend (FastAPI)
- ✅ API REST completa
- ✅ Gerenciamento de sessões
- ✅ Endpoints para chat, histórico e sessões
- ✅ Suporte a WebSocket (preparado)
- ✅ CORS configurado
- ✅ Tratamento de erros robusto

## 📁 Estrutura do Projeto

```
OUDS/
├── OpenManus/                 # Código base do OpenManus
│   ├── app/                   # Módulos principais
│   ├── api_server.py          # Servidor da API OUDS
│   └── requirements.txt       # Dependências Python
│
└── ouds-frontend/             # Frontend React
    ├── src/
    │   ├── App.jsx           # Componente principal
    │   ├── App.css           # Estilos
    │   └── components/ui/    # Componentes UI (shadcn/ui)
    ├── package.json          # Dependências Node.js
    └── index.html            # Página principal
```

## 🛠️ Instalação e Configuração

### Pré-requisitos
- Python 3.11+
- Node.js 20+
- npm ou pnpm

### 1. Configurar Backend

```bash
# Navegar para o diretório do OpenManus
cd OpenManus

# Instalar dependências Python
pip install -r requirements.txt

# Configurar variáveis de ambiente (opcional)
export OPENAI_API_KEY="sua_chave_aqui"

# Iniciar servidor da API
PYTHONPATH=/path/to/OpenManus python3 api_server.py
```

### 2. Configurar Frontend

```bash
# Navegar para o diretório do frontend
cd ouds-frontend

# Instalar dependências
npm install

# Iniciar servidor de desenvolvimento
npm run dev --host
```

## 🔧 Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` no diretório `OpenManus/`:

```env
# Chave da API OpenAI (obrigatória)
OPENAI_API_KEY=sk-...

# Configurações opcionais
WORKSPACE_ROOT=/path/to/workspace
LOG_LEVEL=INFO
```

### Configuração da API

O arquivo `api_server.py` pode ser customizado para:
- Alterar porta do servidor (padrão: 8000)
- Configurar CORS para domínios específicos
- Ajustar timeouts e limites

## 📡 API Endpoints

### GET `/`
Informações básicas da API

### POST `/api/chat`
Enviar mensagem para o agente
```json
{
  "message": "Sua mensagem aqui",
  "session_id": "opcional"
}
```

### GET `/api/sessions`
Listar sessões ativas

### GET `/api/sessions/{session_id}/history`
Obter histórico de uma sessão

### DELETE `/api/sessions/{session_id}`
Deletar uma sessão

### WebSocket `/ws/{session_id}`
Comunicação em tempo real (preparado para uso futuro)

## 🎨 Interface do Usuário

A interface foi projetada para ser:
- **Limpa e Minimalista**: Similar ao chat do Manus original
- **Responsiva**: Funciona em desktop e mobile
- **Intuitiva**: Fácil de usar sem necessidade de treinamento
- **Moderna**: Usa componentes shadcn/ui e Tailwind CSS

### Características Visuais
- Header com logo e status de conexão
- Área de chat com scroll automático
- Input com botão de envio
- Indicadores de carregamento
- Tratamento visual de erros
- Botão para nova conversa

## 🔒 Segurança

- CORS configurado para desenvolvimento
- Validação de entrada com Pydantic
- Tratamento seguro de sessões
- Logs de segurança implementados

## 📈 Performance

- Comunicação assíncrona
- Gerenciamento eficiente de sessões
- Cleanup automático de recursos
- Otimizações de frontend com Vite

## 🐛 Troubleshooting

### Problemas Comuns

1. **Erro "ModuleNotFoundError"**
   ```bash
   # Solução: Configurar PYTHONPATH
   export PYTHONPATH=/path/to/OpenManus
   ```

2. **API não conecta**
   - Verificar se o servidor está rodando na porta 8000
   - Verificar configuração de CORS
   - Verificar logs do servidor

3. **Frontend não carrega**
   - Verificar se as dependências foram instaladas
   - Verificar se a porta 5173 está disponível

## 🚀 Deploy em Produção

### Backend
```bash
# Usar gunicorn para produção
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_server:app --bind 0.0.0.0:8000
```

### Frontend
```bash
# Build para produção
npm run build

# Servir arquivos estáticos
npm install -g serve
serve -s dist -l 3000
```

## 🔮 Próximos Passos

- [ ] Implementar autenticação de usuários
- [ ] Adicionar suporte a upload de arquivos
- [ ] Implementar WebSocket para comunicação em tempo real
- [ ] Adicionar temas dark/light
- [ ] Implementar histórico persistente
- [ ] Adicionar métricas e analytics
- [ ] Implementar rate limiting
- [ ] Adicionar testes automatizados

## 📝 Changelog

### v1.0.0 (2025-06-05)
- ✅ Implementação inicial do OUDS
- ✅ API REST completa
- ✅ Interface React moderna
- ✅ Integração com OpenManus
- ✅ Gerenciamento de sessões
- ✅ Documentação completa

## 🤝 Contribuição

Para contribuir com o projeto:

1. Fork o repositório
2. Crie uma branch para sua feature
3. Implemente as mudanças
4. Adicione testes se necessário
5. Submeta um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 👥 Equipe

- **Desenvolvimento**: Baseado no OpenManus da equipe MetaGPT
- **Interface OUDS**: Implementação customizada para UDS

---

**OUDS - Oráculo UDS v1.0.19**  
*Sistema de IA conversacional baseado no OpenManus*


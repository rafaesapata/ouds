# OUDS - Configuração de Proxy Frontend → Backend

## 📡 **Configuração Implementada**

### **Cenário:**
- **Frontend:** Acessível remotamente via `http://seu-servidor:5173`
- **Backend:** Rodando localmente em `http://localhost:8000`
- **Proxy:** Frontend redireciona chamadas da API para o backend local

### **Rotas do Proxy:**
```
/api/*          → http://localhost:8000/*
/docs           → http://localhost:8000/docs
/openapi.json   → http://localhost:8000/openapi.json
/health         → http://localhost:8000/health
```

## 🚀 **Como usar:**

### **1. Iniciar Backend (local):**
```bash
cd /home/ec2-user/ouds
./fix-backend.sh
# Backend rodará em http://localhost:8000
```

### **2. Iniciar Frontend (acessível remotamente):**
```bash
cd ouds-frontend
npm run dev
# Frontend rodará em http://0.0.0.0:5173
```

### **3. Acessar remotamente:**
```
http://seu-servidor-ip:5173
```

## 🔧 **Configurações aplicadas:**

### **vite.config.js:**
- Host: `0.0.0.0` (permite acesso remoto)
- Proxy `/api` → backend local
- Logs de proxy para debug

### **.env:**
- `OUDS_FRONTEND_HOST=0.0.0.0`
- `OUDS_API_URL=http://localhost:8000`

## 🌐 **URLs de acesso:**

### **Remoto (você):**
- Frontend: `http://seu-servidor:5173`
- API via proxy: `http://seu-servidor:5173/api/*`
- Docs via proxy: `http://seu-servidor:5173/docs`

### **Local (servidor):**
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## 🛡️ **Segurança:**
- Backend permanece local (não exposto)
- Frontend faz proxy transparente
- Logs de proxy para monitoramento

## 🔍 **Debug:**
- Logs do proxy aparecem no console do Vite
- Formato: `Proxying request: GET /api/chat → http://localhost:8000/chat`

## 📋 **Exemplo de uso no código:**
```javascript
// No frontend, use rotas relativas:
fetch('/api/chat', { method: 'POST', ... })
// Será automaticamente redirecionado para http://localhost:8000/chat
```


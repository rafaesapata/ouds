#!/bin/bash

# OUDS - Script de diagnóstico do proxy
# =====================================

echo "🔍 OUDS - Diagnóstico do proxy /api..."
echo "======================================"

# Diretório do projeto
PROJECT_DIR="/home/ubuntu/ouds-project"
FRONTEND_DIR="$PROJECT_DIR/ouds-frontend"

echo "📁 Verificando diretórios..."
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Erro: Diretório frontend não encontrado!"
    exit 1
fi

cd "$FRONTEND_DIR"

echo ""
echo "🔧 1. CONFIGURAÇÃO DO PROXY:"
echo "============================"
echo "📋 Frontend → Backend:"
echo "   http://o.udstec.io/api → http://localhost:8000"
echo "   Proxy fixo no código (sem variáveis)"

echo ""
echo "🌐 2. TESTANDO BACKEND:"
echo "======================"

# Testar backend diretamente
echo "🧪 Testando backend direto..."
if timeout 5 curl -s -f "http://localhost:8000/health" > /dev/null 2>&1; then
    echo "✅ Backend funcionando em localhost:8000"
    timeout 5 curl -s "http://localhost:8000/health" 2>/dev/null
else
    echo "❌ Backend não responde em localhost:8000"
    echo "💡 Inicie o backend: cd OpenManus && python3 api_server.py"
fi

echo ""
echo "🔍 3. VERIFICANDO FRONTEND:"
echo "=========================="

# Verificar se frontend está rodando
if netstat -tlnp 2>/dev/null | grep -q ":80"; then
    echo "✅ Frontend rodando na porta 80"
    
    # Testar proxy local
    echo "🧪 Testando proxy local..."
    if timeout 5 curl -s -f "http://localhost:80/api/health" > /dev/null 2>&1; then
        echo "✅ Proxy /api funcionando localmente"
        echo "📄 Resposta do proxy:"
        timeout 5 curl -s "http://localhost:80/api/health" 2>/dev/null | head -3
    else
        echo "❌ Proxy /api NÃO funciona localmente"
    fi
else
    echo "❌ Frontend não está rodando na porta 80"
    echo "💡 Execute: sudo npm run dev"
fi

echo ""
echo "🔍 4. VERIFICANDO PROCESSOS:"
echo "============================"
echo "📋 Backend (Python):"
ps aux | grep -E "(python.*api_server|python.*8000)" | grep -v grep || echo "❌ Backend não encontrado"

echo ""
echo "📋 Frontend (Node.js):"
ps aux | grep -E "(npm run dev|vite)" | grep -v grep || echo "❌ Frontend não encontrado"

echo ""
echo "🔍 5. TESTANDO CONECTIVIDADE EXTERNA:"
echo "====================================="
echo "🧪 Testando acesso externo ao proxy..."
if timeout 10 curl -s -f "http://o.udstec.io/api/health" > /dev/null 2>&1; then
    echo "✅ Proxy /api funcionando externamente"
    echo "📄 Resposta:"
    timeout 10 curl -s "http://o.udstec.io/api/health" 2>/dev/null | head -3
else
    echo "❌ Proxy /api NÃO funciona externamente"
fi

echo ""
echo "📋 6. RESUMO:"
echo "============"
echo "🎯 URLs para testar:"
echo "Frontend: http://o.udstec.io/"
echo "API via proxy: http://o.udstec.io/api/health"
echo "Backend direto: http://localhost:8000/health"

echo ""
echo "🔧 Comandos úteis:"
echo "=================="
echo "Iniciar backend: cd OpenManus && python3 api_server.py &"
echo "Iniciar frontend: cd ouds-frontend && sudo npm run dev"
echo "Testar proxy: curl http://o.udstec.io/api/health"
echo "Ver logs: console do browser (F12)"

echo ""
echo "🎯 Como funciona:"
echo "================="
echo "1. Frontend faz requisição para http://o.udstec.io/api/chat"
echo "2. Proxy do Vite intercepta /api"
echo "3. Redireciona para http://localhost:8000/chat"
echo "4. Backend responde"
echo "5. Proxy retorna resposta para frontend"


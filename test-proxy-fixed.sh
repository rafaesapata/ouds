#!/bin/bash

# OUDS - Diagnóstico do proxy com endpoints corretos
# ==================================================

echo "🔍 OUDS - Diagnóstico do proxy (endpoints corretos)..."
echo "====================================================="

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
echo "   http://o.udstec.io/api → http://localhost:8000/api"
echo "   Proxy sem rewrite (mantém /api)"

echo ""
echo "🌐 2. TESTANDO BACKEND:"
echo "======================"

# Testar backend diretamente
echo "🧪 Testando backend direto..."
if timeout 5 curl -s -f "http://localhost:8000/" > /dev/null 2>&1; then
    echo "✅ Backend funcionando em localhost:8000"
    timeout 5 curl -s "http://localhost:8000/" 2>/dev/null
else
    echo "❌ Backend não responde em localhost:8000"
    echo "💡 Inicie o backend: cd OpenManus && python3 api_server.py"
fi

echo ""
echo "🧪 Testando POST /api/chat..."
if timeout 5 curl -s -f -X POST -H "Content-Type: application/json" -d '{"message":"test"}' "http://localhost:8000/api/chat" > /dev/null 2>&1; then
    echo "✅ POST /api/chat funcionando"
else
    echo "❌ POST /api/chat não funciona"
fi

echo ""
echo "🔍 3. VERIFICANDO FRONTEND:"
echo "=========================="

# Verificar se frontend está rodando
if netstat -tlnp 2>/dev/null | grep -q ":80"; then
    echo "✅ Frontend rodando na porta 80"
    
    # Testar proxy local
    echo "🧪 Testando proxy local..."
    if timeout 5 curl -s -f "http://localhost:80/api/" > /dev/null 2>&1; then
        echo "✅ Proxy /api/ funcionando localmente"
        echo "📄 Resposta do proxy:"
        timeout 5 curl -s "http://localhost:80/api/" 2>/dev/null | head -3
    else
        echo "❌ Proxy /api/ NÃO funciona localmente"
    fi
    
    # Testar POST via proxy
    echo "🧪 Testando POST /api/chat via proxy..."
    if timeout 5 curl -s -f -X POST -H "Content-Type: application/json" -d '{"message":"test"}' "http://localhost:80/api/chat" > /dev/null 2>&1; then
        echo "✅ Proxy POST /api/chat funcionando"
    else
        echo "❌ Proxy POST /api/chat não funciona"
    fi
else
    echo "❌ Frontend não está rodando na porta 80"
    echo "💡 Execute: sudo npm run dev"
fi

echo ""
echo "🔍 4. TESTANDO CONECTIVIDADE EXTERNA:"
echo "====================================="
echo "🧪 Testando acesso externo ao proxy..."
if timeout 10 curl -s -f "http://o.udstec.io/api/" > /dev/null 2>&1; then
    echo "✅ Proxy /api/ funcionando externamente"
    echo "📄 Resposta:"
    timeout 10 curl -s "http://o.udstec.io/api/" 2>/dev/null | head -3
else
    echo "❌ Proxy /api/ NÃO funciona externamente"
fi

echo ""
echo "🧪 Testando POST /api/chat externo..."
if timeout 10 curl -s -f -X POST -H "Content-Type: application/json" -d '{"message":"test"}' "http://o.udstec.io/api/chat" > /dev/null 2>&1; then
    echo "✅ Proxy POST /api/chat funcionando externamente"
else
    echo "❌ Proxy POST /api/chat NÃO funciona externamente"
fi

echo ""
echo "📋 5. RESUMO:"
echo "============"
echo "🎯 URLs para testar:"
echo "Frontend: http://o.udstec.io/"
echo "API via proxy: http://o.udstec.io/api/"
echo "Chat via proxy: http://o.udstec.io/api/chat"
echo "Backend direto: http://localhost:8000/"

echo ""
echo "🔧 Comandos úteis:"
echo "=================="
echo "Iniciar backend: cd OpenManus && python3 api_server.py &"
echo "Iniciar frontend: cd ouds-frontend && sudo npm run dev"
echo "Testar chat: curl -X POST -H 'Content-Type: application/json' -d '{\"message\":\"test\"}' http://o.udstec.io/api/chat"
echo "Ver logs: console do browser (F12)"


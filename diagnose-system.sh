#!/bin/bash

# OUDS - Script de diagnóstico simplificado
# ==========================================

echo "🔍 OUDS - Diagnóstico do sistema..."
echo "==================================="

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
echo "🔧 1. CONFIGURAÇÃO:"
echo "=================="
echo "📋 URL da API:"
grep "VITE_API_URL" .env 2>/dev/null || echo "❌ VITE_API_URL não encontrada"

echo ""
echo "📋 Versão:"
grep "OUDS_VERSION" .env 2>/dev/null || echo "❌ OUDS_VERSION não encontrada"

echo ""
echo "🌐 2. TESTANDO BACKEND:"
echo "======================"

# Extrair URL do backend
BACKEND_URL=$(grep "VITE_API_URL" .env 2>/dev/null | cut -d'=' -f2)
if [ -z "$BACKEND_URL" ]; then
    BACKEND_URL="http://localhost:8000"
fi

echo "🎯 Backend URL: $BACKEND_URL"

# Testar backend diretamente
echo "🧪 Testando backend..."
if timeout 5 curl -s -f "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo "✅ Backend funcionando"
    timeout 5 curl -s "$BACKEND_URL/health" 2>/dev/null
else
    echo "❌ Backend não responde"
    echo "💡 Inicie o backend: cd OpenManus && python3 api_server.py"
fi

echo ""
echo "🔍 3. VERIFICANDO FRONTEND:"
echo "=========================="

# Verificar se frontend está rodando
if netstat -tlnp 2>/dev/null | grep -q ":80"; then
    echo "✅ Frontend rodando na porta 80"
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
echo "🔍 5. TESTANDO CONECTIVIDADE:"
echo "============================="
echo "🧪 Testando acesso externo..."
if timeout 10 curl -s -f "http://52.71.245.167/" > /dev/null 2>&1; then
    echo "✅ Frontend acessível externamente"
else
    echo "❌ Frontend não acessível externamente"
fi

echo ""
echo "📋 6. RESUMO:"
echo "============"
echo "🎯 URLs para testar:"
echo "Frontend: http://o.udstec.io/"
echo "Backend: $BACKEND_URL/health"

echo ""
echo "🔧 Comandos úteis:"
echo "=================="
echo "Iniciar backend: cd OpenManus && python3 api_server.py &"
echo "Iniciar frontend: cd ouds-frontend && sudo npm run dev"
echo "Ver logs: tail -f logs/ouds.log"


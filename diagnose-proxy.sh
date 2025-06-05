#!/bin/bash

# OUDS - Diagnóstico completo do proxy /api
# ==========================================

echo "🔍 OUDS - Diagnóstico completo do proxy /api..."
echo "==============================================="

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
echo "🔧 1. VARIÁVEIS DO .ENV:"
echo "========================"
echo "📋 Variáveis relacionadas à API:"
grep -E "(VITE_API_URL|OUDS_API_URL|VITE_PROXY)" .env 2>/dev/null || echo "❌ Nenhuma variável encontrada"

echo ""
echo "🌐 2. TESTANDO BACKEND:"
echo "======================"

# Extrair URL do backend
BACKEND_URL=$(grep "VITE_API_URL" .env 2>/dev/null | cut -d'=' -f2)
if [ -z "$BACKEND_URL" ]; then
    BACKEND_URL=$(grep "OUDS_API_URL" .env 2>/dev/null | cut -d'=' -f2)
fi
if [ -z "$BACKEND_URL" ]; then
    BACKEND_URL="http://localhost:8000"
fi

echo "🎯 Backend URL configurada: $BACKEND_URL"

# Testar backend diretamente
echo "🧪 Testando backend diretamente..."
if timeout 5 curl -s -f "$BACKEND_URL/" > /dev/null 2>&1; then
    echo "✅ Backend respondendo em $BACKEND_URL/"
    echo "📄 Resposta:"
    timeout 5 curl -s "$BACKEND_URL/" 2>/dev/null | head -3
else
    echo "❌ Backend NÃO está respondendo em $BACKEND_URL/"
    echo "💡 Verifique se o backend está rodando:"
    echo "   cd OpenManus && python3 api_server.py"
fi

echo ""
echo "🧪 Testando endpoint /health..."
if timeout 5 curl -s -f "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo "✅ Endpoint /health funcionando"
    timeout 5 curl -s "$BACKEND_URL/health" 2>/dev/null
else
    echo "❌ Endpoint /health não responde"
fi

echo ""
echo "🔍 3. VERIFICANDO FRONTEND:"
echo "=========================="

# Verificar se frontend está rodando
if netstat -tlnp 2>/dev/null | grep -q ":5173"; then
    echo "✅ Frontend rodando na porta 5173"
    
    # Testar proxy local
    echo "🧪 Testando proxy local..."
    if timeout 5 curl -s -f "http://localhost:5173/api/" > /dev/null 2>&1; then
        echo "✅ Proxy /api funcionando localmente"
        echo "📄 Resposta do proxy:"
        timeout 5 curl -s "http://localhost:5173/api/" 2>/dev/null | head -3
    else
        echo "❌ Proxy /api NÃO funciona localmente"
        echo "🔍 Testando outros endpoints do proxy..."
        
        # Testar /health via proxy
        if timeout 5 curl -s -f "http://localhost:5173/health" > /dev/null 2>&1; then
            echo "✅ Proxy /health funcionando"
        else
            echo "❌ Proxy /health também não funciona"
        fi
    fi
else
    echo "❌ Frontend NÃO está rodando na porta 5173"
    echo "💡 Execute: npm run dev"
fi

echo ""
echo "🔍 4. VERIFICANDO PROCESSOS:"
echo "============================"
echo "📋 Processos Python (backend):"
ps aux | grep -E "(python|api_server)" | grep -v grep || echo "❌ Nenhum processo Python encontrado"

echo ""
echo "📋 Processos Node.js (frontend):"
ps aux | grep -E "(node|npm|vite)" | grep -v grep || echo "❌ Nenhum processo Node.js encontrado"

echo ""
echo "🔍 5. VERIFICANDO PORTAS:"
echo "========================"
echo "📋 Porta 8000 (backend):"
netstat -tlnp 2>/dev/null | grep ":8000" || echo "❌ Porta 8000 não está em uso"

echo ""
echo "📋 Porta 5173 (frontend):"
netstat -tlnp 2>/dev/null | grep ":5173" || echo "❌ Porta 5173 não está em uso"

echo ""
echo "🔍 6. TESTANDO CONECTIVIDADE EXTERNA:"
echo "====================================="
echo "🧪 Testando acesso externo ao frontend..."
if timeout 10 curl -s -f "http://52.71.245.167:5173/" > /dev/null 2>&1; then
    echo "✅ Frontend acessível externamente"
    
    echo "🧪 Testando proxy externo /api/..."
    if timeout 10 curl -s -f "http://52.71.245.167:5173/api/" > /dev/null 2>&1; then
        echo "✅ Proxy /api funcionando externamente"
    else
        echo "❌ Proxy /api NÃO funciona externamente"
    fi
    
    echo "🧪 Testando proxy externo /health..."
    if timeout 10 curl -s -f "http://52.71.245.167:5173/health" > /dev/null 2>&1; then
        echo "✅ Proxy /health funcionando externamente"
    else
        echo "❌ Proxy /health NÃO funciona externamente"
    fi
else
    echo "❌ Frontend NÃO acessível externamente"
fi

echo ""
echo "📋 7. RESUMO E SOLUÇÕES:"
echo "========================"
echo "🔧 Para resolver problemas do proxy /api:"
echo ""
echo "1️⃣ Se backend não estiver rodando:"
echo "   cd OpenManus && python3 api_server.py &"
echo ""
echo "2️⃣ Se frontend não estiver rodando:"
echo "   cd ouds-frontend && npm run dev"
echo ""
echo "3️⃣ Se proxy não funcionar:"
echo "   - Verifique logs no console do browser (F12)"
echo "   - Reinicie frontend: Ctrl+C e npm run dev"
echo "   - Verifique variável VITE_API_URL no .env"
echo ""
echo "4️⃣ Para debug avançado:"
echo "   - Logs do frontend: npm run dev (veja console)"
echo "   - Logs do backend: python3 api_server.py (veja terminal)"
echo "   - Teste manual: curl http://localhost:5173/api/"

echo ""
echo "🎯 URLs para testar:"
echo "==================="
echo "Backend direto: $BACKEND_URL/"
echo "Proxy local: http://localhost:5173/api/"
echo "Proxy externo: http://52.71.245.167:5173/api/"
echo "Frontend: http://o.udstec.io/"


#!/bin/bash

# OUDS - Teste dos endpoints corretos do backend
# ==============================================

echo "🔍 OUDS - Testando endpoints que EXISTEM no backend..."
echo "====================================================="

BACKEND_URL="http://localhost:8000"

echo "🎯 Testando backend em: $BACKEND_URL"
echo ""

# Função para testar endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    echo "🧪 Testando $method $endpoint:"
    
    if [ "$method" = "GET" ]; then
        if timeout 5 curl -s -f "$BACKEND_URL$endpoint" > /dev/null 2>&1; then
            echo "✅ $method $endpoint - Funciona"
            curl -s "$BACKEND_URL$endpoint" 2>/dev/null | head -2
        else
            echo "❌ $method $endpoint - Não funciona"
        fi
    elif [ "$method" = "POST" ]; then
        if timeout 5 curl -s -f -X POST -H "Content-Type: application/json" -d "$data" "$BACKEND_URL$endpoint" > /dev/null 2>&1; then
            echo "✅ $method $endpoint - Funciona"
            curl -s -X POST -H "Content-Type: application/json" -d "$data" "$BACKEND_URL$endpoint" 2>/dev/null | head -2
        else
            echo "❌ $method $endpoint - Não funciona"
        fi
    fi
    echo ""
}

echo "📋 ENDPOINTS QUE EXISTEM (conforme api_server.py):"
echo "=================================================="

# Testar endpoints que realmente existem
test_endpoint "GET" "/"
test_endpoint "POST" "/api/chat" '{"message":"Olá, teste de conectividade"}'
test_endpoint "GET" "/api/sessions"

echo "📋 ENDPOINTS QUE NÃO EXISTEM:"
echo "============================="

# Testar endpoints que não existem (para confirmar)
test_endpoint "GET" "/health"
test_endpoint "GET" "/api/health"

echo "📋 RESUMO:"
echo "=========="
echo "✅ Endpoints funcionais:"
echo "   GET  / (raiz do backend)"
echo "   POST /api/chat (chat principal)"
echo "   GET  /api/sessions (listar sessões)"
echo ""
echo "❌ Endpoints que não existem:"
echo "   /health"
echo "   /api/health"
echo ""
echo "🔧 Frontend deve usar:"
echo "   - http://o.udstec.io/api/ (verificar backend)"
echo "   - http://o.udstec.io/api/chat (chat)"
echo "   - http://o.udstec.io/api/sessions (sessões)"


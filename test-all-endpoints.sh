#!/bin/bash

# OUDS - Teste completo de endpoints do backend
# =============================================

echo "🔍 OUDS - Testando TODOS os endpoints do backend..."
echo "=================================================="

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
            echo "❌ $method $endpoint - Não funciona (404 ou erro)"
        fi
    elif [ "$method" = "POST" ]; then
        if timeout 5 curl -s -f -X POST -H "Content-Type: application/json" -d "$data" "$BACKEND_URL$endpoint" > /dev/null 2>&1; then
            echo "✅ $method $endpoint - Funciona"
        else
            echo "❌ $method $endpoint - Não funciona (404 ou erro)"
        fi
    fi
    echo ""
}

# Testar endpoints comuns
test_endpoint "GET" "/"
test_endpoint "GET" "/health"
test_endpoint "GET" "/api"
test_endpoint "GET" "/api/"
test_endpoint "GET" "/api/health"
test_endpoint "GET" "/api/chat"
test_endpoint "GET" "/chat"
test_endpoint "GET" "/docs"
test_endpoint "GET" "/api/docs"
test_endpoint "GET" "/openapi.json"
test_endpoint "GET" "/api/openapi.json"

# Testar POST endpoints
test_endpoint "POST" "/chat" '{"message":"test"}'
test_endpoint "POST" "/api/chat" '{"message":"test"}'

echo "📋 ANÁLISE DOS RESULTADOS:"
echo "=========================="
echo ""
echo "🎯 Com base nos testes, configure o proxy assim:"
echo ""
echo "Se o backend tem endpoints /api/*, use:"
echo "   // SEM rewrite - mantém /api"
echo "   '/api': { target: 'http://localhost:8000' }"
echo ""
echo "Se o backend tem endpoints sem /api, use:"
echo "   // COM rewrite - remove /api"
echo "   '/api': { target: 'http://localhost:8000', rewrite: (path) => path.replace(/^\/api/, '') }"
echo ""
echo "🔧 Agora teste novamente:"
echo "curl http://o.udstec.io/api/health"
echo "curl http://o.udstec.io/api/chat"


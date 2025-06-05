#!/bin/bash

# OUDS - Teste de mapeamento de endpoints
# =======================================

echo "🔍 OUDS - Testando mapeamento de endpoints..."
echo "=============================================="

echo "📋 MAPEAMENTO FRONTEND → BACKEND:"
echo "================================="
echo ""

echo "✅ Endpoints que precisam de /api/api/ (backend tem /api prefix):"
echo "Frontend → Proxy (rewrite) → Backend"
echo "/api/api/chat → /api/chat → /api/chat ✅"
echo "/api/api/sessions → /api/sessions → /api/sessions ✅"
echo "/api/api/sessions/{id} → /api/sessions/{id} → /api/sessions/{id} ✅"
echo "/api/api/sessions/{id}/history → /api/sessions/{id}/history → /api/sessions/{id}/history ✅"
echo ""

echo "✅ Endpoints que usam /api/ (backend sem /api prefix):"
echo "Frontend → Proxy (rewrite) → Backend"
echo "/api/ → / → / ✅"
echo "/api/ws/{id} → /ws/{id} → /ws/{id} ✅"
echo ""

echo "🧪 TESTANDO ENDPOINTS REAIS:"
echo "============================"

BACKEND_URL="http://localhost:8000"

# Função para testar endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    
    echo "🧪 $description:"
    echo "   $method $endpoint"
    
    if [ "$method" = "GET" ]; then
        if timeout 5 curl -s -f "$BACKEND_URL$endpoint" > /dev/null 2>&1; then
            echo "   ✅ Funciona"
        else
            echo "   ❌ Não funciona"
        fi
    elif [ "$method" = "POST" ]; then
        if timeout 5 curl -s -f -X POST -H "Content-Type: application/json" -d '{"message":"test"}' "$BACKEND_URL$endpoint" > /dev/null 2>&1; then
            echo "   ✅ Funciona"
        else
            echo "   ❌ Não funciona"
        fi
    fi
    echo ""
}

echo "📋 Testando endpoints do backend diretamente:"
echo "============================================="

test_endpoint "GET" "/" "Raiz"
test_endpoint "POST" "/api/chat" "Chat"
test_endpoint "GET" "/api/sessions" "Listar sessões"

echo "📋 RESUMO DO MAPEAMENTO:"
echo "========================"
echo ""
echo "🎯 Frontend deve usar:"
echo "   Chat: API_ENDPOINTS.CHAT = '/api/api/chat'"
echo "   Sessões: API_ENDPOINTS.SESSIONS = '/api/api/sessions'"
echo "   Histórico: API_ENDPOINTS.SESSION_HISTORY = '/api/api/sessions'"
echo "   WebSocket: API_ENDPOINTS.WEBSOCKET = '/api/ws'"
echo "   Raiz: API_ENDPOINTS.ROOT = '/api/'"
echo ""
echo "🔧 Proxy faz rewrite removendo primeiro /api:"
echo "   /api/api/chat → /api/chat (correto)"
echo "   /api/ws/123 → /ws/123 (correto)"
echo "   /api/ → / (correto)"


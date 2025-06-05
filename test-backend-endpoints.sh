#!/bin/bash

# OUDS - Teste de endpoints do backend
# ====================================

echo "🔍 OUDS - Testando endpoints do backend..."
echo "=========================================="

BACKEND_URL="http://localhost:8000"

echo "🎯 Testando backend em: $BACKEND_URL"
echo ""

# Testar endpoint raiz
echo "🧪 1. Testando endpoint raiz (/):"
if timeout 5 curl -s -f "$BACKEND_URL/" > /dev/null 2>&1; then
    echo "✅ GET / - Funciona"
    curl -s "$BACKEND_URL/" 2>/dev/null | head -3
else
    echo "❌ GET / - Não funciona"
fi

echo ""

# Testar /health
echo "🧪 2. Testando /health:"
if timeout 5 curl -s -f "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo "✅ GET /health - Funciona"
    curl -s "$BACKEND_URL/health" 2>/dev/null
else
    echo "❌ GET /health - Não funciona"
fi

echo ""

# Testar /api/health
echo "🧪 3. Testando /api/health:"
if timeout 5 curl -s -f "$BACKEND_URL/api/health" > /dev/null 2>&1; then
    echo "✅ GET /api/health - Funciona"
    curl -s "$BACKEND_URL/api/health" 2>/dev/null
else
    echo "❌ GET /api/health - Não funciona"
fi

echo ""

# Testar /chat
echo "🧪 4. Testando /chat:"
if timeout 5 curl -s -f "$BACKEND_URL/chat" > /dev/null 2>&1; then
    echo "✅ GET /chat - Funciona"
    curl -s "$BACKEND_URL/chat" 2>/dev/null | head -3
else
    echo "❌ GET /chat - Não funciona"
fi

echo ""

# Testar /api/chat
echo "🧪 5. Testando /api/chat:"
if timeout 5 curl -s -f "$BACKEND_URL/api/chat" > /dev/null 2>&1; then
    echo "✅ GET /api/chat - Funciona"
    curl -s "$BACKEND_URL/api/chat" 2>/dev/null | head -3
else
    echo "❌ GET /api/chat - Não funciona"
fi

echo ""

# Testar POST /chat
echo "🧪 6. Testando POST /chat:"
if timeout 5 curl -s -f -X POST -H "Content-Type: application/json" -d '{"message":"test"}' "$BACKEND_URL/chat" > /dev/null 2>&1; then
    echo "✅ POST /chat - Funciona"
else
    echo "❌ POST /chat - Não funciona"
fi

echo ""

# Testar POST /api/chat
echo "🧪 7. Testando POST /api/chat:"
if timeout 5 curl -s -f -X POST -H "Content-Type: application/json" -d '{"message":"test"}' "$BACKEND_URL/api/chat" > /dev/null 2>&1; then
    echo "✅ POST /api/chat - Funciona"
else
    echo "❌ POST /api/chat - Não funciona"
fi

echo ""
echo "📋 RESUMO:"
echo "=========="
echo "🎯 Com base nos testes acima, o proxy deve ser configurado para:"
echo ""
echo "Se o backend tem /health e /chat:"
echo "   rewrite: (path) => path.replace(/^\/api/, '')"
echo ""
echo "Se o backend tem /api/health e /api/chat:"
echo "   rewrite: (path) => path  // sem rewrite"
echo ""
echo "🔧 Ajuste o vite.config.js conforme os endpoints que funcionam!"


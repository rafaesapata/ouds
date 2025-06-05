#!/bin/bash

# OUDS - Script para testar configuração do proxy
# ===============================================

echo "🔍 OUDS - Testando configuração do proxy..."
echo "============================================="

# Diretório do frontend
FRONTEND_DIR="/home/ubuntu/ouds-project/ouds-frontend"

echo "📁 Verificando diretório: $FRONTEND_DIR"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Erro: Diretório frontend não encontrado!"
    exit 1
fi

cd "$FRONTEND_DIR"

echo ""
echo "🔧 Variáveis do .env relacionadas ao proxy:"
echo "============================================"
grep -E "(VITE_API_URL|VITE_PROXY|OUDS_API_URL)" .env || echo "❌ Nenhuma variável encontrada"

echo ""
echo "🌐 Testando conectividade com o backend:"
echo "========================================"

# Extrair URL do backend do .env
BACKEND_URL=$(grep "VITE_API_URL" .env | cut -d'=' -f2)
if [ -z "$BACKEND_URL" ]; then
    BACKEND_URL=$(grep "OUDS_API_URL" .env | cut -d'=' -f2)
fi

if [ -z "$BACKEND_URL" ]; then
    BACKEND_URL="http://localhost:8000"
fi

echo "🎯 Backend URL: $BACKEND_URL"

# Testar conectividade
echo "🧪 Testando $BACKEND_URL/health..."
if curl -s -f "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo "✅ Backend acessível em $BACKEND_URL/health"
    curl -s "$BACKEND_URL/health" | head -3
else
    echo "❌ Backend não acessível em $BACKEND_URL/health"
fi

echo ""
echo "🧪 Testando $BACKEND_URL/..."
if curl -s -f "$BACKEND_URL/" > /dev/null 2>&1; then
    echo "✅ Backend acessível em $BACKEND_URL/"
    curl -s "$BACKEND_URL/" | head -3
else
    echo "❌ Backend não acessível em $BACKEND_URL/"
fi

echo ""
echo "🔍 Verificando se o frontend está rodando:"
echo "=========================================="
if netstat -tlnp 2>/dev/null | grep -q ":5173"; then
    echo "✅ Frontend rodando na porta 5173"
    echo "🌐 Teste o proxy em: http://o.udstec.io/api/"
    echo "🌐 Teste direto em: http://o.udstec.io/health"
else
    echo "❌ Frontend não está rodando na porta 5173"
    echo "💡 Execute: npm run dev"
fi

echo ""
echo "📋 Comandos para debug:"
echo "======================"
echo "1. Ver logs do frontend: npm run dev"
echo "2. Testar proxy direto: curl http://localhost:5173/api/"
echo "3. Testar backend direto: curl $BACKEND_URL/"
echo "4. Ver configuração: cat .env | grep -E '(API_URL|PROXY)'"

echo ""
echo "🔧 Se o proxy não funcionar:"
echo "============================"
echo "1. Verifique se o backend está rodando"
echo "2. Verifique as variáveis VITE_API_URL no .env"
echo "3. Reinicie o frontend: npm run dev"
echo "4. Verifique logs no console do browser (F12)"


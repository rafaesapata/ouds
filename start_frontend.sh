#!/bin/bash

# OUDS - Script de Inicialização do Frontend
# ==========================================

echo "🎨 OUDS - Iniciando Frontend (Interface Web)"
echo "============================================"
echo ""

# Verificar se estamos no diretório correto
if [ ! -d "ouds-frontend" ]; then
    echo "❌ Erro: Diretório ouds-frontend não encontrado!"
    echo "💡 Execute este script a partir do diretório raiz do OUDS"
    exit 1
fi

# Entrar no diretório do frontend
cd ouds-frontend

# Verificar se o Node.js está instalado
if ! command -v node &> /dev/null; then
    echo "❌ Erro: Node.js não está instalado!"
    echo "💡 Instale o Node.js: https://nodejs.org/"
    exit 1
fi

# Verificar se o npm está instalado
if ! command -v npm &> /dev/null; then
    echo "❌ Erro: npm não está instalado!"
    echo "💡 npm geralmente vem com o Node.js"
    exit 1
fi

# Verificar se as dependências estão instaladas
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependências do frontend..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Erro na instalação das dependências!"
        echo "💡 Tente: npm install --force"
        exit 1
    fi
fi

# Verificar arquivo .env
if [ ! -f ".env" ]; then
    echo "⚠️ Arquivo .env não encontrado. Criando a partir do exemplo..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📝 Arquivo .env criado com configurações padrão"
    else
        echo "⚠️ Arquivo .env.example não encontrado. Usando configurações padrão."
    fi
fi

# Ler configurações do .env se existir
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Configurar porta padrão se não estiver definida
if [ -z "$OUDS_FRONTEND_PORT" ]; then
    export OUDS_FRONTEND_PORT=5173
fi

if [ -z "$OUDS_FRONTEND_HOST" ]; then
    export OUDS_FRONTEND_HOST=localhost
fi

if [ -z "$OUDS_API_URL" ]; then
    export OUDS_API_URL=http://localhost:8000
fi

echo "🌐 Iniciando servidor de desenvolvimento na porta $OUDS_FRONTEND_PORT..."
echo "🎯 Interface Web: http://$OUDS_FRONTEND_HOST:$OUDS_FRONTEND_PORT"
echo "🔗 API Backend: $OUDS_API_URL"
echo ""
echo "⏹️ Para parar o servidor, pressione Ctrl+C"
echo ""

# Verificar se o backend está rodando
echo "🔍 Verificando conexão com o backend..."
if curl -s --max-time 3 "$OUDS_API_URL" > /dev/null 2>&1; then
    echo "✅ Backend está rodando em $OUDS_API_URL"
else
    echo "⚠️ Backend não está respondendo em $OUDS_API_URL"
    echo "💡 Certifique-se de que o backend está rodando:"
    echo "   ./start_backend.sh"
fi
echo ""

# Iniciar o servidor de desenvolvimento
npm run dev --host


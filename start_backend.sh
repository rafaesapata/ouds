#!/bin/bash

# OUDS - Script de Inicialização do Backend
# =========================================

echo "🚀 OUDS - Iniciando Backend (API)"
echo "================================="
echo ""

# Verificar se estamos no diretório correto
if [ ! -d "OpenManus" ]; then
    echo "❌ Erro: Diretório OpenManus não encontrado!"
    echo "💡 Execute este script a partir do diretório raiz do OUDS"
    exit 1
fi

# Entrar no diretório do backend
cd OpenManus

# Verificar se o arquivo da API existe
if [ ! -f "api_server.py" ]; then
    echo "❌ Erro: Arquivo api_server.py não encontrado!"
    echo "💡 Verifique se a instalação foi concluída corretamente"
    exit 1
fi

# Verificar se as dependências estão instaladas
echo "🔍 Verificando dependências..."
if ! python3.11 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "⚠️ Dependências não encontradas. Executando instalação..."
    if [ -f "../install_ouds.sh" ]; then
        cd ..
        ./install_ouds.sh
        cd OpenManus
    else
        echo "❌ Script de instalação não encontrado!"
        echo "💡 Execute: pip3.11 install fastapi uvicorn openai"
        exit 1
    fi
fi

# Verificar arquivo .env
if [ ! -f ".env" ]; then
    echo "⚠️ Arquivo .env não encontrado. Criando a partir do exemplo..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📝 Arquivo .env criado. Configure sua OPENAI_API_KEY!"
    else
        echo "❌ Arquivo .env.example não encontrado!"
    fi
fi

# Verificar se OPENAI_API_KEY está configurada
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo "⚠️ IMPORTANTE: Configure sua OPENAI_API_KEY no arquivo .env"
    echo "📝 Edite o arquivo: nano .env"
    echo "🔑 Adicione: OPENAI_API_KEY=sk-sua_chave_aqui"
    echo ""
fi

# Configurar PYTHONPATH
export PYTHONPATH=$(pwd)

# Ler configurações do .env se existir
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Configurar porta padrão se não estiver definida
if [ -z "$OUDS_API_PORT" ]; then
    export OUDS_API_PORT=8000
fi

if [ -z "$OUDS_API_HOST" ]; then
    export OUDS_API_HOST=0.0.0.0
fi

echo "🌐 Iniciando servidor na porta $OUDS_API_PORT..."
echo "📡 Acesse a API em: http://localhost:$OUDS_API_PORT"
echo "📚 Documentação em: http://localhost:$OUDS_API_PORT/docs"
echo ""
echo "⏹️ Para parar o servidor, pressione Ctrl+C"
echo ""

# Iniciar o servidor
python3.11 api_server.py


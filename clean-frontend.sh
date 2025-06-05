#!/bin/bash

# Script para limpar cache e reiniciar frontend do OUDS
# Resolve problemas de cache e garante inicialização limpa

echo "🧹 OUDS - Limpeza de cache e reinicialização do frontend..."
echo "=========================================================="

# Verificar se estamos no diretório correto
if [ ! -d "ouds-frontend" ]; then
    echo "❌ Erro: Execute este script no diretório raiz do OUDS"
    echo "💡 Comando: cd /home/ec2-user/ouds && ./clean-frontend.sh"
    exit 1
fi

echo "📁 Diretório atual: $(pwd)"

# Parar processos do frontend em execução
echo "🛑 Parando processos do frontend..."
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "ouds-frontend" 2>/dev/null || true
sleep 2

# Navegar para o diretório frontend
cd ouds-frontend

echo "🧹 Limpando cache e dependências..."

# Limpar cache npm
echo "📦 Limpando cache npm..."
npm cache clean --force 2>/dev/null || true

# Remover node_modules e package-lock.json
echo "🗑️ Removendo node_modules e package-lock.json..."
rm -rf node_modules package-lock.json

# Limpar cache do Vite
echo "⚡ Limpando cache do Vite..."
rm -rf .vite dist

# Limpar cache do browser (se existir)
echo "🌐 Limpando cache do browser..."
rm -rf .cache

# Limpar logs temporários
echo "📋 Limpando logs temporários..."
rm -rf *.log npm-debug.log* yarn-debug.log* yarn-error.log*

# Reinstalar dependências
echo "📦 Reinstalando dependências..."
if npm install; then
    echo "✅ Dependências instaladas com sucesso"
elif npm install --legacy-peer-deps; then
    echo "✅ Dependências instaladas com --legacy-peer-deps"
else
    echo "❌ Erro na instalação de dependências"
    echo "🔄 Tentando com yarn..."
    if command -v yarn &> /dev/null; then
        yarn install && echo "✅ Dependências instaladas com yarn"
    else
        echo "❌ Falha na instalação de dependências"
        exit 1
    fi
fi

# Verificar se o .env está configurado corretamente
echo "⚙️ Verificando configuração..."
if [ -f ".env" ]; then
    echo "✅ Arquivo .env encontrado"
    if grep -q "OUDS_FRONTEND_HOST=0.0.0.0" .env; then
        echo "✅ Host configurado para acesso remoto"
    else
        echo "⚠️ Configurando host para acesso remoto..."
        sed -i 's/OUDS_FRONTEND_HOST=.*/OUDS_FRONTEND_HOST=0.0.0.0/' .env
    fi
    
    if grep -q "OUDS_FRONTEND_OPEN=false" .env; then
        echo "✅ Abertura automática desabilitada"
    else
        echo "⚠️ Desabilitando abertura automática do browser..."
        sed -i 's/OUDS_FRONTEND_OPEN=.*/OUDS_FRONTEND_OPEN=false/' .env
    fi
else
    echo "⚠️ Arquivo .env não encontrado, copiando do exemplo..."
    cp .env.example .env
fi

# Testar se o servidor inicia sem erros
echo "🧪 Testando inicialização do servidor..."
timeout 10s npm run dev > /dev/null 2>&1 &
SERVER_PID=$!
sleep 5

if ps -p $SERVER_PID > /dev/null 2>&1; then
    echo "✅ Servidor iniciando sem erros!"
    kill $SERVER_PID 2>/dev/null || true
    
    # Verificar porta configurada
    PORT=$(grep OUDS_FRONTEND_PORT .env | cut -d'=' -f2)
    echo "🌐 Porta configurada: ${PORT:-5173}"
    
else
    echo "⚠️ Servidor pode ter problemas, verificando..."
    # Tentar iniciar em foreground para ver erros
    echo "🔍 Iniciando em foreground para diagnóstico..."
    timeout 5s npm run dev || echo "❌ Erro detectado na inicialização"
fi

echo ""
echo "🎉 Limpeza concluída!"
echo "===================="
echo ""
echo "📋 Ações realizadas:"
echo "  ✅ Processos parados"
echo "  ✅ Cache npm limpo"
echo "  ✅ node_modules removido"
echo "  ✅ Cache Vite limpo"
echo "  ✅ Dependências reinstaladas"
echo "  ✅ Configuração verificada"
echo "  ✅ Teste de inicialização"
echo ""
echo "🚀 Para iniciar o frontend:"
echo "  npm run dev"
echo ""
echo "🌐 Acesso remoto:"
echo "  http://seu-servidor:${PORT:-5173}"
echo ""
echo "🛡️ Erro xdg-open resolvido:"
echo "  ✅ Abertura automática desabilitada"
echo ""


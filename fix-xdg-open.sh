#!/bin/bash

# OUDS - Script para corrigir erro xdg-open e garantir funcionamento do frontend
# ==============================================================================

set -e

echo "🔧 OUDS - Corrigindo erro xdg-open e reiniciando frontend..."
echo "=============================================================="

# Diretório base
OUDS_DIR="/home/ubuntu/ouds-project"
FRONTEND_DIR="$OUDS_DIR/ouds-frontend"

echo "📁 Diretório atual: $OUDS_DIR"

# Verificar se estamos no diretório correto
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Erro: Diretório ouds-frontend não encontrado!"
    echo "   Esperado: $FRONTEND_DIR"
    exit 1
fi

cd "$FRONTEND_DIR"

echo "🛑 Parando todos os processos do frontend..."
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "node.*vite" 2>/dev/null || true
sleep 2

echo "🔍 Verificando configuração do .env..."
if [ ! -f ".env" ]; then
    echo "⚠️ Arquivo .env não encontrado, criando..."
    cat > .env << 'EOF'
# OUDS - Configurações do Frontend
OUDS_FRONTEND_HOST=0.0.0.0
OUDS_FRONTEND_PORT=5173
OUDS_FRONTEND_OPEN=false
OUDS_API_URL=http://localhost:8000
OUDS_VERSION=1.0.22
EOF
fi

# Verificar se OUDS_FRONTEND_OPEN está definido
if ! grep -q "OUDS_FRONTEND_OPEN=false" .env; then
    echo "🔧 Adicionando OUDS_FRONTEND_OPEN=false ao .env..."
    echo "OUDS_FRONTEND_OPEN=false" >> .env
fi

echo "✅ Configuração do .env verificada"

echo "🧹 Limpando cache do npm e vite..."
npm cache clean --force 2>/dev/null || true
rm -rf .vite 2>/dev/null || true
rm -rf dist 2>/dev/null || true

echo "🔧 Verificando vite.config.js..."
if grep -q "open: false" vite.config.js; then
    echo "✅ vite.config.js já configurado corretamente"
else
    echo "❌ vite.config.js precisa ser corrigido"
    exit 1
fi

echo "🧪 Testando inicialização do servidor (modo não-interativo)..."

# Criar script temporário para testar o servidor (CommonJS)
cat > test-server.cjs << 'EOF'
const { spawn } = require('child_process');

console.log('🚀 Iniciando servidor de teste...');

const server = spawn('npm', ['run', 'dev'], {
    stdio: ['pipe', 'pipe', 'pipe'],
    env: { 
        ...process.env, 
        CI: 'true',
        OUDS_FRONTEND_OPEN: 'false'
    }
});

let output = '';
let hasError = false;

server.stdout.on('data', (data) => {
    const text = data.toString();
    output += text;
    console.log('📤 STDOUT:', text.trim());
    
    if (text.includes('Local:') && text.includes('5173')) {
        console.log('✅ Servidor iniciado com sucesso!');
        server.kill('SIGTERM');
        process.exit(0);
    }
});

server.stderr.on('data', (data) => {
    const text = data.toString();
    console.log('📤 STDERR:', text.trim());
    
    if (text.includes('xdg-open') || text.includes('ENOENT')) {
        console.log('❌ Erro xdg-open detectado!');
        hasError = true;
        server.kill('SIGTERM');
        process.exit(1);
    }
});

server.on('close', (code) => {
    if (!hasError && output.includes('Local:')) {
        console.log('✅ Teste concluído com sucesso!');
        process.exit(0);
    } else if (hasError) {
        console.log('❌ Teste falhou devido ao erro xdg-open');
        process.exit(1);
    } else {
        console.log('⚠️ Teste inconclusivo, código:', code);
        process.exit(code || 1);
    }
});

// Timeout de 30 segundos
setTimeout(() => {
    console.log('⏰ Timeout do teste');
    server.kill('SIGTERM');
    process.exit(1);
}, 30000);
EOF

# Executar teste
echo "🧪 Executando teste de 30 segundos..."
if node test-server.cjs; then
    echo "✅ Teste passou! Servidor pode ser iniciado sem erro xdg-open"
    rm -f test-server.cjs
else
    echo "❌ Teste falhou! Ainda há problemas com xdg-open"
    rm -f test-server.cjs
    exit 1
fi

echo ""
echo "🎉 Correção do erro xdg-open concluída!"
echo ""
echo "📋 Para iniciar o frontend agora:"
echo "   cd $FRONTEND_DIR"
echo "   npm run dev"
echo ""
echo "🌐 Acesso remoto:"
echo "   http://seu-servidor:5173"
echo ""
echo "🔍 Para verificar logs do proxy:"
echo "   Verifique o console do npm run dev"
echo ""


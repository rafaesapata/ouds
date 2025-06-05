#!/bin/bash

# Script para corrigir erros de importação @/lib/utils no OUDS
# Resolve: Failed to resolve import "@/lib/utils"

echo "🔧 OUDS - Corrigindo erros de importação @/lib/utils..."
echo "======================================================="

# Verificar se estamos no diretório correto
if [ ! -d "ouds-frontend" ]; then
    echo "❌ Erro: Execute este script no diretório raiz do OUDS"
    echo "💡 Comando: cd /home/ec2-user/ouds && ./fix-utils-import.sh"
    exit 1
fi

# Navegar para o frontend
cd ouds-frontend

echo "📁 Diretório atual: $(pwd)"

# Parar servidores em execução
echo "🛑 Parando servidores em execução..."
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 2

# Verificar se o diretório lib existe
if [ ! -d "src/lib" ]; then
    echo "📁 Criando diretório src/lib..."
    mkdir -p src/lib
fi

# Navegar para o diretório lib
cd src/lib

echo "📂 Verificando arquivos em src/lib..."

# Verificar se utils.js existe e renomear para utils.ts
if [ -f "utils.js" ]; then
    echo "🔄 Renomeando utils.js para utils.ts..."
    mv utils.js utils.ts
    echo "✅ utils.js → utils.ts"
else
    echo "ℹ️  utils.js não encontrado, verificando utils.ts..."
fi

# Criar utils.ts se não existir
if [ ! -f "utils.ts" ]; then
    echo "📝 Criando arquivo utils.ts..."
    cat > utils.ts << 'EOF'
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
EOF
    echo "✅ utils.ts criado"
else
    echo "✅ utils.ts já existe"
fi

# Criar index.ts para facilitar importações
echo "📝 Criando index.ts..."
echo "export * from './utils';" > index.ts
echo "✅ index.ts criado"

# Voltar para o diretório frontend
cd ../..

# Verificar e corrigir vite.config.js
echo "🔧 Verificando vite.config.js..."
if ! grep -q "extensions:" vite.config.js; then
    echo "🔄 Adicionando configuração de extensões no vite.config.js..."
    
    # Backup do arquivo original
    cp vite.config.js vite.config.js.backup
    
    # Adicionar configuração de extensões
    sed -i '/alias: {/a\      },\n      extensions: ['"'"'.js'"'"', '"'"'.jsx'"'"', '"'"'.ts'"'"', '"'"'.tsx'"'"', '"'"'.json'"'"']' vite.config.js
    
    echo "✅ vite.config.js atualizado"
else
    echo "✅ vite.config.js já configurado"
fi

# Limpar cache e dependências
echo "🧹 Limpando cache e dependências..."
rm -rf node_modules package-lock.json .vite
npm cache clean --force 2>/dev/null || true

# Reinstalar dependências
echo "📦 Reinstalando dependências..."
if npm install; then
    echo "✅ Dependências instaladas com sucesso"
else
    echo "⚠️  Erro na instalação, tentando com --legacy-peer-deps..."
    if npm install --legacy-peer-deps; then
        echo "✅ Dependências instaladas com --legacy-peer-deps"
    else
        echo "❌ Erro na instalação de dependências"
        exit 1
    fi
fi

# Testar se o servidor inicia
echo "🧪 Testando servidor de desenvolvimento..."
timeout 10s npm run dev > /dev/null 2>&1 &
SERVER_PID=$!
sleep 5

if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Servidor iniciando sem erros!"
    kill $SERVER_PID 2>/dev/null || true
else
    echo "⚠️  Servidor pode ter problemas, verifique manualmente"
fi

echo ""
echo "🎉 Correção concluída!"
echo "====================="
echo ""
echo "📋 Arquivos corrigidos:"
echo "  ✅ src/lib/utils.ts (função cn disponível)"
echo "  ✅ src/lib/index.ts (re-exportação)"
echo "  ✅ vite.config.js (extensões configuradas)"
echo ""
echo "🚀 Para iniciar o frontend:"
echo "  cd ouds-frontend"
echo "  npm run dev"
echo ""
echo "🌐 URL esperada: http://localhost:5173"
echo ""


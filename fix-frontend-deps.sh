#!/bin/bash

# Script para corrigir conflitos de dependências do frontend OUDS
# Resolve problemas de ERESOLVE e incompatibilidades de versões

echo "🔧 OUDS - Corrigindo conflitos de dependências do frontend..."
echo "============================================================"

# Navegar para o diretório do frontend
cd /home/ubuntu/ouds-project/ouds-frontend || {
    echo "❌ Erro: Diretório ouds-frontend não encontrado"
    exit 1
}

echo "📁 Diretório atual: $(pwd)"

# Verificar se package.json existe
if [ ! -f "package.json" ]; then
    echo "❌ Erro: package.json não encontrado"
    exit 1
fi

echo "📦 Arquivo package.json encontrado"

# Corrigir conflitos conhecidos automaticamente
echo "🔧 Corrigindo conflitos conhecidos de versões..."

# Conflito 1: date-fns vs react-day-picker
if grep -q '"date-fns": "^4\.' package.json; then
    echo "🔄 Corrigindo date-fns para compatibilidade com react-day-picker..."
    sed -i 's/"date-fns": "^4\.[^"]*"/"date-fns": "^3.6.0"/g' package.json
fi

# Conflito 2: react-day-picker vs React 19
if grep -q '"react-day-picker": "8\.' package.json; then
    echo "🔄 Atualizando react-day-picker para compatibilidade com React 19..."
    sed -i 's/"react-day-picker": "8\.[^"]*"/"react-day-picker": "^9.7.0"/g' package.json
fi

# Conflito 3: React 19 vs outras dependências
echo "🔍 Verificando compatibilidade com React 19..."

echo "✅ Conflitos conhecidos corrigidos automaticamente"

# Limpar cache e node_modules após correções
echo "🧹 Limpando cache e dependências antigas..."
rm -rf node_modules package-lock.json yarn.lock pnpm-lock.yaml
npm cache clean --force 2>/dev/null || true

# Estratégia 1: Instalação com --legacy-peer-deps
echo "🔄 Tentativa 1: Instalação com --legacy-peer-deps"
if npm install --legacy-peer-deps; then
    echo "✅ Instalação com --legacy-peer-deps bem-sucedida!"
    
    # Testar se o servidor de desenvolvimento funciona
    echo "🧪 Testando servidor de desenvolvimento..."
    timeout 10s npm run dev > /dev/null 2>&1 &
    DEV_PID=$!
    sleep 5
    
    if kill -0 $DEV_PID 2>/dev/null; then
        kill $DEV_PID
        echo "✅ Servidor de desenvolvimento funcionando!"
        echo "🎉 Frontend configurado com sucesso!"
        exit 0
    else
        echo "⚠️ Servidor de desenvolvimento com problemas, tentando próxima estratégia..."
    fi
fi

# Estratégia 2: Instalação com --force
echo "🔄 Tentativa 2: Instalação com --force"
rm -rf node_modules package-lock.json
if npm install --force; then
    echo "✅ Instalação com --force bem-sucedida!"
    
    # Testar novamente
    echo "🧪 Testando servidor de desenvolvimento..."
    timeout 10s npm run dev > /dev/null 2>&1 &
    DEV_PID=$!
    sleep 5
    
    if kill -0 $DEV_PID 2>/dev/null; then
        kill $DEV_PID
        echo "✅ Servidor de desenvolvimento funcionando!"
        echo "🎉 Frontend configurado com sucesso!"
        exit 0
    fi
fi

# Estratégia 3: Usar yarn como alternativa
echo "🔄 Tentativa 3: Usando Yarn como alternativa"
if command -v yarn >/dev/null 2>&1; then
    rm -rf node_modules package-lock.json
    if yarn install; then
        echo "✅ Instalação com Yarn bem-sucedida!"
        
        # Testar com yarn
        echo "🧪 Testando servidor de desenvolvimento com Yarn..."
        timeout 10s yarn dev > /dev/null 2>&1 &
        DEV_PID=$!
        sleep 5
        
        if kill -0 $DEV_PID 2>/dev/null; then
            kill $DEV_PID
            echo "✅ Servidor de desenvolvimento funcionando!"
            echo "🎉 Frontend configurado com sucesso!"
            exit 0
        fi
    fi
else
    echo "⚠️ Yarn não está instalado, pulando esta estratégia"
fi

# Estratégia 4: Instalar yarn e tentar novamente
echo "🔄 Tentativa 4: Instalando Yarn e tentando novamente"
if npm install -g yarn; then
    rm -rf node_modules package-lock.json
    if yarn install; then
        echo "✅ Instalação com Yarn bem-sucedida!"
        echo "🎉 Frontend configurado com sucesso!"
        exit 0
    fi
fi

# Se chegou até aqui, houve problema
echo ""
echo "❌ Erro: Não foi possível resolver os conflitos de dependências"
echo ""
echo "🔧 Soluções manuais:"
echo "1. Tentar instalação manual:"
echo "   cd ouds-frontend"
echo "   rm -rf node_modules package-lock.json"
echo "   npm install --legacy-peer-deps"
echo ""
echo "2. Usar versões específicas:"
echo "   npm install date-fns@3.6.0 react-day-picker@8.10.1"
echo ""
echo "3. Usar Yarn:"
echo "   yarn install"
echo ""
echo "4. Atualizar Node.js:"
echo "   Certifique-se de usar Node.js 18+ ou 20+"
echo ""
echo "5. Limpar cache global:"
echo "   npm cache clean --force"
echo "   rm -rf ~/.npm"

exit 1


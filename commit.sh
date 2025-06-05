#!/bin/bash

# Script para commit com incremento automático de versão
# Uso: ./commit.sh "mensagem do commit"

if [ -z "$1" ]; then
    echo "❌ Erro: Forneça uma mensagem de commit"
    echo "Uso: ./commit.sh \"sua mensagem de commit\""
    exit 1
fi

echo "🔄 Incrementando versão..."

# Verificar se Node.js está disponível
if ! command -v node &> /dev/null; then
    echo "⚠️ Node.js não encontrado. Incrementando versão manualmente..."
    
    # Ler versão atual do package.json
    CURRENT_VERSION=$(grep '"version"' package.json | sed 's/.*"version": "\(.*\)".*/\1/')
    
    # Incrementar patch version (assumindo formato x.y.z)
    IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
    MAJOR=${VERSION_PARTS[0]}
    MINOR=${VERSION_PARTS[1]}
    PATCH=${VERSION_PARTS[2]}
    
    NEW_PATCH=$((PATCH + 1))
    NEW_VERSION="$MAJOR.$MINOR.$NEW_PATCH"
    
    # Atualizar package.json
    sed -i "s/\"version\": \"$CURRENT_VERSION\"/\"version\": \"$NEW_VERSION\"/" package.json
    
    echo "✅ Versão atualizada de $CURRENT_VERSION para $NEW_VERSION"
else
    # Usar npm para incrementar versão
    npm run version:patch
fi

echo "📝 Adicionando arquivos ao Git..."
git add .

echo "💾 Fazendo commit..."
git commit -m "$1

🔖 Versão: $(grep '"version"' package.json | sed 's/.*"version": "\(.*\)".*/\1/')"

echo "🎉 Commit realizado com sucesso!"
echo "📤 Para enviar para o repositório, execute: git push"


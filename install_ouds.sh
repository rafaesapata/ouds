#!/bin/bash

# OUDS - Oráculo UDS
# Script de instalação automática
# Versão: 1.0.0

set -e

echo "🚀 OUDS - Oráculo UDS - Instalação Automática"
echo "=============================================="
echo ""

# Verificar pré-requisitos
echo "📋 Verificando pré-requisitos..."

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION encontrado"

# Verificar Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js não encontrado. Por favor, instale Node.js 20+"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✅ Node.js $NODE_VERSION encontrado"

# Verificar npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm não encontrado. Por favor, instale npm"
    exit 1
fi

NPM_VERSION=$(npm --version)
echo "✅ npm $NPM_VERSION encontrado"

echo ""

# Configurar Backend
echo "🔧 Configurando Backend (API OUDS)..."
cd OpenManus

echo "📦 Instalando dependências Python..."

# Detectar arquitetura
ARCH=$(uname -m)
echo "🔍 Arquitetura detectada: $ARCH"

# Escolher arquivo de dependências baseado na arquitetura
if [[ "$ARCH" == "arm64" || "$ARCH" == "aarch64" ]]; then
    REQUIREMENTS_FILE="requirements-arm64.txt"
    echo "📱 Usando dependências otimizadas para ARM64..."
else
    REQUIREMENTS_FILE="requirements.txt"
    echo "💻 Usando dependências padrão para x86_64..."
fi

echo "Tentando instalação completa primeiro..."
if pip3 install -r $REQUIREMENTS_FILE; then
    echo "✅ Dependências completas instaladas com sucesso!"
else
    echo "⚠️ Erro na instalação completa. Tentando instalação mínima..."
    if pip3 install -r requirements-minimal.txt; then
        echo "✅ Dependências mínimas instaladas com sucesso!"
        echo "ℹ️ Algumas funcionalidades avançadas podem não estar disponíveis."
    else
        echo "⚠️ Erro na instalação mínima. Tentando instalação segura..."
        if ./install-safe.sh; then
            echo "✅ Dependências instaladas com método seguro!"
            echo "ℹ️ Resolvidos conflitos com pacotes do sistema."
        else
            echo "⚠️ Erro na instalação segura. Tentando instalação ultra-mínima..."
            if pip3 install -r requirements-core.txt; then
                echo "✅ Dependências ultra-mínimas instaladas com sucesso!"
                echo "⚠️ Apenas funcionalidades básicas estarão disponíveis."
            else
                echo "❌ Erro na instalação das dependências."
                echo "💡 Possíveis soluções:"
                echo "   1. Execute: ./install-safe.sh"
                echo "   2. Instale manualmente: pip3 install --user fastapi uvicorn openai"
                echo "   3. Use ambiente virtual: python3 -m venv venv && source venv/bin/activate"
                exit 1
            fi
        fi
    fi
fi

echo "⚙️ Configurando variáveis de ambiente..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Arquivo .env criado a partir do .env.example"
    echo "⚠️ IMPORTANTE: Configure sua OPENAI_API_KEY no arquivo OpenManus/.env!"
else
    echo "📝 Arquivo .env já existe. Mantendo configurações atuais."
fi

cd ..

# Configurar Frontend
echo ""
echo "🎨 Configurando Frontend (React)..."
cd ouds-frontend

echo "📦 Instalando dependências Node.js..."
npm install

cd ..

# Criar scripts de execução
echo ""
echo "📜 Criando scripts de execução..."

# Script para iniciar backend
cat > start_backend.sh << 'EOF'
#!/bin/bash
echo "🚀 Iniciando OUDS Backend..."
cd OpenManus
export PYTHONPATH=$(pwd)
python3 api_server.py
EOF

chmod +x start_backend.sh

# Script para iniciar frontend
cat > start_frontend.sh << 'EOF'
#!/bin/bash
echo "🎨 Iniciando OUDS Frontend..."
cd ouds-frontend
npm run dev --host
EOF

chmod +x start_frontend.sh

# Script para iniciar ambos
cat > start_ouds.sh << 'EOF'
#!/bin/bash
echo "🚀 Iniciando OUDS completo..."
echo "Backend será iniciado em background..."

# Iniciar backend em background
cd OpenManus
export PYTHONPATH=$(pwd)
python3 api_server.py &
BACKEND_PID=$!

# Aguardar backend inicializar
echo "⏳ Aguardando backend inicializar..."
sleep 5

# Verificar se backend está rodando
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ Backend iniciado com sucesso!"
else
    echo "❌ Erro ao iniciar backend"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

cd ..

# Iniciar frontend
echo "🎨 Iniciando frontend..."
cd ouds-frontend
npm run dev --host

# Cleanup ao sair
trap "echo '🛑 Parando OUDS...'; kill $BACKEND_PID 2>/dev/null; exit" INT TERM
EOF

chmod +x start_ouds.sh

# Criar arquivo de configuração
cat > ouds_config.json << EOF
{
  "name": "OUDS - Oráculo UDS",
  "version": "1.0.15",
  "description": "Sistema de IA conversacional OUDS - Oráculo UDS",
  "backend": {
    "port": 8000,
    "host": "localhost",
    "api_base": "http://localhost:8000"
  },
  "frontend": {
    "port": 5173,
    "host": "localhost",
    "url": "http://localhost:5173"
  },
  "installation_date": "$(date -I)",
  "status": "installed"
}
EOF

echo ""
echo "✅ Instalação concluída com sucesso!"
echo ""
echo "📋 Próximos passos:"
echo "1. Configure sua OPENAI_API_KEY no arquivo OpenManus/.env"
echo "2. Execute um dos scripts:"
echo "   • ./start_ouds.sh      - Inicia backend e frontend juntos"
echo "   • ./start_backend.sh   - Inicia apenas o backend"
echo "   • ./start_frontend.sh  - Inicia apenas o frontend"
echo ""
echo "🌐 URLs de acesso:"
echo "   • Frontend: http://localhost:5173"
echo "   • API Backend: http://localhost:8000"
echo ""
echo "📚 Documentação completa: OUDS_README.md"
echo ""
echo "🎉 OUDS está pronto para uso!"


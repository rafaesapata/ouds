#!/bin/bash

# Script de instalação específico para Amazon EC2
# Resolve problemas comuns de dependências em ambientes EC2

echo "🚀 OUDS - Instalação para Amazon EC2"
echo "===================================="

# Detectar sistema operacional
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    echo "❌ Não foi possível detectar o sistema operacional"
    exit 1
fi

echo "🔍 Sistema detectado: $OS $VER"

# Função para testar se um módulo Python está disponível
test_python_module() {
    python3 -c "import $1; print('✅ $1 disponível')" 2>/dev/null
}

# Função para instalar via pip com múltiplas estratégias
install_pip_package() {
    local package=$1
    echo "📦 Instalando $package..."
    
    # Estratégia 1: pip normal
    if pip3 install "$package"; then
        echo "✅ $package instalado com sucesso"
        return 0
    fi
    
    # Estratégia 2: pip com --user
    echo "🔄 Tentando com --user..."
    if pip3 install --user "$package"; then
        echo "✅ $package instalado com --user"
        return 0
    fi
    
    # Estratégia 3: pip com --break-system-packages (Python 3.11+)
    echo "🔄 Tentando com --break-system-packages..."
    if pip3 install --break-system-packages "$package"; then
        echo "✅ $package instalado com --break-system-packages"
        return 0
    fi
    
    echo "❌ Falha ao instalar $package"
    return 1
}

# Atualizar sistema
echo "🔄 Atualizando sistema..."
if command -v yum >/dev/null 2>&1; then
    sudo yum update -y
    sudo yum install -y python3-pip python3-devel gcc
elif command -v apt >/dev/null 2>&1; then
    sudo apt update
    sudo apt install -y python3-pip python3-dev build-essential
fi

# Atualizar pip
echo "🔄 Atualizando pip..."
python3 -m pip install --upgrade pip --user

# Lista de dependências essenciais
ESSENTIAL_PACKAGES=(
    "fastapi>=0.100.0"
    "uvicorn>=0.20.0"
    "pydantic>=2.0.0"
    "openai>=1.0.0"
    "httpx>=0.24.0"
    "requests>=2.28.0"
    "aiofiles>=0.8.0"
)

# Lista de dependências adicionais
ADDITIONAL_PACKAGES=(
    "docker>=6.0.0"
    "boto3>=1.30.0"
    "tenacity>=8.0.0"
    "loguru>=0.6.0"
    "pyyaml>=6.0"
    "tomli>=2.0.0"
    "tiktoken>=0.5.0"
)

# Instalar dependências essenciais
echo "📦 Instalando dependências essenciais..."
for package in "${ESSENTIAL_PACKAGES[@]}"; do
    if ! install_pip_package "$package"; then
        echo "⚠️ Falha ao instalar $package (essencial)"
    fi
done

# Instalar dependências adicionais
echo "📦 Instalando dependências adicionais..."
for package in "${ADDITIONAL_PACKAGES[@]}"; do
    if ! install_pip_package "$package"; then
        echo "⚠️ Falha ao instalar $package (opcional)"
    fi
done

# Verificar instalação
echo ""
echo "🔍 Verificando instalação..."
FAILED_MODULES=()

for module in fastapi uvicorn pydantic openai httpx requests aiofiles; do
    if test_python_module "$module"; then
        continue
    else
        echo "❌ $module não disponível"
        FAILED_MODULES+=("$module")
    fi
done

# Configurar PATH se necessário
echo "🔧 Configurando PATH..."
if [ -d "$HOME/.local/bin" ]; then
    if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        export PATH="$HOME/.local/bin:$PATH"
        echo "✅ PATH atualizado"
    fi
fi

# Resultado final
echo ""
echo "📊 Resultado da instalação:"
if [ ${#FAILED_MODULES[@]} -eq 0 ]; then
    echo "🎉 Todas as dependências essenciais instaladas com sucesso!"
    echo ""
    echo "🚀 Para iniciar o OUDS:"
    echo "   ./start_ouds.sh"
    echo ""
    echo "🌐 URLs de acesso:"
    echo "   - Interface: http://localhost:5173"
    echo "   - API: http://localhost:8000"
    exit 0
else
    echo "⚠️ Algumas dependências falharam: ${FAILED_MODULES[*]}"
    echo ""
    echo "🔧 Soluções manuais:"
    echo "1. Tentar com ambiente virtual:"
    echo "   python3 -m venv ouds-env"
    echo "   source ouds-env/bin/activate"
    echo "   pip install fastapi uvicorn pydantic openai"
    echo ""
    echo "2. Instalar via gerenciador do sistema:"
    if command -v yum >/dev/null 2>&1; then
        echo "   sudo yum install python3-fastapi python3-uvicorn"
    elif command -v apt >/dev/null 2>&1; then
        echo "   sudo apt install python3-fastapi python3-uvicorn"
    fi
    echo ""
    echo "3. Verificar versão do Python:"
    echo "   python3 --version"
    echo "   (Recomendado: Python 3.8+)"
    exit 1
fi


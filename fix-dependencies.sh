#!/bin/bash

# OUDS - Correção Completa de Dependências
# ========================================

echo "🔧 OUDS - Correção Completa de Dependências"
echo "==========================================="
echo ""

# Detectar diretório do projeto
if [ ! -d "OpenManus" ]; then
    echo "❌ Erro: Diretório OpenManus não encontrado!"
    echo "💡 Execute este script a partir do diretório raiz do OUDS"
    exit 1
fi

cd OpenManus

# Criar arquivos de requirements se não existirem
echo "📝 Criando arquivos de requirements..."

# requirements-minimal.txt
cat > requirements-minimal.txt << 'EOF'
# OUDS - Dependências Mínimas
# ============================

# Core API
fastapi>=0.115.0
uvicorn>=0.34.0
pydantic>=2.10.0
pydantic-settings>=2.0.0

# OpenAI Integration
openai>=1.66.0
tiktoken>=0.9.0

# AWS Integration
boto3>=1.34.0
botocore>=1.34.0

# Utilities
aiofiles>=24.1.0
httpx>=0.27.0
requests>=2.32.0
tenacity>=9.0.0
pyyaml>=6.0.0
loguru>=0.7.0
colorama>=0.4.6

# Web scraping
beautifulsoup4>=4.12.0

# Data processing
pandas>=1.5.0

# HTTP streaming
httpx-sse>=0.3.0
sse-starlette>=1.0.0

# Docker support
docker>=6.0.0

# Browser automation
browser-use>=0.2.5
playwright>=1.40.0

# MCP Support
mcp>=1.9.0

# Search engines
duckduckgo-search>=6.0.0
googlesearch-python>=1.2.0
baidusearch>=1.0.0

# TOML support
tomli>=2.0.0
EOF

# requirements-core.txt
cat > requirements-core.txt << 'EOF'
# OUDS - Dependências Ultra-Mínimas
# ==================================

# Core API Framework
fastapi>=0.100.0
uvicorn>=0.20.0
pydantic>=2.0.0

# OpenAI Integration
openai>=1.0.0
tiktoken>=0.5.0

# AWS Integration
boto3>=1.30.0

# Utilities básicas
httpx>=0.24.0
requests>=2.28.0
aiofiles>=0.8.0
tenacity>=8.0.0
loguru>=0.6.0
pyyaml>=6.0
EOF

# requirements-safe.txt
cat > requirements-safe.txt << 'EOF'
# OUDS - Dependências com Resolução de Conflitos
# ==============================================

# Core API
fastapi>=0.100.0
uvicorn>=0.20.0
pydantic>=2.0.0

# OpenAI Integration
openai>=1.0.0
tiktoken>=0.5.0

# AWS Integration
boto3>=1.30.0
botocore>=1.30.0

# HTTP e Async
httpx>=0.24.0
aiofiles>=0.8.0

# Utilities (com resolução de conflitos RPM)
requests>=2.28.0
pyyaml>=6.0.0
loguru>=0.6.0
tenacity>=8.0.0

# MCP Support
httpx-sse>=0.3.0
sse-starlette>=1.0.0
pydantic-settings>=2.0.0
EOF

# requirements.txt (completo)
cat > requirements.txt << 'EOF'
# OUDS - Dependências Completas
# =============================

# Core API
fastapi~=0.115.11
uvicorn~=0.34.0
pydantic~=2.10.6
pydantic-settings~=2.0.0

# OpenAI Integration
openai~=1.66.3
tiktoken~=0.9.0

# AWS Integration
boto3~=1.34.0
botocore~=1.34.0

# Utilities
aiofiles~=24.1.0
httpx~=0.27.0
requests~=2.32.3
tenacity~=9.0.0
pyyaml~=6.0.2
loguru~=0.7.3
colorama~=0.4.6

# Web scraping e parsing
beautifulsoup4~=4.12.0
lxml~=5.0.0

# Data processing
pandas~=2.2.0
numpy~=1.26.0

# HTTP streaming
httpx-sse~=0.3.0
sse-starlette~=1.0.0

# MCP Support
mcp>=1.9.0

# Browser automation (opcional)
# browser-use>=0.2.5
# playwright>=1.40.0

# Search engines (opcional)
# duckduckgo-search>=6.0.0
# googlesearch-python>=1.2.0

# Docker support (opcional)
# docker>=7.0.0
EOF

echo "✅ Arquivos de requirements criados!"

# Função para instalar uv se não estiver disponível
install_uv() {
    if command -v uv >/dev/null 2>&1; then
        echo "✅ uv já está instalado"
        uv --version
        return 0
    fi
    
    echo "📦 Instalando uv (gerenciador de pacotes Python ultra-rápido)..."
    
    # Método 1: Via curl (recomendado)
    if curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1; then
        export PATH="$HOME/.cargo/bin:$PATH"
        if command -v uv >/dev/null 2>&1; then
            echo "✅ uv instalado com sucesso via curl"
            uv --version
            return 0
        fi
    fi
    
    # Método 2: Via pip
    if pip3 install uv >/dev/null 2>&1; then
        echo "✅ uv instalado com sucesso via pip"
        uv --version
        return 0
    fi
    
    # Método 3: Via pip --user
    if pip3 install --user uv >/dev/null 2>&1; then
        echo "✅ uv instalado com sucesso via pip --user"
        export PATH="$HOME/.local/bin:$PATH"
        uv --version
        return 0
    fi
    
    echo "⚠️ Não foi possível instalar uv, usando pip como fallback"
    return 1
}

# Função para instalar pacote com múltiplas estratégias (incluindo uv)
install_package() {
    local package=$1
    local name=$(echo $package | cut -d'>' -f1 | cut -d'=' -f1)
    
    echo "📦 Instalando $name..."
    
    # Estratégia 1: uv (mais rápido)
    if command -v uv >/dev/null 2>&1; then
        if uv pip install "$package" >/dev/null 2>&1; then
            echo "✅ $name instalado com sucesso (uv)"
            return 0
        fi
        
        # uv com --user
        if uv pip install --user "$package" >/dev/null 2>&1; then
            echo "✅ $name instalado com sucesso (uv --user)"
            return 0
        fi
    fi
    
    # Estratégia 2: Instalação normal com pip
    if pip3 install "$package" >/dev/null 2>&1; then
        echo "✅ $name instalado com sucesso (pip normal)"
        return 0
    fi
    
    # Estratégia 3: Instalação do usuário
    if pip3 install --user "$package" >/dev/null 2>&1; then
        echo "✅ $name instalado com sucesso (pip --user)"
        return 0
    fi
    
    # Estratégia 4: Force reinstall
    if pip3 install --user --force-reinstall "$package" >/dev/null 2>&1; then
        echo "✅ $name instalado com sucesso (pip --force-reinstall)"
        return 0
    fi
    
    # Estratégia 5: No deps
    if pip3 install --user --no-deps "$package" >/dev/null 2>&1; then
        echo "✅ $name instalado com sucesso (pip --no-deps)"
        return 0
    fi
    
    # Estratégia 6: uv com --break-system-packages (se disponível)
    if command -v uv >/dev/null 2>&1; then
        if uv pip install --break-system-packages "$package" >/dev/null 2>&1; then
            echo "✅ $name instalado com sucesso (uv --break-system-packages)"
            return 0
        fi
    fi
    
    echo "❌ Falha ao instalar $name"
    return 1
}

# Pacotes críticos em ordem de prioridade
critical_packages=(
    "fastapi>=0.100.0"
    "uvicorn>=0.20.0"
    "pydantic>=2.0.0"
    "openai>=1.0.0"
    "tiktoken>=0.5.0"
    "boto3>=1.30.0"
    "requests>=2.28.0"
    "httpx>=0.24.0"
    "aiofiles>=0.8.0"
    "tenacity>=8.0.0"
    "loguru>=0.6.0"
    "pyyaml>=6.0.0"
    "tomli>=2.0.0"
    "docker>=6.0.0"
    "beautifulsoup4>=4.12.0"
    "pandas>=1.5.0"
    "browser-use>=0.2.5"
    "mcp>=1.9.0"
    "duckduckgo-search>=6.0.0"
    "googlesearch-python>=1.2.0"
    "baidusearch>=1.0.0"
    "playwright>=1.40.0"
)

echo ""
echo "🚀 Instalando uv (gerenciador ultra-rápido)..."
echo "============================================="
install_uv

echo ""
echo "🚀 Instalando dependências críticas..."
echo "======================================"

failed_packages=()

for package in "${critical_packages[@]}"; do
    if ! install_package "$package"; then
        failed_packages+=("$package")
    fi
done

echo ""
echo "📊 Resultado da Instalação:"
echo "=========================="

if [ ${#failed_packages[@]} -eq 0 ]; then
    echo "🎉 Todas as dependências críticas foram instaladas com sucesso!"
else
    echo "⚠️ Alguns pacotes falharam:"
    for package in "${failed_packages[@]}"; do
        echo "   - $package"
    done
    echo ""
    echo "💡 Soluções para pacotes que falharam:"
    echo "   1. Usar ambiente virtual:"
    echo "      python3 -m venv venv"
    echo "      source venv/bin/activate"
    echo "      pip install <pacote>"
    echo ""
    echo "   2. Instalar via gerenciador do sistema:"
    echo "      sudo yum install python3-boto3 python3-requests python3-pyyaml"
    echo ""
fi

# Verificar instalação
echo ""
echo "🔍 Verificando instalação..."
echo "============================"

# Função para verificar módulo com nome correto
check_module() {
    local package_name=$1
    local module_name=$2
    
    if python3 -c "import $module_name" 2>/dev/null; then
        version=$(python3 -c "import $module_name; print(getattr($module_name, '__version__', 'N/A'))" 2>/dev/null)
        echo "✅ $package_name ($version)"
        return 0
    else
        echo "❌ $package_name (não instalado)"
        return 1
    fi
}

# Verificar pacotes com mapeamento correto de nomes
echo "Verificando módulos essenciais:"
check_module "fastapi" "fastapi"
check_module "uvicorn" "uvicorn"
check_module "pydantic" "pydantic"
check_module "openai" "openai"
check_module "tiktoken" "tiktoken"
check_module "boto3" "boto3"
check_module "requests" "requests"
check_module "tenacity" "tenacity"
check_module "docker" "docker"
check_module "beautifulsoup4" "bs4"
check_module "pandas" "pandas"
check_module "browser-use" "browser_use"
check_module "mcp" "mcp"
check_module "duckduckgo-search" "duckduckgo_search"
check_module "googlesearch-python" "googlesearch"
check_module "baidusearch" "baidusearch"
check_module "playwright" "playwright"
check_module "tomli" "tomli"

echo ""
echo "🎯 Próximos passos:"
echo "=================="
echo "1. Configure sua chave OpenAI:"
echo "   nano .env"
echo "   # Adicione: OPENAI_API_KEY=sk-sua_chave_aqui"
echo ""
echo "2. Teste o backend:"
echo "   cd .."
echo "   ./start_backend.sh"
echo ""
echo "3. Para instalações futuras, use uv (mais rápido):"
echo "   uv pip install <pacote>"
echo ""
echo "4. Se houver problemas, execute:"
echo "   ./diagnose.sh"
echo ""

cd ..
echo "✅ Correção completa finalizada!"


#!/bin/bash

# OUDS - Script de Diagnóstico de Dependências
# =============================================

echo "🔍 OUDS - Diagnóstico de Dependências"
echo "======================================"
echo ""

# Informações do sistema
echo "📋 Informações do Sistema:"
echo "- OS: $(uname -s)"
echo "- Arquitetura: $(uname -m)"
echo "- Kernel: $(uname -r)"
echo ""

# Informações do Python
echo "🐍 Informações do Python:"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "- Versão: $PYTHON_VERSION"
    echo "- Localização: $(which python3)"
    
    # Verificar pip
    if command -v pip3 &> /dev/null; then
        PIP_VERSION=$(pip3 --version)
        echo "- pip: $PIP_VERSION"
    else
        echo "- pip: ❌ Não encontrado"
    fi
else
    echo "- ❌ Python3 não encontrado"
fi
echo ""

# Testar dependências críticas
echo "🧪 Testando Dependências Críticas:"

critical_packages=("fastapi" "uvicorn" "pydantic" "openai" "tiktoken" "httpx" "requests" "aiofiles" "loguru" "pyyaml" "tenacity")

for package in "${critical_packages[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        version=$(python3 -c "import $package; print(getattr($package, '__version__', 'N/A'))" 2>/dev/null)
        echo "- ✅ $package ($version)"
    else
        echo "- ❌ $package (não instalado)"
    fi
done
echo ""

# Verificar conflitos com pacotes rpm
echo "🔍 Verificando Conflitos RPM:"
rpm_conflicts=("requests" "pyyaml" "urllib3" "certifi")

for package in "${rpm_conflicts[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        # Verificar se foi instalado via rpm
        if rpm -q python3-$package 2>/dev/null || rpm -q python-$package 2>/dev/null; then
            echo "- ⚠️ $package (instalado via RPM - possível conflito)"
        else
            version=$(python3 -c "import $package; print(getattr($package, '__version__', 'N/A'))" 2>/dev/null)
            echo "- ✅ $package ($version - via pip)"
        fi
    else
        echo "- ❌ $package (não instalado)"
    fi
done
echo ""

# Testar dependências opcionais
echo "🔧 Testando Dependências Opcionais:"

optional_packages=("mcp" "anthropic" "browser_use" "playwright")

for package in "${optional_packages[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        version=$(python3 -c "import $package; print(getattr($package, '__version__', 'N/A'))" 2>/dev/null)
        echo "- ✅ $package ($version)"
    else
        echo "- ⚠️ $package (não instalado - opcional)"
    fi
done
echo ""

# Verificar conectividade
echo "🌐 Testando Conectividade:"
if curl -s --max-time 5 https://pypi.org > /dev/null; then
    echo "- ✅ Conexão com PyPI"
else
    echo "- ❌ Problema de conexão com PyPI"
fi

if curl -s --max-time 5 https://api.openai.com > /dev/null; then
    echo "- ✅ Conexão com OpenAI API"
else
    echo "- ⚠️ Problema de conexão com OpenAI API"
fi
echo ""

# Verificar arquivos de dependências
echo "📄 Verificando Arquivos de Dependências:"
requirements_files=("requirements.txt" "requirements-minimal.txt" "requirements-core.txt" "requirements-arm64.txt")

for file in "${requirements_files[@]}"; do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        echo "- ✅ $file ($lines linhas)"
    else
        echo "- ❌ $file (não encontrado)"
    fi
done
echo ""

# Sugestões baseadas na arquitetura
echo "💡 Sugestões:"
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" || "$ARCH" == "aarch64" ]]; then
    echo "- Detectada arquitetura ARM64"
    echo "- Recomendado usar: pip3 install -r requirements-arm64.txt"
    echo "- Se houver problemas, tente: pip3 install -r requirements-core.txt"
else
    echo "- Detectada arquitetura x86_64"
    echo "- Recomendado usar: pip3 install -r requirements.txt"
    echo "- Se houver problemas, tente: pip3 install -r requirements-minimal.txt"
fi
echo ""

# Comando de instalação manual
echo "🛠️ Instalação Manual de Emergência:"
echo "pip3 install fastapi uvicorn pydantic openai tiktoken httpx requests aiofiles loguru pyyaml"
echo ""

echo "✅ Diagnóstico concluído!"
echo "📧 Se problemas persistirem, compartilhe este relatório com a equipe de suporte."


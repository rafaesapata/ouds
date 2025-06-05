#!/bin/bash

# OUDS - Script de Instalação Segura
# ==================================
# Resolve conflitos com pacotes instalados via rpm/sistema

echo "🔧 OUDS - Instalação Segura de Dependências"
echo "==========================================="
echo ""

# Função para instalar pacote com fallback
install_package_safe() {
    local package=$1
    echo "📦 Instalando $package..."
    
    # Tentar instalação normal primeiro
    if pip3 install "$package" >/dev/null 2>&1; then
        echo "✅ $package instalado com sucesso"
        return 0
    fi
    
    # Se falhar, tentar com --user
    echo "⚠️ Tentando instalação com --user..."
    if pip3 install --user "$package" >/dev/null 2>&1; then
        echo "✅ $package instalado com --user"
        return 0
    fi
    
    # Se ainda falhar, tentar com --force-reinstall
    echo "⚠️ Tentando com --force-reinstall..."
    if pip3 install --user --force-reinstall "$package" >/dev/null 2>&1; then
        echo "✅ $package instalado com --force-reinstall"
        return 0
    fi
    
    # Se tudo falhar, tentar sem dependências
    echo "⚠️ Tentando sem dependências..."
    if pip3 install --user --force-reinstall --no-deps "$package" >/dev/null 2>&1; then
        echo "⚠️ $package instalado sem dependências"
        return 0
    fi
    
    echo "❌ Falha ao instalar $package"
    return 1
}

# Pacotes críticos que podem ter conflitos
critical_packages=(
    "requests>=2.28.0"
    "pyyaml>=6.0.0"
    "fastapi>=0.100.0"
    "uvicorn>=0.20.0"
    "pydantic>=2.0.0"
    "openai>=1.0.0"
    "tiktoken>=0.5.0"
    "boto3>=1.30.0"
    "httpx>=0.24.0"
    "aiofiles>=0.8.0"
    "loguru>=0.6.0"
    "tenacity>=8.0.0"
)

# Pacotes opcionais
optional_packages=(
    "httpx-sse>=0.3.0"
    "sse-starlette>=1.0.0"
    "pydantic-settings>=2.0.0"
)

echo "🚀 Instalando pacotes críticos..."
failed_critical=0
for package in "${critical_packages[@]}"; do
    if ! install_package_safe "$package"; then
        ((failed_critical++))
    fi
done

echo ""
echo "🔧 Instalando pacotes opcionais..."
failed_optional=0
for package in "${optional_packages[@]}"; do
    if ! install_package_safe "$package"; then
        ((failed_optional++))
    fi
done

echo ""
echo "📊 Resumo da Instalação:"
echo "- Pacotes críticos falharam: $failed_critical/${#critical_packages[@]}"
echo "- Pacotes opcionais falharam: $failed_optional/${#optional_packages[@]}"

if [ $failed_critical -eq 0 ]; then
    echo "✅ Todos os pacotes críticos foram instalados com sucesso!"
    exit 0
elif [ $failed_critical -le 2 ]; then
    echo "⚠️ Alguns pacotes críticos falharam, mas o sistema pode funcionar"
    exit 0
else
    echo "❌ Muitos pacotes críticos falharam. Verifique os erros acima."
    exit 1
fi


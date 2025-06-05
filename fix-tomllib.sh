#!/bin/bash

# OUDS - Correção Rápida para TOML Support
# ========================================

echo "🔧 OUDS - Correção Rápida: Suporte TOML (tomllib/tomli)"
echo "======================================================"
echo ""

# Verificar versão do Python
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python detectado: $python_version"

# Verificar se tomllib está disponível (Python 3.11+)
if python3 -c "import tomllib" 2>/dev/null; then
    echo "✅ tomllib está disponível (Python 3.11+)"
    echo "🎉 Suporte TOML OK!"
    exit 0
fi

echo "⚠️ tomllib não disponível, instalando tomli como fallback..."

# Verificar se tomli já está instalado
if python3 -c "import tomli" 2>/dev/null; then
    version=$(python3 -c "import tomli; print(tomli.__version__)" 2>/dev/null)
    echo "✅ tomli já está instalado (versão: $version)"
    echo "🎉 Suporte TOML OK via tomli!"
    exit 0
fi

echo "📦 Instalando tomli..."

# Tentar diferentes métodos de instalação
methods=(
    "pip3 install tomli>=2.0.0"
    "pip3 install --user tomli>=2.0.0"
    "pip3 install --user --force-reinstall tomli>=2.0.0"
    "python3 -m pip install tomli>=2.0.0"
    "python3 -m pip install --user tomli>=2.0.0"
)

for method in "${methods[@]}"; do
    echo "🔄 Tentando: $method"
    
    if $method >/dev/null 2>&1; then
        echo "✅ Sucesso com: $method"
        
        # Verificar se foi instalado corretamente
        if python3 -c "import tomli" 2>/dev/null; then
            version=$(python3 -c "import tomli; print(tomli.__version__)" 2>/dev/null)
            echo "🎉 tomli instalado com sucesso! (versão: $version)"
            echo ""
            echo "💡 Agora você pode executar:"
            echo "   ./start_backend.sh"
            echo "   ./start_ouds.sh"
            exit 0
        fi
    else
        echo "❌ Falhou: $method"
    fi
done

echo ""
echo "❌ Não foi possível instalar tomli automaticamente."
echo ""
echo "💡 Soluções manuais:"
echo ""
echo "1. Instalar manualmente:"
echo "   pip3 install tomli"
echo ""
echo "2. Usar ambiente virtual:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install tomli"
echo ""
echo "3. Instalar via gerenciador do sistema:"
echo "   # Ubuntu/Debian:"
echo "   sudo apt install python3-tomli"
echo "   # CentOS/RHEL/Fedora:"
echo "   sudo yum install python3-tomli"
echo ""
echo "4. Usar script de correção completa:"
echo "   ./fix-dependencies.sh"
echo ""
echo "ℹ️ Nota: O código foi atualizado para funcionar mesmo sem tomli,"
echo "   usando um fallback JSON simples."
echo ""

exit 1


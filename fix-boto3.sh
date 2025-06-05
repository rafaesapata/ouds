#!/bin/bash

# OUDS - Correção Rápida para Boto3
# =================================

echo "🔧 OUDS - Correção Rápida: Instalando Boto3"
echo "==========================================="
echo ""

# Verificar se boto3 já está instalado
if python3 -c "import boto3" 2>/dev/null; then
    version=$(python3 -c "import boto3; print(boto3.__version__)" 2>/dev/null)
    echo "✅ Boto3 já está instalado (versão: $version)"
    exit 0
fi

echo "📦 Instalando boto3 (AWS SDK para Python)..."

# Tentar diferentes métodos de instalação
methods=(
    "pip3 install boto3>=1.30.0"
    "pip3 install --user boto3>=1.30.0"
    "pip3 install --user --force-reinstall boto3>=1.30.0"
    "python3 -m pip install boto3>=1.30.0"
    "python3 -m pip install --user boto3>=1.30.0"
    "pip3 install boto3 botocore"
)

for method in "${methods[@]}"; do
    echo "🔄 Tentando: $method"
    
    if $method >/dev/null 2>&1; then
        echo "✅ Sucesso com: $method"
        
        # Verificar se foi instalado corretamente
        if python3 -c "import boto3" 2>/dev/null; then
            version=$(python3 -c "import boto3; print(boto3.__version__)" 2>/dev/null)
            echo "🎉 Boto3 instalado com sucesso! (versão: $version)"
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
echo "❌ Não foi possível instalar boto3 automaticamente."
echo ""
echo "💡 Soluções manuais:"
echo ""
echo "1. Instalar manualmente:"
echo "   pip3 install boto3"
echo ""
echo "2. Usar ambiente virtual:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install boto3"
echo ""
echo "3. Instalar via gerenciador do sistema:"
echo "   # Amazon Linux/CentOS/RHEL:"
echo "   sudo yum install python3-boto3"
echo "   # Ubuntu/Debian:"
echo "   sudo apt install python3-boto3"
echo "   # Fedora:"
echo "   sudo dnf install python3-boto3"
echo ""
echo "4. Usar script de correção completa:"
echo "   ./fix-dependencies.sh"
echo ""

exit 1


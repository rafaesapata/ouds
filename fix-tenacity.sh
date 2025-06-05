#!/bin/bash

# OUDS - Correção Rápida para Tenacity
# ====================================

echo "🔧 OUDS - Correção Rápida: Instalando Tenacity"
echo "=============================================="
echo ""

# Verificar se tenacity já está instalado
if python3 -c "import tenacity" 2>/dev/null; then
    version=$(python3 -c "import tenacity; print(tenacity.__version__)" 2>/dev/null)
    echo "✅ Tenacity já está instalado (versão: $version)"
    exit 0
fi

echo "📦 Instalando tenacity..."

# Tentar diferentes métodos de instalação
methods=(
    "pip3 install tenacity>=8.0.0"
    "pip3 install --user tenacity>=8.0.0"
    "pip3 install --user --force-reinstall tenacity>=8.0.0"
    "python3 -m pip install tenacity>=8.0.0"
    "python3 -m pip install --user tenacity>=8.0.0"
)

for method in "${methods[@]}"; do
    echo "🔄 Tentando: $method"
    
    if $method >/dev/null 2>&1; then
        echo "✅ Sucesso com: $method"
        
        # Verificar se foi instalado corretamente
        if python3 -c "import tenacity" 2>/dev/null; then
            version=$(python3 -c "import tenacity; print(tenacity.__version__)" 2>/dev/null)
            echo "🎉 Tenacity instalado com sucesso! (versão: $version)"
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
echo "❌ Não foi possível instalar tenacity automaticamente."
echo ""
echo "💡 Soluções manuais:"
echo ""
echo "1. Instalar manualmente:"
echo "   pip3 install tenacity"
echo ""
echo "2. Usar ambiente virtual:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install tenacity"
echo ""
echo "3. Instalar via gerenciador do sistema:"
echo "   # Ubuntu/Debian:"
echo "   sudo apt install python3-tenacity"
echo "   # CentOS/RHEL:"
echo "   sudo yum install python3-tenacity"
echo "   # Fedora:"
echo "   sudo dnf install python3-tenacity"
echo ""
echo "4. Usar instalação mínima:"
echo "   ./install-safe.sh"
echo ""

exit 1


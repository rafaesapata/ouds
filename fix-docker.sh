#!/bin/bash

# Script para instalar módulo Docker para OUDS
# Resolve o erro: ModuleNotFoundError: No module named 'docker'

echo "🐳 OUDS - Instalando módulo Docker..."
echo "===================================="

# Função para testar se docker está instalado
test_docker() {
    python3 -c "
import docker
print('✅ Docker instalado com sucesso!')
print('Versão:', docker.__version__)
try:
    client = docker.from_env()
    print('✅ Cliente Docker conectado')
except Exception as e:
    print('⚠️ Aviso: Docker daemon não está rodando, mas módulo está instalado')
    print('Para usar sandbox, inicie o Docker daemon')
" 2>/dev/null
}

# Verificar se já está instalado
echo "🔍 Verificando se Docker já está instalado..."
if test_docker; then
    echo "✅ Docker já está instalado e funcionando!"
    exit 0
fi

echo "📦 Instalando módulo Docker..."

# Estratégia 1: Instalação normal
echo "🔄 Tentativa 1: Instalação normal"
if pip3 install docker>=6.0.0; then
    echo "✅ Instalação normal bem-sucedida"
    if test_docker; then
        echo "🎉 Docker instalado e testado com sucesso!"
        exit 0
    fi
fi

# Estratégia 2: Instalação com --user
echo "🔄 Tentativa 2: Instalação com --user"
if pip3 install --user docker>=6.0.0; then
    echo "✅ Instalação com --user bem-sucedida"
    if test_docker; then
        echo "🎉 Docker instalado e testado com sucesso!"
        exit 0
    fi
fi

# Estratégia 3: Força reinstalação
echo "🔄 Tentativa 3: Força reinstalação"
if pip3 install --user --force-reinstall docker>=6.0.0; then
    echo "✅ Força reinstalação bem-sucedida"
    if test_docker; then
        echo "🎉 Docker instalado e testado com sucesso!"
        exit 0
    fi
fi

# Estratégia 4: Via gerenciador do sistema
echo "🔄 Tentativa 4: Via gerenciador do sistema"
if command -v yum >/dev/null 2>&1; then
    echo "Detectado sistema baseado em YUM (CentOS/RHEL/Amazon Linux)"
    if sudo yum install -y python3-docker; then
        echo "✅ Instalação via yum bem-sucedida"
        if test_docker; then
            echo "🎉 Docker instalado e testado com sucesso!"
            exit 0
        fi
    fi
elif command -v apt >/dev/null 2>&1; then
    echo "Detectado sistema baseado em APT (Ubuntu/Debian)"
    if sudo apt update && sudo apt install -y python3-docker; then
        echo "✅ Instalação via apt bem-sucedida"
        if test_docker; then
            echo "🎉 Docker instalado e testado com sucesso!"
            exit 0
        fi
    fi
fi

# Se chegou até aqui, houve problema
echo ""
echo "❌ Erro: Não foi possível instalar o módulo Docker"
echo ""
echo "🔧 Soluções manuais:"
echo "1. Instalar manualmente:"
echo "   pip3 install docker"
echo ""
echo "2. Usar ambiente virtual:"
echo "   python3 -m venv ouds-env"
echo "   source ouds-env/bin/activate"
echo "   pip install docker"
echo ""
echo "3. Verificar se pip está atualizado:"
echo "   pip3 install --upgrade pip"
echo "   pip3 install docker"
echo ""
echo "4. Para Amazon Linux/CentOS:"
echo "   sudo yum install python3-pip python3-devel"
echo "   pip3 install docker"
echo ""
echo "5. Para Ubuntu/Debian:"
echo "   sudo apt update"
echo "   sudo apt install python3-pip python3-dev"
echo "   pip3 install docker"

exit 1


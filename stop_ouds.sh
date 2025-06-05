#!/bin/bash

# OUDS - Script de Parada
# =======================

echo "🛑 OUDS - Parando Sistema"
echo "========================"
echo ""

# Função para parar processos em uma porta
stop_port() {
    local port=$1
    local service_name=$2
    
    echo "🔍 Verificando porta $port ($service_name)..."
    
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        echo "⏹️ Parando $service_name (porta $port)..."
        kill $pids 2>/dev/null
        
        # Aguardar um pouco
        sleep 2
        
        # Verificar se ainda está rodando
        local remaining_pids=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$remaining_pids" ]; then
            echo "💀 Forçando parada do $service_name..."
            kill -9 $remaining_pids 2>/dev/null
        fi
        
        echo "✅ $service_name parado"
    else
        echo "ℹ️ $service_name não estava rodando"
    fi
}

# Parar serviços nas portas padrão
stop_port 8000 "Backend (API)"
stop_port 5173 "Frontend (Interface Web)"

# Parar processos por nome (fallback)
echo ""
echo "🔍 Verificando processos por nome..."

# Parar processos do Python relacionados ao OUDS
python_pids=$(pgrep -f "api_server.py" 2>/dev/null)
if [ ! -z "$python_pids" ]; then
    echo "⏹️ Parando processos Python do OUDS..."
    kill $python_pids 2>/dev/null
    sleep 1
    # Verificar se ainda estão rodando
    remaining_python=$(pgrep -f "api_server.py" 2>/dev/null)
    if [ ! -z "$remaining_python" ]; then
        kill -9 $remaining_python 2>/dev/null
    fi
    echo "✅ Processos Python parados"
fi

# Parar processos do Node.js relacionados ao OUDS
node_pids=$(pgrep -f "vite.*ouds-frontend" 2>/dev/null)
if [ ! -z "$node_pids" ]; then
    echo "⏹️ Parando processos Node.js do OUDS..."
    kill $node_pids 2>/dev/null
    sleep 1
    # Verificar se ainda estão rodando
    remaining_node=$(pgrep -f "vite.*ouds-frontend" 2>/dev/null)
    if [ ! -z "$remaining_node" ]; then
        kill -9 $remaining_node 2>/dev/null
    fi
    echo "✅ Processos Node.js parados"
fi

echo ""
echo "🧹 Limpando arquivos temporários..."

# Limpar logs antigos (manter apenas os 5 mais recentes)
if [ -d "logs" ]; then
    find logs -name "*.log" -type f -mtime +5 -delete 2>/dev/null
fi

# Limpar cache do Node.js se necessário
if [ -d "ouds-frontend/.vite" ]; then
    echo "🗑️ Limpando cache do Vite..."
    rm -rf ouds-frontend/.vite
fi

echo ""
echo "✅ OUDS parado com sucesso!"
echo ""
echo "💡 Para iniciar novamente:"
echo "   ./start_ouds.sh      # Sistema completo"
echo "   ./start_backend.sh   # Apenas backend"
echo "   ./start_frontend.sh  # Apenas frontend"


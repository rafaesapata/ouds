#!/bin/bash

# OUDS - Script de Inicialização Completa
# =======================================

echo "🚀 OUDS - Oráculo UDS"
echo "===================="
echo "Iniciando sistema completo..."
echo ""

# Verificar se estamos no diretório correto
if [ ! -d "OpenManus" ] || [ ! -d "ouds-frontend" ]; then
    echo "❌ Erro: Diretórios do projeto não encontrados!"
    echo "💡 Execute este script a partir do diretório raiz do OUDS"
    echo "📁 Estrutura esperada:"
    echo "   - OpenManus/ (backend)"
    echo "   - ouds-frontend/ (frontend)"
    exit 1
fi

# Função para verificar se uma porta está em uso
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Porta em uso
    else
        return 1  # Porta livre
    fi
}

# Função para parar processos em uma porta
stop_port() {
    local port=$1
    local pids=$(lsof -ti:$port)
    if [ ! -z "$pids" ]; then
        echo "⏹️ Parando processos na porta $port..."
        kill $pids 2>/dev/null
        sleep 2
    fi
}

# Verificar portas
BACKEND_PORT=8000
FRONTEND_PORT=5173

echo "🔍 Verificando portas..."
if check_port $BACKEND_PORT; then
    echo "⚠️ Porta $BACKEND_PORT já está em uso"
    read -p "Deseja parar o processo existente? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        stop_port $BACKEND_PORT
    else
        echo "❌ Não é possível iniciar o backend na porta $BACKEND_PORT"
        exit 1
    fi
fi

if check_port $FRONTEND_PORT; then
    echo "⚠️ Porta $FRONTEND_PORT já está em uso"
    read -p "Deseja parar o processo existente? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        stop_port $FRONTEND_PORT
    else
        echo "❌ Não é possível iniciar o frontend na porta $FRONTEND_PORT"
        exit 1
    fi
fi

# Verificar dependências básicas
echo "🔍 Verificando dependências..."

# Verificar Python e pip
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 não encontrado!"
    echo "💡 Instale o Python 3.11 ou verifique se está no PATH"
    exit 1
fi

# Verificar Node.js e npm
if ! command -v node &> /dev/null; then
    echo "❌ Node.js não encontrado!"
    echo "💡 Instale o Node.js: https://nodejs.org/"
    exit 1
fi

# Verificar se a instalação foi feita
if [ ! -f "OpenManus/.env" ]; then
    echo "⚠️ Sistema não parece estar configurado."
    echo "🔧 Executando instalação..."
    if [ -f "install_ouds.sh" ]; then
        ./install_ouds.sh
        if [ $? -ne 0 ]; then
            echo "❌ Erro na instalação!"
            exit 1
        fi
    else
        echo "❌ Script de instalação não encontrado!"
        exit 1
    fi
fi

# Criar arquivo de log
LOG_DIR="logs"
mkdir -p $LOG_DIR
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# Função para cleanup ao sair
cleanup() {
    echo ""
    echo "🛑 Parando OUDS..."
    
    # Parar backend
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "⏹️ Backend parado"
    fi
    
    # Parar frontend
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "⏹️ Frontend parado"
    fi
    
    echo "👋 OUDS finalizado!"
    exit 0
}

# Configurar trap para cleanup
trap cleanup SIGINT SIGTERM

echo ""
echo "🚀 Iniciando OUDS..."
echo "==================="

# Iniciar backend em background
echo "🔧 Iniciando backend..."
./start_backend.sh > $BACKEND_LOG 2>&1 &
BACKEND_PID=$!

# Aguardar backend inicializar
echo "⏳ Aguardando backend inicializar..."
for i in {1..30}; do
    if curl -s --max-time 1 http://localhost:$BACKEND_PORT > /dev/null 2>&1; then
        echo "✅ Backend iniciado com sucesso!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Timeout: Backend não iniciou em 30 segundos"
        echo "📋 Verifique o log: $BACKEND_LOG"
        cleanup
        exit 1
    fi
    sleep 1
done

# Iniciar frontend em background
echo "🎨 Iniciando frontend..."
./start_frontend.sh > $FRONTEND_LOG 2>&1 &
FRONTEND_PID=$!

# Aguardar frontend inicializar
echo "⏳ Aguardando frontend inicializar..."
for i in {1..60}; do
    if curl -s --max-time 1 http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        echo "✅ Frontend iniciado com sucesso!"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "❌ Timeout: Frontend não iniciou em 60 segundos"
        echo "📋 Verifique o log: $FRONTEND_LOG"
        cleanup
        exit 1
    fi
    sleep 1
done

echo ""
echo "🎉 OUDS iniciado com sucesso!"
echo "============================"
echo ""
echo "🌐 URLs de Acesso:"
echo "   Interface Web: http://localhost:$FRONTEND_PORT"
echo "   API Backend:   http://localhost:$BACKEND_PORT"
echo "   Documentação:  http://localhost:$BACKEND_PORT/docs"
echo ""
echo "📋 Logs:"
echo "   Backend:  $BACKEND_LOG"
echo "   Frontend: $FRONTEND_LOG"
echo ""
echo "⏹️ Para parar o sistema, pressione Ctrl+C"
echo ""

# Aguardar indefinidamente
while true; do
    # Verificar se os processos ainda estão rodando
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Backend parou inesperadamente!"
        echo "📋 Verifique o log: $BACKEND_LOG"
        cleanup
        exit 1
    fi
    
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ Frontend parou inesperadamente!"
        echo "📋 Verifique o log: $FRONTEND_LOG"
        cleanup
        exit 1
    fi
    
    sleep 5
done


#!/bin/bash

# Script para diagnosticar e corrigir problemas do backend OUDS
# Resolve: ⚠️ Não foi possível conectar ao servidor localhost:8000

echo "🔍 OUDS - Diagnóstico e correção do backend..."
echo "=============================================="

# Verificar se estamos no diretório correto
if [ ! -d "OpenManus" ]; then
    echo "❌ Erro: Execute este script no diretório raiz do OUDS"
    echo "💡 Comando: cd /home/ec2-user/ouds && ./fix-backend.sh"
    exit 1
fi

echo "📁 Diretório atual: $(pwd)"

# Função para verificar porta
check_port() {
    local port=$1
    if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        echo "✅ Porta $port está em uso"
        netstat -tlnp | grep ":$port "
        return 0
    else
        echo "❌ Porta $port está livre"
        return 1
    fi
}

# Função para matar processos na porta 8000
kill_port_8000() {
    echo "🛑 Parando processos na porta 8000..."
    local pids=$(lsof -ti:8000 2>/dev/null)
    if [ -n "$pids" ]; then
        echo "🔄 Matando processos: $pids"
        kill -9 $pids 2>/dev/null || true
        sleep 2
    fi
    
    # Matar processos Python relacionados ao OUDS
    pkill -f "api_server.py" 2>/dev/null || true
    pkill -f "uvicorn" 2>/dev/null || true
    sleep 1
}

# Diagnóstico inicial
echo ""
echo "🔍 Diagnóstico inicial..."
echo "========================"

# Verificar porta 8000
echo "🌐 Verificando porta 8000..."
check_port 8000

# Verificar processos Python
echo ""
echo "🐍 Verificando processos Python..."
python_procs=$(ps aux | grep -E "(python|api_server|uvicorn)" | grep -v grep)
if [ -n "$python_procs" ]; then
    echo "✅ Processos Python encontrados:"
    echo "$python_procs"
else
    echo "❌ Nenhum processo Python relacionado encontrado"
fi

# Parar processos existentes
kill_port_8000

# Verificar dependências críticas
echo ""
echo "📦 Verificando dependências críticas..."
echo "======================================="

cd OpenManus

# Verificar se Python funciona
if ! python3 --version > /dev/null 2>&1; then
    echo "❌ Python3 não encontrado"
    exit 1
else
    echo "✅ Python3: $(python3 --version)"
fi

# Verificar dependências essenciais
echo "🔍 Verificando módulos essenciais..."
essential_modules=("fastapi" "uvicorn" "openai" "pydantic")

for module in "${essential_modules[@]}"; do
    if python3 -c "import $module" 2>/dev/null; then
        version=$(python3 -c "import $module; print(getattr($module, '__version__', 'N/A'))" 2>/dev/null)
        echo "✅ $module ($version)"
    else
        echo "❌ $module (não instalado)"
        echo "🔄 Instalando $module..."
        pip3 install --user $module || echo "⚠️ Erro ao instalar $module"
    fi
done

# Verificar arquivo .env
echo ""
echo "⚙️ Verificando configuração..."
echo "============================="

if [ ! -f ".env" ]; then
    echo "⚠️ Arquivo .env não encontrado"
    echo "📝 Criando .env de exemplo..."
    cat > .env << 'EOF'
# Configuração do OUDS Backend
OPENAI_API_KEY=sk-sua_chave_openai_aqui
OUDS_API_HOST=0.0.0.0
OUDS_API_PORT=8000
OUDS_DEBUG=false
EOF
    echo "✅ Arquivo .env criado"
    echo "⚠️ IMPORTANTE: Configure sua chave OpenAI no arquivo .env"
else
    echo "✅ Arquivo .env encontrado"
fi

# Verificar se a chave OpenAI está configurada
if grep -q "sk-" .env 2>/dev/null; then
    echo "✅ Chave OpenAI parece estar configurada"
else
    echo "⚠️ Chave OpenAI não configurada ou inválida"
    echo "💡 Edite o arquivo .env e adicione: OPENAI_API_KEY=sk-sua_chave_aqui"
fi

# Testar importação do módulo principal
echo ""
echo "🧪 Testando módulo principal..."
echo "==============================="

if python3 -c "from app.agent.manus import Manus; print('✅ Módulo Manus OK')" 2>/dev/null; then
    echo "✅ Importação do Manus bem-sucedida"
else
    echo "❌ Erro na importação do Manus"
    echo "🔄 Executando correções de dependências..."
    cd ..
    ./fix-dependencies.sh
    cd OpenManus
fi

# Tentar iniciar o servidor
echo ""
echo "🚀 Iniciando servidor backend..."
echo "================================"

echo "🔄 Tentando iniciar na porta 8000..."

# Iniciar servidor em background e capturar PID
python3 api_server.py &
SERVER_PID=$!

# Aguardar alguns segundos para o servidor iniciar
echo "⏳ Aguardando servidor iniciar..."
sleep 5

# Verificar se o processo ainda está rodando
if ps -p $SERVER_PID > /dev/null 2>&1; then
    echo "✅ Processo do servidor rodando (PID: $SERVER_PID)"
    
    # Verificar se a porta está respondendo
    sleep 2
    if check_port 8000; then
        echo "🎉 Servidor backend iniciado com sucesso!"
        echo "🌐 URL: http://localhost:8000"
        echo "📚 Documentação: http://localhost:8000/docs"
        
        # Testar endpoint básico
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ Endpoint de saúde respondendo"
        else
            echo "⚠️ Endpoint de saúde não responde (normal se não implementado)"
        fi
        
        echo ""
        echo "🎯 Próximos passos:"
        echo "=================="
        echo "1. ✅ Backend rodando na porta 8000"
        echo "2. 🌐 Acesse o frontend: http://localhost:5173"
        echo "3. 📚 Documentação da API: http://localhost:8000/docs"
        echo ""
        echo "🛑 Para parar o servidor: kill $SERVER_PID"
        
    else
        echo "❌ Servidor iniciou mas porta 8000 não está respondendo"
        kill $SERVER_PID 2>/dev/null || true
    fi
else
    echo "❌ Servidor falhou ao iniciar"
    echo "📋 Verificando logs de erro..."
    
    # Tentar iniciar em foreground para ver erros
    echo "🔍 Tentando iniciar em foreground para diagnóstico..."
    timeout 10s python3 api_server.py || echo "❌ Erro ao iniciar servidor"
fi

echo ""
echo "📋 Diagnóstico concluído!"
echo "========================"


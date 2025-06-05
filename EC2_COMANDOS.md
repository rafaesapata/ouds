# OUDS - Comandos para Amazon EC2
# ================================

## 🚨 ERRO: ModuleNotFoundError: No module named 'fastapi'

### ⚡ SOLUÇÃO RÁPIDA (Execute no seu EC2):

```bash
# 1. Navegar para o diretório
cd /home/ec2-user/ouds

# 2. Atualizar repositório
git pull

# 3. Instalar dependências essenciais
pip3 install --user fastapi uvicorn pydantic openai

# 4. Testar se funcionou
python3 -c "import fastapi; print('✅ FastAPI OK!')"
```

### 🔧 SOLUÇÃO COMPLETA:

```bash
# Script automático para EC2
./install-ec2.sh
```

### 🛠️ SOLUÇÕES ALTERNATIVAS:

#### Opção 1: Instalação com --user
```bash
pip3 install --user fastapi>=0.100.0 uvicorn>=0.20.0 pydantic>=2.0.0 openai>=1.0.0
```

#### Opção 2: Para Amazon Linux 2023
```bash
sudo yum update -y
sudo yum install -y python3-pip python3-devel
pip3 install --user fastapi uvicorn pydantic openai
```

#### Opção 3: Ambiente Virtual (Recomendado)
```bash
python3 -m venv ouds-env
source ouds-env/bin/activate
pip install fastapi uvicorn pydantic openai docker boto3
```

#### Opção 4: Com --break-system-packages (Python 3.11+)
```bash
pip3 install --break-system-packages fastapi uvicorn pydantic openai
```

### 🔍 VERIFICAR INSTALAÇÃO:

```bash
# Testar imports
python3 -c "
import fastapi, uvicorn, pydantic, openai
print('✅ Todas as dependências OK!')
print('FastAPI:', fastapi.__version__)
print('Uvicorn:', uvicorn.__version__)
"
```

### 🚀 INICIAR OUDS:

```bash
# Configurar OpenAI (OBRIGATÓRIO)
nano OpenManus/.env
# Adicionar: OPENAI_API_KEY=sk-sua_chave_aqui

# Iniciar sistema
./start_ouds.sh
```

### 🌐 ACESSAR:

- **Interface Web:** http://localhost:5173
- **API Backend:** http://localhost:8000
- **Documentação:** http://localhost:8000/docs

### 🆘 SE AINDA DER ERRO:

1. **Verificar Python:**
   ```bash
   python3 --version
   which python3
   ```

2. **Verificar pip:**
   ```bash
   pip3 --version
   which pip3
   ```

3. **Limpar cache:**
   ```bash
   pip3 cache purge
   ```

4. **Verificar PATH:**
   ```bash
   echo $PATH
   export PATH="$HOME/.local/bin:$PATH"
   ```

5. **Reinstalar pip:**
   ```bash
   curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
   python3 get-pip.py --user
   ```

### 📞 DIAGNÓSTICO:

```bash
# Script de diagnóstico
./diagnose.sh

# Ou manual:
python3 -c "
import sys
print('Python:', sys.version)
print('Path:', sys.path)
try:
    import fastapi
    print('✅ FastAPI OK')
except ImportError as e:
    print('❌ FastAPI Error:', e)
"
```


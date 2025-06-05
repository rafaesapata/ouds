# OUDS - Guia Rápido de Uso

## 🚀 Início Rápido

### 1. Instalação Automática
```bash
./install_ouds.sh
```

### 2. Configuração
Edite o arquivo `OpenManus/.env` e adicione sua chave da OpenAI:
```env
OPENAI_API_KEY=sk-sua_chave_aqui
```

### 3. Execução
```bash
# Iniciar sistema completo
./start_ouds.sh

# OU iniciar separadamente:
./start_backend.sh    # Terminal 1
./start_frontend.sh   # Terminal 2
```

### 4. Acesso
- **Interface Web**: http://localhost:5173
- **API**: http://localhost:8000

## 🔧 Comandos Úteis

### Backend
```bash
# Iniciar API manualmente
cd OpenManus
export PYTHONPATH=$(pwd)
python3 api_server.py

# Testar API
curl http://localhost:8000/

# Ver logs
tail -f logs/ouds.log
```

### Frontend
```bash
# Iniciar desenvolvimento
cd ouds-frontend
npm run dev --host

# Build para produção
npm run build

# Preview da build
npm run preview
```

## 🐛 Solução de Problemas

### Backend não inicia
1. Verificar se todas as dependências estão instaladas:
   ```bash
   cd OpenManus && pip install -r requirements.txt
   ```

2. Verificar PYTHONPATH:
   ```bash
   export PYTHONPATH=/caminho/para/OpenManus
   ```

3. Verificar porta 8000:
   ```bash
   lsof -i :8000
   ```

### Frontend não conecta
1. Verificar se backend está rodando:
   ```bash
   curl http://localhost:8000/
   ```

2. Verificar console do navegador para erros CORS

3. Limpar cache do navegador

### Erro de dependências
```bash
# Reinstalar dependências Python
cd OpenManus
pip install --force-reinstall -r requirements.txt

# Reinstalar dependências Node.js
cd ouds-frontend
rm -rf node_modules package-lock.json
npm install
```

## 📊 Monitoramento

### Verificar Status
```bash
# Status dos serviços
ps aux | grep -E "(api_server|npm)"

# Verificar portas
netstat -tlnp | grep -E "(8000|5173)"

# Logs em tempo real
tail -f OpenManus/logs/*.log
```

### Métricas da API
```bash
# Estatísticas básicas
curl http://localhost:8000/api/sessions

# Health check
curl http://localhost:8000/health
```

## 🔒 Segurança

### Produção
- Configurar CORS para domínios específicos
- Usar HTTPS
- Implementar rate limiting
- Configurar firewall

### Desenvolvimento
- Manter chaves de API seguras
- Não commitar arquivos .env
- Usar variáveis de ambiente

## 📈 Performance

### Otimizações Backend
- Usar gunicorn em produção
- Configurar cache Redis
- Implementar connection pooling

### Otimizações Frontend
- Build otimizada para produção
- Lazy loading de componentes
- Compressão de assets

## 🔄 Atualizações

### Atualizar OpenManus
```bash
cd OpenManus
git pull origin main
pip install -r requirements.txt
```

### Atualizar Frontend
```bash
cd ouds-frontend
npm update
```

## 📞 Suporte

Para problemas ou dúvidas:
1. Verificar logs de erro
2. Consultar documentação completa (OUDS_README.md)
3. Verificar issues conhecidos
4. Contatar equipe de desenvolvimento

---

**OUDS v1.0.8** - Sistema de IA conversacional baseado no OpenManus


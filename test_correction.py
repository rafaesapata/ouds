#!/usr/bin/env python3
"""
Script para testar a correção do erro 'dict' object has no attribute 'model'
"""

import asyncio
import json
import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("test_correction")

async def test_chat_stream(base_url="http://localhost:8000", workspace_id="default"):
    """Testa o endpoint de streaming de chat"""
    import aiohttp
    
    logger.info(f"Testando endpoint de streaming em {base_url}/chat/stream")
    
    # Dados para o teste
    test_data = {
        "message": "Olá, este é um teste para verificar a correção do erro.",
        "session_id": f"test_session_{datetime.now().timestamp()}",
        "workspace_id": workspace_id
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/chat/stream",
                json=test_data,
                timeout=30
            ) as response:
                if response.status == 200:
                    logger.info(f"Conexão estabelecida com sucesso (status {response.status})")
                    
                    # Processar a resposta de streaming
                    buffer = ""
                    async for line in response.content:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:].strip()
                            if data_str:
                                try:
                                    data = json.loads(data_str)
                                    if data.get("type") == "chunk":
                                        print(f"Chunk recebido: {data.get('content', '')[:50]}...")
                                    elif data.get("type") == "error":
                                        logger.error(f"Erro recebido: {data.get('error')}")
                                        return False
                                    elif data.get("type") == "end":
                                        logger.info("Streaming concluído com sucesso")
                                        return True
                                except json.JSONDecodeError:
                                    logger.warning(f"Erro ao decodificar JSON: {data_str}")
                else:
                    logger.error(f"Erro na conexão: status {response.status}")
                    error_text = await response.text()
                    logger.error(f"Detalhes do erro: {error_text}")
                    return False
    except Exception as e:
        logger.error(f"Exceção durante o teste: {e}")
        return False

async def main():
    """Função principal"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
        
    if len(sys.argv) > 2:
        workspace_id = sys.argv[2]
    else:
        workspace_id = "default"
    
    logger.info(f"Iniciando teste com base_url={base_url}, workspace_id={workspace_id}")
    
    success = await test_chat_stream(base_url, workspace_id)
    
    if success:
        logger.info("✅ TESTE PASSOU: A correção resolveu o problema!")
        sys.exit(0)
    else:
        logger.error("❌ TESTE FALHOU: O problema ainda persiste.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())


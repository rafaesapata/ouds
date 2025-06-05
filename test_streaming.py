#!/usr/bin/env python3
"""
Script para testar o endpoint de streaming do chat.
"""
import asyncio
import json
import sys
from urllib.parse import urljoin

import aiohttp


async def test_streaming(base_url="http://localhost:8000", workspace_id="default"):
    """Testa o endpoint de streaming do chat."""
    url = urljoin(base_url, "/chat/stream")
    
    # Dados para enviar
    data = {
        "message": "Olá, como você está?",
        "workspace_id": workspace_id,
        "session_id": None  # Deixar None para criar uma nova sessão
    }
    
    print(f"Enviando requisição para {url} com dados: {data}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    print(f"Erro: {response.status} - {await response.text()}")
                    return
                
                print(f"Status da resposta: {response.status}")
                
                # Processar o stream de eventos
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        try:
                            event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                            event_type = event_data.get('type')
                            
                            if event_type == 'start':
                                print(f"Streaming iniciado para sessão: {event_data.get('session_id')}")
                            elif event_type == 'chunk':
                                print(f"Chunk recebido: {event_data.get('content')}")
                            elif event_type == 'status':
                                print(f"Status: {event_data.get('data')}")
                            elif event_type == 'end':
                                print(f"Streaming finalizado para sessão: {event_data.get('session_id')}")
                            elif event_type == 'error':
                                print(f"Erro no streaming: {event_data.get('error')}")
                        except json.JSONDecodeError:
                            print(f"Erro ao decodificar JSON: {line}")
        except Exception as e:
            print(f"Erro na requisição: {e}")


if __name__ == "__main__":
    # Pegar argumentos da linha de comando
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    workspace_id = sys.argv[2] if len(sys.argv) > 2 else "default"
    
    print(f"Testando endpoint de streaming em {base_url} para workspace {workspace_id}")
    asyncio.run(test_streaming(base_url, workspace_id))


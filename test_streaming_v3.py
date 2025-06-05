#!/usr/bin/env python3
"""
Script para testar o endpoint de streaming do chat com suporte a workspaces e tratamento de erros.
"""
import asyncio
import json
import sys
import time
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
    
    print(f"\n=== Testando endpoint de streaming ===")
    print(f"URL: {url}")
    print(f"Workspace: {workspace_id}")
    print(f"Mensagem: {data['message']}")
    
    async with aiohttp.ClientSession() as session:
        try:
            start_time = time.time()
            async with session.post(url, json=data) as response:
                print(f"Status da resposta: {response.status}")
                
                if response.status != 200:
                    print(f"Erro: {response.status} - {await response.text()}")
                    return False
                
                # Processar o stream de eventos
                received_chunks = 0
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        try:
                            event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                            event_type = event_data.get('type')
                            
                            if event_type == 'start':
                                print(f"✅ Streaming iniciado para sessão: {event_data.get('session_id')}")
                            elif event_type == 'chunk':
                                received_chunks += 1
                                content = event_data.get('content')
                                print(f"✅ Chunk #{received_chunks}: {content[:30]}..." if len(content) > 30 else content)
                            elif event_type == 'status':
                                print(f"✅ Status: {event_data.get('data')}")
                            elif event_type == 'end':
                                print(f"✅ Streaming finalizado para sessão: {event_data.get('session_id')}")
                            elif event_type == 'error':
                                print(f"❌ Erro no streaming: {event_data.get('error')}")
                                return False
                        except json.JSONDecodeError:
                            print(f"❌ Erro ao decodificar JSON: {line}")
            
            end_time = time.time()
            print(f"✅ Teste concluído em {end_time - start_time:.2f} segundos")
            print(f"✅ Recebidos {received_chunks} chunks")
            return True
            
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            return False


async def test_multiple_workspaces():
    """Testa o endpoint de streaming com múltiplos workspaces."""
    workspaces = ["default", "test", "rafaelsapata"]
    results = {}
    
    for workspace in workspaces:
        print(f"\n--- Testando workspace: {workspace} ---\n")
        success = await test_streaming(workspace_id=workspace)
        results[workspace] = "✅ Sucesso" if success else "❌ Falha"
        await asyncio.sleep(1)  # Pequena pausa entre testes
    
    print("\n=== Resultados dos testes ===")
    for workspace, result in results.items():
        print(f"Workspace {workspace}: {result}")


if __name__ == "__main__":
    # Pegar argumentos da linha de comando
    if len(sys.argv) > 1 and sys.argv[1] == "--multi":
        print("Testando múltiplos workspaces")
        asyncio.run(test_multiple_workspaces())
    else:
        base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
        workspace_id = sys.argv[2] if len(sys.argv) > 2 else "default"
        
        print(f"Testando endpoint de streaming em {base_url} para workspace {workspace_id}")
        asyncio.run(test_streaming(base_url, workspace_id))


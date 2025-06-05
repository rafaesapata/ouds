#!/usr/bin/env python3
"""
Script para testar a implementação simplificada do endpoint de streaming.
"""
import json
import sys
import time
import urllib.request
import urllib.error
import urllib.parse


def test_streaming(base_url="http://localhost:8000", workspace_id="default"):
    """Testa o endpoint de streaming do chat."""
    url = f"{base_url}/chat/stream"
    
    # Dados para enviar
    data = {
        "message": "Qual é o site do dashboard APN?",
        "workspace_id": workspace_id,
        "session_id": None  # Deixar None para criar uma nova sessão
    }
    
    print(f"\n=== Testando endpoint de streaming simplificado ===")
    print(f"URL: {url}")
    print(f"Workspace: {workspace_id}")
    print(f"Mensagem: {data['message']}")
    
    try:
        # Converter dados para JSON
        data_json = json.dumps(data).encode('utf-8')
        
        # Criar requisição
        req = urllib.request.Request(
            url,
            data=data_json,
            headers={'Content-Type': 'application/json'}
        )
        
        # Enviar requisição
        start_time = time.time()
        with urllib.request.urlopen(req) as response:
            print(f"Status da resposta: {response.status}")
            
            # Ler resposta linha por linha
            for line in response:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    try:
                        event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                        event_type = event_data.get('type')
                        
                        if event_type == 'start':
                            print(f"✅ Streaming iniciado para sessão: {event_data.get('session_id')}")
                        elif event_type == 'chunk':
                            content = event_data.get('content')
                            print(f"✅ Chunk recebido: {content[:50]}..." if len(content) > 50 else content)
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
        return True
        
    except urllib.error.HTTPError as e:
        print(f"❌ Erro HTTP: {e.code} - {e.reason}")
        # Ler o corpo da resposta de erro
        error_body = e.read().decode('utf-8')
        print(f"Detalhes do erro: {error_body}")
        return False
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False


if __name__ == "__main__":
    # Pegar argumentos da linha de comando
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    workspace_id = sys.argv[2] if len(sys.argv) > 2 else "rafaelsapata"
    
    print(f"Testando endpoint de streaming em {base_url} para workspace {workspace_id}")
    test_streaming(base_url, workspace_id)


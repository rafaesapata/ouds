#!/usr/bin/env python3
"""
Script para testar a correção do erro 'dict' object has no attribute 'model' - Versão 2
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

logger = logging.getLogger("test_correction_v2")

async def test_chat_stream(base_url="http://localhost:8000", workspace_id="default"):
    """Testa o endpoint de streaming de chat"""
    import aiohttp
    
    logger.info(f"Testando endpoint de streaming em {base_url}/chat/stream")
    
    # Dados para o teste
    test_data = {
        "message": "Olá, este é um teste para verificar a correção do erro v2.",
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
                    chunks_received = 0
                    async for line in response.content:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:].strip()
                            if data_str:
                                try:
                                    data = json.loads(data_str)
                                    if data.get("type") == "chunk":
                                        chunks_received += 1
                                        print(f"Chunk {chunks_received} recebido: {data.get('content', '')[:50]}...")
                                    elif data.get("type") == "error":
                                        logger.error(f"Erro recebido: {data.get('error')}")
                                        return False
                                    elif data.get("type") == "end":
                                        logger.info(f"Streaming concluído com sucesso. Total de chunks: {chunks_received}")
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

async def test_schema_compatibility():
    """Testa a compatibilidade das classes Schema com diferentes formatos de dados"""
    try:
        # Importar as classes necessárias
        sys.path.append('/home/ubuntu/projects/ouds')
        from OpenManus.app.schema import Function, ToolCall, Message
        
        logger.info("Testando compatibilidade da classe Function")
        
        # Teste 1: Criar Function a partir de dicionário
        function_dict = {"name": "test_function", "arguments": '{"arg1": "value1"}'}
        function = Function.from_dict(function_dict)
        assert function.name == "test_function"
        assert function.arguments == '{"arg1": "value1"}'
        logger.info("✅ Teste 1 passou: Function.from_dict")
        
        # Teste 2: Converter Function para dicionário
        function_dump = function.model_dump()
        assert isinstance(function_dump, dict)
        assert function_dump["name"] == "test_function"
        assert function_dump["arguments"] == '{"arg1": "value1"}'
        logger.info("✅ Teste 2 passou: Function.model_dump")
        
        logger.info("Testando compatibilidade da classe ToolCall")
        
        # Teste 3: Criar ToolCall a partir de dicionário
        tool_call_dict = {
            "id": "test_id",
            "type": "function",
            "function": {"name": "test_function", "arguments": '{"arg1": "value1"}'}
        }
        tool_call = ToolCall.from_dict(tool_call_dict)
        assert tool_call.id == "test_id"
        assert tool_call.type == "function"
        assert tool_call.function.name == "test_function"
        logger.info("✅ Teste 3 passou: ToolCall.from_dict")
        
        logger.info("Testando compatibilidade da classe Message")
        
        # Teste 4: Criar Message a partir de tool_calls
        tool_calls = [tool_call]
        message = Message.from_tool_calls(tool_calls, content="Test content")
        assert message.role == "assistant"
        assert message.content == "Test content"
        assert len(message.tool_calls) == 1
        logger.info("✅ Teste 4 passou: Message.from_tool_calls com objetos ToolCall")
        
        # Teste 5: Criar Message a partir de dicionários de tool_calls
        tool_calls_dict = [tool_call_dict]
        message = Message.from_tool_calls(tool_calls_dict, content="Test content")
        assert message.role == "assistant"
        assert message.content == "Test content"
        assert len(message.tool_calls) == 1
        logger.info("✅ Teste 5 passou: Message.from_tool_calls com dicionários")
        
        # Teste 6: Criar Message a partir de tool_calls com dados incompletos
        incomplete_tool_call = {"id": "test_id"}  # Sem function
        message = Message.from_tool_calls([incomplete_tool_call], content="Test content")
        assert message.role == "assistant"
        assert message.content == "Test content"
        assert len(message.tool_calls) == 0  # Deve ser ignorado por estar incompleto
        logger.info("✅ Teste 6 passou: Message.from_tool_calls com dados incompletos")
        
        return True
    except Exception as e:
        logger.error(f"Erro nos testes de compatibilidade: {e}")
        return False

async def main():
    """Função principal"""
    logger.info("Iniciando testes de correção v2")
    
    # Teste 1: Compatibilidade das classes Schema
    logger.info("Executando teste de compatibilidade das classes Schema")
    schema_test_result = await test_schema_compatibility()
    
    if schema_test_result:
        logger.info("✅ Testes de compatibilidade das classes Schema passaram!")
    else:
        logger.error("❌ Testes de compatibilidade das classes Schema falharam.")
        sys.exit(1)
    
    # Teste 2: Endpoint de streaming (opcional, se o servidor estiver disponível)
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        
        if len(sys.argv) > 2:
            workspace_id = sys.argv[2]
        else:
            workspace_id = "default"
        
        logger.info(f"Executando teste de streaming com base_url={base_url}, workspace_id={workspace_id}")
        stream_test_result = await test_chat_stream(base_url, workspace_id)
        
        if stream_test_result:
            logger.info("✅ Teste de streaming passou!")
        else:
            logger.error("❌ Teste de streaming falhou.")
            sys.exit(1)
    else:
        logger.info("Teste de streaming não executado. Para testar, forneça a URL do servidor como argumento.")
    
    logger.info("✅ TODOS OS TESTES PASSARAM: A correção resolveu o problema!")
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())


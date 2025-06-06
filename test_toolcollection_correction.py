#!/usr/bin/env python3
"""
Script de teste para verificar a correção do erro 'ToolCollection' object has no attribute 'to_openai_tools'
"""

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, '/home/ubuntu/projects/ouds/OpenManus')

def test_tool_collection_to_openai_tools():
    """Testa se o método to_openai_tools existe e funciona corretamente."""
    try:
        from app.tool.tool_collection import ToolCollection
        from app.tool.base import BaseTool
        
        # Criar uma tool de exemplo para teste
        class TestTool(BaseTool):
            def __init__(self):
                super().__init__(
                    name="test_tool",
                    description="Uma tool de teste",
                    parameters={
                        "type": "object",
                        "properties": {
                            "input": {
                                "type": "string",
                                "description": "Input de teste"
                            }
                        },
                        "required": ["input"]
                    }
                )
            
            async def execute(self, **kwargs):
                return f"Executado com: {kwargs}"
        
        # Criar uma coleção de tools
        test_tool = TestTool()
        collection = ToolCollection(test_tool)
        
        # Testar se o método to_openai_tools existe
        if not hasattr(collection, 'to_openai_tools'):
            print("❌ ERRO: Método to_openai_tools não existe na classe ToolCollection")
            return False
        
        # Testar se o método funciona
        openai_tools = collection.to_openai_tools()
        
        # Verificar se o resultado tem o formato correto
        if not isinstance(openai_tools, list):
            print("❌ ERRO: to_openai_tools deve retornar uma lista")
            return False
        
        if len(openai_tools) != 1:
            print(f"❌ ERRO: Esperado 1 tool, mas retornou {len(openai_tools)}")
            return False
        
        tool = openai_tools[0]
        
        # Verificar estrutura do tool
        expected_keys = ["type", "function"]
        if not all(key in tool for key in expected_keys):
            print(f"❌ ERRO: Tool deve ter as chaves {expected_keys}, mas tem {list(tool.keys())}")
            return False
        
        if tool["type"] != "function":
            print(f"❌ ERRO: Tool type deve ser 'function', mas é '{tool['type']}'")
            return False
        
        function = tool["function"]
        expected_function_keys = ["name", "description", "parameters"]
        if not all(key in function for key in expected_function_keys):
            print(f"❌ ERRO: Function deve ter as chaves {expected_function_keys}, mas tem {list(function.keys())}")
            return False
        
        if function["name"] != "test_tool":
            print(f"❌ ERRO: Function name deve ser 'test_tool', mas é '{function['name']}'")
            return False
        
        print("✅ TESTE PASSOU: Método to_openai_tools funciona corretamente!")
        print(f"Formato retornado: {openai_tools}")
        return True
        
    except Exception as e:
        print(f"❌ ERRO: Exceção durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_tool_collection():
    """Testa se a classe ToolCollection pode ser importada sem erros."""
    try:
        from app.tool.tool_collection import ToolCollection
        print("✅ TESTE PASSOU: ToolCollection importada com sucesso")
        return True
    except Exception as e:
        print(f"❌ ERRO: Não foi possível importar ToolCollection: {e}")
        return False

def main():
    """Executa todos os testes."""
    print("🔧 Testando correção do erro 'ToolCollection' object has no attribute 'to_openai_tools'")
    print("=" * 80)
    
    # Teste 1: Importação
    print("\n1. Testando importação da ToolCollection...")
    if not test_import_tool_collection():
        print("\n❌ TESTE FALHOU: Não foi possível importar ToolCollection")
        return False
    
    # Teste 2: Método to_openai_tools
    print("\n2. Testando método to_openai_tools...")
    if not test_tool_collection_to_openai_tools():
        print("\n❌ TESTE FALHOU: Método to_openai_tools não funciona corretamente")
        return False
    
    print("\n" + "=" * 80)
    print("✅ TODOS OS TESTES PASSARAM: A correção foi implementada com sucesso!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


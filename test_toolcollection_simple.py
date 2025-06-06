#!/usr/bin/env python3
"""
Script de teste simplificado para verificar a correção do erro 'ToolCollection' object has no attribute 'to_openai_tools'
Este teste não depende de módulos externos como browser_use.
"""

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, '/home/ubuntu/projects/ouds/OpenManus')

def test_tool_collection_method_exists():
    """Testa se o método to_openai_tools existe na classe ToolCollection."""
    try:
        # Importar apenas o que precisamos
        import inspect
        
        # Ler o arquivo diretamente para verificar se o método existe
        with open('/home/ubuntu/projects/ouds/OpenManus/app/tool/tool_collection.py', 'r') as f:
            content = f.read()
        
        # Verificar se o método to_openai_tools está definido
        if 'def to_openai_tools(' not in content:
            print("❌ ERRO: Método to_openai_tools não encontrado no arquivo")
            return False
        
        # Verificar se o método retorna o tipo correto
        if 'List[Dict[str, Any]]' not in content:
            print("❌ ERRO: Método to_openai_tools não tem o tipo de retorno correto")
            return False
        
        # Verificar se o método chama to_param()
        if 'tool.to_param()' not in content:
            print("❌ ERRO: Método to_openai_tools não chama tool.to_param()")
            return False
        
        print("✅ TESTE PASSOU: Método to_openai_tools está definido corretamente!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO: Exceção durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_syntax_validation():
    """Testa se o arquivo tem sintaxe válida."""
    try:
        import py_compile
        py_compile.compile('/home/ubuntu/projects/ouds/OpenManus/app/tool/tool_collection.py', doraise=True)
        print("✅ TESTE PASSOU: Arquivo tool_collection.py tem sintaxe válida")
        return True
    except Exception as e:
        print(f"❌ ERRO: Arquivo tool_collection.py tem erro de sintaxe: {e}")
        return False

def test_method_signature():
    """Testa se a assinatura do método está correta."""
    try:
        with open('/home/ubuntu/projects/ouds/OpenManus/app/tool/tool_collection.py', 'r') as f:
            content = f.read()
        
        # Procurar pela definição do método
        lines = content.split('\n')
        method_line = None
        for i, line in enumerate(lines):
            if 'def to_openai_tools(' in line:
                method_line = line.strip()
                break
        
        if not method_line:
            print("❌ ERRO: Definição do método to_openai_tools não encontrada")
            return False
        
        # Verificar se a assinatura está correta
        expected_signature = "def to_openai_tools(self) -> List[Dict[str, Any]]:"
        if expected_signature not in method_line:
            print(f"❌ ERRO: Assinatura incorreta. Esperado: {expected_signature}")
            print(f"Encontrado: {method_line}")
            return False
        
        print("✅ TESTE PASSOU: Assinatura do método to_openai_tools está correta!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO: Exceção durante verificação da assinatura: {e}")
        return False

def test_method_implementation():
    """Testa se a implementação do método está correta."""
    try:
        with open('/home/ubuntu/projects/ouds/OpenManus/app/tool/tool_collection.py', 'r') as f:
            content = f.read()
        
        # Verificar se a implementação está correta
        if 'return [tool.to_param() for tool in self.tools]' not in content:
            print("❌ ERRO: Implementação do método to_openai_tools está incorreta")
            return False
        
        print("✅ TESTE PASSOU: Implementação do método to_openai_tools está correta!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO: Exceção durante verificação da implementação: {e}")
        return False

def main():
    """Executa todos os testes."""
    print("🔧 Testando correção do erro 'ToolCollection' object has no attribute 'to_openai_tools'")
    print("=" * 80)
    
    tests = [
        ("Validação de sintaxe", test_syntax_validation),
        ("Existência do método", test_tool_collection_method_exists),
        ("Assinatura do método", test_method_signature),
        ("Implementação do método", test_method_implementation),
    ]
    
    all_passed = True
    
    for i, (test_name, test_func) in enumerate(tests, 1):
        print(f"\n{i}. {test_name}...")
        if not test_func():
            print(f"\n❌ TESTE FALHOU: {test_name}")
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ TODOS OS TESTES PASSARAM: A correção foi implementada com sucesso!")
        print("\nO método to_openai_tools() foi adicionado à classe ToolCollection e deve resolver o erro:")
        print("'ToolCollection' object has no attribute 'to_openai_tools'")
    else:
        print("❌ ALGUNS TESTES FALHARAM: A correção precisa ser revisada")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


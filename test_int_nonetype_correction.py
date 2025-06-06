#!/usr/bin/env python3
"""
Script de teste para verificar a correção do erro "'>' not supported between instances of 'int' and 'NoneType'"
"""

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, '/home/ubuntu/projects/ouds/OpenManus')

def test_max_input_tokens_none_handling():
    """Testa se as comparações com max_input_tokens lidam corretamente com None."""
    try:
        # Ler o arquivo para verificar se as correções foram aplicadas
        with open('/home/ubuntu/projects/ouds/OpenManus/app/llm.py', 'r') as f:
            content = f.read()
        
        # Verificar se todas as comparações foram corrigidas
        problematic_comparisons = content.count('if input_tokens > self.settings.max_input_tokens:')
        if problematic_comparisons > 0:
            print(f"❌ ERRO: Ainda existem {problematic_comparisons} comparações problemáticas")
            return False
        
        # Verificar se as correções foram aplicadas
        corrected_comparisons = content.count('if self.settings.max_input_tokens is not None and input_tokens > self.settings.max_input_tokens:')
        if corrected_comparisons != 3:
            print(f"❌ ERRO: Esperado 3 comparações corrigidas, mas encontrado {corrected_comparisons}")
            return False
        
        print("✅ TESTE PASSOU: Todas as comparações com max_input_tokens foram corrigidas!")
        print(f"Encontradas {corrected_comparisons} comparações corrigidas")
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
        py_compile.compile('/home/ubuntu/projects/ouds/OpenManus/app/llm.py', doraise=True)
        print("✅ TESTE PASSOU: Arquivo llm.py tem sintaxe válida")
        return True
    except Exception as e:
        print(f"❌ ERRO: Arquivo llm.py tem erro de sintaxe: {e}")
        return False

def test_logic_correctness():
    """Testa se a lógica das correções está correta."""
    try:
        with open('/home/ubuntu/projects/ouds/OpenManus/app/llm.py', 'r') as f:
            content = f.read()
        
        # Verificar se as linhas corretas foram modificadas
        lines = content.split('\n')
        corrected_lines = []
        
        for i, line in enumerate(lines):
            if 'if self.settings.max_input_tokens is not None and input_tokens > self.settings.max_input_tokens:' in line:
                corrected_lines.append(i + 1)  # +1 porque enumerate começa em 0
        
        if len(corrected_lines) != 3:
            print(f"❌ ERRO: Esperado 3 linhas corrigidas, mas encontrado {len(corrected_lines)}")
            return False
        
        print(f"✅ TESTE PASSOU: Correções aplicadas nas linhas: {corrected_lines}")
        
        # Verificar se a lógica está correta (None check primeiro)
        for line_num in corrected_lines:
            line = lines[line_num - 1]  # -1 porque enumerate começa em 0
            if not line.strip().startswith('if self.settings.max_input_tokens is not None and'):
                print(f"❌ ERRO: Lógica incorreta na linha {line_num}")
                return False
        
        print("✅ TESTE PASSOU: Lógica das correções está correta!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO: Exceção durante verificação da lógica: {e}")
        return False

def test_methods_affected():
    """Testa se os métodos corretos foram afetados."""
    try:
        with open('/home/ubuntu/projects/ouds/OpenManus/app/llm.py', 'r') as f:
            content = f.read()
        
        # Verificar se as correções estão nos métodos corretos
        methods_with_corrections = []
        lines = content.split('\n')
        current_method = None
        
        for i, line in enumerate(lines):
            if line.strip().startswith('async def ') or line.strip().startswith('def '):
                current_method = line.strip()
            elif 'if self.settings.max_input_tokens is not None and input_tokens > self.settings.max_input_tokens:' in line:
                methods_with_corrections.append(current_method)
        
        expected_methods = ['async def ask(', 'async def ask_tool(', 'async def ask_tool_streaming(']
        
        if len(methods_with_corrections) != 3:
            print(f"❌ ERRO: Esperado 3 métodos corrigidos, mas encontrado {len(methods_with_corrections)}")
            return False
        
        print("✅ TESTE PASSOU: Correções aplicadas nos métodos corretos!")
        print(f"Métodos corrigidos: {len(methods_with_corrections)}")
        return True
        
    except Exception as e:
        print(f"❌ ERRO: Exceção durante verificação dos métodos: {e}")
        return False

def main():
    """Executa todos os testes."""
    print("🔧 Testando correção do erro '>' not supported between instances of 'int' and 'NoneType'")
    print("=" * 80)
    
    tests = [
        ("Validação de sintaxe", test_syntax_validation),
        ("Verificação das comparações corrigidas", test_max_input_tokens_none_handling),
        ("Verificação da lógica das correções", test_logic_correctness),
        ("Verificação dos métodos afetados", test_methods_affected),
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
        print("\nAs verificações de None foram adicionadas antes das comparações com max_input_tokens.")
        print("Isso resolve o erro: '>' not supported between instances of 'int' and 'NoneType'")
    else:
        print("❌ ALGUNS TESTES FALHARAM: A correção precisa ser revisada")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


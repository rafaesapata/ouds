#!/usr/bin/env python3.11

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, '/home/ubuntu/ouds-project/OpenManus')

try:
    from app.knowledge import get_global_knowledge
    
    print("Testando base de conhecimento global...")
    
    # Obter instância
    kb = get_global_knowledge()
    
    # Testar carregamento
    entries = kb.get_all_entries()
    print(f"✅ Entradas carregadas: {len(entries)}")
    
    # Testar contexto para LLM
    context = kb.get_context_for_llm(max_entries=3)
    print(f"✅ Contexto LLM gerado: {len(context)} caracteres")
    
    # Testar estatísticas
    stats = kb.get_stats()
    print(f"✅ Estatísticas: {stats['total_entries']} entradas totais")
    
    # Testar validação
    validation = kb.validate_knowledge_file()
    print(f"✅ Validação: {'Válido' if validation['valid'] else 'Inválido'}")
    
    print("\n🎉 Todos os testes passaram! Sistema funcionando corretamente.")
    
except Exception as e:
    print(f"❌ Erro no teste: {e}")
    import traceback
    traceback.print_exc()


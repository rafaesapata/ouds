def get_agent_name():
    """Obtém o nome do agente da base de conhecimento global"""
    try:
        from app.knowledge import get_global_knowledge
        kb = get_global_knowledge()
        
        # Buscar diretiva de identidade (gk-001)
        identity_entry = kb.get_entry_by_id("gk-001")
        if identity_entry:
            # Extrair nome do agente da diretiva
            import re
            match = re.search(r"'([^']+)'", identity_entry.content)
            if match:
                return match.group(1)
        
        # Fallback para nome padrão
        return "OpenManus"
    except Exception:
        # Em caso de erro, usar nome padrão
        return "OpenManus"

def get_system_prompt_with_global_knowledge():
    """Constrói o prompt do sistema incluindo conhecimento global"""
    try:
        from app.knowledge import get_system_context_for_llm
        
        # Obter contexto global
        global_context = get_system_context_for_llm(max_entries=15)
        
        # Obter nome do agente
        agent_name = get_agent_name()
        
        # Construir prompt base
        base_prompt = (
            f"You are {agent_name}, an all-capable AI assistant, aimed at solving any task presented by the user. You have various tools at your disposal that you can call upon to efficiently complete complex requests. Whether it's programming, information retrieval, file processing, web browsing, or human interaction (only for extreme cases), you can handle it all. "
            "The initial directory is: {{directory}}. "
            "IMPORTANT: When creating files or projects, always create the necessary directory structure first using the str_replace_editor tool with 'create' command. If a directory doesn't exist, create it step by step before creating files inside it."
        )
        
        # Adicionar conhecimento global se disponível
        if global_context:
            return f"{base_prompt}\n\n{global_context}"
        else:
            return base_prompt
            
    except Exception as e:
        # Em caso de erro, usar prompt padrão
        agent_name = get_agent_name()
        return (
            f"You are {agent_name}, an all-capable AI assistant, aimed at solving any task presented by the user. You have various tools at your disposal that you can call upon to efficiently complete complex requests. Whether it's programming, information retrieval, file processing, web browsing, or human interaction (only for extreme cases), you can handle it all. "
            "The initial directory is: {{directory}}. "
            "IMPORTANT: When creating files or projects, always create the necessary directory structure first using the str_replace_editor tool with 'create' command. If a directory doesn't exist, create it step by step before creating files inside it."
        )

# Obter nome do agente dinamicamente
AGENT_NAME = get_agent_name()

# Obter prompt do sistema com conhecimento global
SYSTEM_PROMPT = get_system_prompt_with_global_knowledge()

NEXT_STEP_PROMPT = """
Based on user needs, proactively select the most appropriate tool or combination of tools. For complex tasks, you can break down the problem and use different tools step by step to solve it. After using each tool, clearly explain the execution results and suggest the next steps.

IMPORTANT: For simple questions or conversations, ALWAYS provide a helpful response first, then use the `terminate` tool to end the interaction. Never use `terminate` without first giving a proper response to the user's message. The user should always receive a meaningful answer before the conversation ends.

If you want to stop the interaction at any point, use the `terminate` tool/function call.
"""

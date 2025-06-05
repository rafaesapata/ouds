"""
OUDS - Integração de Arquivos com Sistema de Conhecimento
======================================================

Este módulo implementa a integração entre o sistema de arquivos do workspace
e o sistema de conhecimento, permitindo que o chat acesse arquivos.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import mimetypes
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class FileAccessManager:
    """Gerenciador de acesso a arquivos do workspace"""
    
    def __init__(self, base_path: Optional[str] = None):
        if base_path is None:
            # Detectar caminho dinamicamente baseado na configuração
            try:
                from app.config import config
                self.base_path = config.workspace_root
            except ImportError:
                # Fallback: usar caminho relativo ao arquivo atual
                current_file = Path(__file__).resolve()
                project_root = current_file.parent.parent.parent
                self.base_path = project_root / "workspace"
        else:
            self.base_path = Path(base_path)
    
    def get_workspace_path(self, workspace_id: str) -> Path:
        """Retorna o caminho do workspace"""
        workspace_path = self.base_path / workspace_id
        workspace_path.mkdir(exist_ok=True)
        
        # Garantir que o diretório de arquivos exista
        files_path = workspace_path / "files"
        files_path.mkdir(exist_ok=True)
        
        return workspace_path
    
    def list_files(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Lista todos os arquivos no workspace"""
        try:
            workspace_path = self.get_workspace_path(workspace_id)
            files_path = workspace_path / "files"
            
            files = []
            for file_path in files_path.rglob("*"):
                if file_path.is_file():
                    # Ignorar arquivos ocultos e do sistema
                    if file_path.name.startswith('.'):
                        continue
                    
                    stat = file_path.stat()
                    files.append({
                        "name": file_path.name,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "type": mimetypes.guess_type(str(file_path))[0] or "application/octet-stream",
                        "path": str(file_path.relative_to(files_path))
                    })
            
            # Ordenar por data de modificação (mais recente primeiro)
            files.sort(key=lambda x: x["modified"], reverse=True)
            return files
            
        except Exception as e:
            logger.error(f"Erro ao listar arquivos: {e}")
            return []
    
    def file_exists(self, workspace_id: str, filename: str) -> bool:
        """Verifica se um arquivo existe no workspace"""
        try:
            workspace_path = self.get_workspace_path(workspace_id)
            files_path = workspace_path / "files"
            file_path = files_path / filename
            
            # Verificação de segurança: garantir que o arquivo está dentro do workspace
            if not str(file_path.resolve()).startswith(str(files_path.resolve())):
                logger.warning(f"Tentativa de acesso a arquivo fora do workspace: {filename}")
                return False
            
            return file_path.exists() and file_path.is_file()
            
        except Exception as e:
            logger.error(f"Erro ao verificar existência do arquivo {filename}: {e}")
            return False
    
    def read_file(self, workspace_id: str, filename: str) -> Optional[str]:
        """Lê o conteúdo de um arquivo do workspace"""
        try:
            workspace_path = self.get_workspace_path(workspace_id)
            files_path = workspace_path / "files"
            file_path = files_path / filename
            
            # Verificação de segurança: garantir que o arquivo está dentro do workspace
            if not str(file_path.resolve()).startswith(str(files_path.resolve())):
                logger.warning(f"Tentativa de acesso a arquivo fora do workspace: {filename}")
                return None
            
            if not file_path.exists() or not file_path.is_file():
                logger.warning(f"Arquivo não encontrado: {filename}")
                return None
            
            # Verificar se é um arquivo de texto
            mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
            if not mime_type.startswith('text/') and mime_type != 'application/json':
                logger.warning(f"Arquivo não é de texto: {filename} ({mime_type})")
                return f"[Arquivo binário: {mime_type}]"
            
            # Ler conteúdo do arquivo
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            return content
            
        except Exception as e:
            logger.error(f"Erro ao ler arquivo {filename}: {e}")
            return None
    
    def get_file_info(self, workspace_id: str, filename: str) -> Optional[Dict[str, Any]]:
        """Obtém informações sobre um arquivo do workspace"""
        try:
            workspace_path = self.get_workspace_path(workspace_id)
            files_path = workspace_path / "files"
            file_path = files_path / filename
            
            # Verificação de segurança: garantir que o arquivo está dentro do workspace
            if not str(file_path.resolve()).startswith(str(files_path.resolve())):
                logger.warning(f"Tentativa de acesso a arquivo fora do workspace: {filename}")
                return None
            
            if not file_path.exists() or not file_path.is_file():
                logger.warning(f"Arquivo não encontrado: {filename}")
                return None
            
            stat = file_path.stat()
            return {
                "name": file_path.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "type": mimetypes.guess_type(str(file_path))[0] or "application/octet-stream",
                "path": str(file_path.relative_to(files_path))
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter informações do arquivo {filename}: {e}")
            return None
    
    def search_file_content(self, workspace_id: str, search_terms: List[str]) -> List[Tuple[str, str, float]]:
        """
        Busca termos em todos os arquivos do workspace e retorna os arquivos que contêm os termos,
        junto com trechos relevantes e uma pontuação de relevância.
        """
        results = []
        
        try:
            files = self.list_files(workspace_id)
            
            for file in files:
                content = self.read_file(workspace_id, file["name"])
                if not content:
                    continue
                
                # Calcular pontuação de relevância
                score = 0
                matches = []
                
                for term in search_terms:
                    if not term or len(term) < 3:
                        continue
                        
                    # Buscar o termo no conteúdo (case insensitive)
                    term_lower = term.lower()
                    content_lower = content.lower()
                    
                    if term_lower in content_lower:
                        # Aumentar pontuação baseado na frequência do termo
                        occurrences = content_lower.count(term_lower)
                        score += occurrences * len(term) * 0.1
                        
                        # Encontrar contexto ao redor do termo
                        start_pos = content_lower.find(term_lower)
                        if start_pos >= 0:
                            # Extrair um trecho ao redor do termo (50 caracteres antes e depois)
                            start = max(0, start_pos - 50)
                            end = min(len(content), start_pos + len(term) + 50)
                            excerpt = content[start:end]
                            
                            # Adicionar reticências se o trecho foi cortado
                            if start > 0:
                                excerpt = "..." + excerpt
                            if end < len(content):
                                excerpt = excerpt + "..."
                                
                            matches.append(excerpt)
                
                # Se encontrou correspondências, adicionar aos resultados
                if score > 0:
                    results.append((file["name"], "\n".join(matches[:3]), score))
            
            # Ordenar por pontuação (mais relevante primeiro)
            results.sort(key=lambda x: x[2], reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"Erro ao buscar conteúdo nos arquivos: {e}")
            return []

# Instância global do gerenciador de arquivos
file_access_manager = FileAccessManager()

def get_file_context_for_chat(workspace_id: str, message: str) -> Optional[str]:
    """
    Analisa a mensagem do usuário e verifica se há referências a arquivos.
    Se houver, retorna o contexto com o conteúdo dos arquivos.
    """
    try:
        # Log do workspace sendo usado
        logger.info(f"Buscando contexto de arquivos para workspace_id: {workspace_id}")
        
        # Verificar se a mensagem menciona arquivos
        file_keywords = [
            'arquivo', 'arquivos', 'file', 'files', 'documento', 'documentos', 
            'ler', 'leia', 'abrir', 'abra', 'mostrar', 'mostre', 'exibir', 'exiba',
            '.txt', '.json', '.csv', '.md', '.py', '.js', '.html', '.css'
        ]
        
        # Palavras-chave específicas para busca de conteúdo
        content_keywords = [
            'url', 'link', 'site', 'endereço', 'dashboard', 'painel', 'apn', 
            'versão', 'version', 'data', 'date', 'informação', 'information'
        ]
        
        has_file_reference = any(keyword in message.lower() for keyword in file_keywords)
        has_content_reference = any(keyword in message.lower() for keyword in content_keywords)
        
        # Listar arquivos disponíveis
        files = file_access_manager.list_files(workspace_id)
        if not files:
            if has_file_reference:
                return "Não há arquivos disponíveis no workspace."
            return None
        
        # Verificar se algum arquivo é mencionado explicitamente
        mentioned_files = []
        for file in files:
            if file["name"].lower() in message.lower():
                mentioned_files.append(file["name"])
        
        # Se não houver menção explícita, verificar se há menção a conteúdo de arquivos
        if not mentioned_files and (has_file_reference or has_content_reference):
            # Extrair termos de busca da mensagem
            search_terms = []
            
            # Adicionar palavras-chave de conteúdo encontradas na mensagem
            for keyword in content_keywords:
                if keyword in message.lower():
                    search_terms.append(keyword)
            
            # Adicionar substantivos e adjetivos da mensagem
            words = re.findall(r'\b[a-zA-Z0-9_-]{3,}\b', message.lower())
            search_terms.extend([word for word in words if len(word) > 3])
            
            # Buscar termos em todos os arquivos
            if search_terms:
                search_results = file_access_manager.search_file_content(workspace_id, search_terms)
                
                # Se encontrou resultados, adicionar aos arquivos mencionados
                if search_results:
                    for filename, _, _ in search_results[:2]:  # Limitar a 2 arquivos mais relevantes
                        if filename not in mentioned_files:
                            mentioned_files.append(filename)
        
        # Para cada arquivo mencionado, ler seu conteúdo
        file_contents = []
        for filename in mentioned_files:
            content = file_access_manager.read_file(workspace_id, filename)
            if content:
                # Limitar tamanho do conteúdo para não sobrecarregar o contexto
                if len(content) > 2000:
                    content = content[:2000] + "... [conteúdo truncado]"
                file_contents.append(f"Conteúdo do arquivo {filename}:\n```\n{content}\n```")
        
        if file_contents:
            return "\n\n".join(file_contents)
        
        # Se não encontrou arquivos específicos mas há referência a arquivos,
        # listar os arquivos disponíveis
        if has_file_reference:
            file_list = "\n".join([f"- {file['name']} ({file['type']})" for file in files[:10]])
            return f"Arquivos disponíveis no workspace:\n{file_list}"
        
        return None
        
    except Exception as e:
        logger.error(f"Erro ao obter contexto de arquivos: {e}")
        return None


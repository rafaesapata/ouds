import React from 'react';
import { FileText, Download, ExternalLink } from 'lucide-react';
import { buildApiUrl } from '@/lib/api.js';

/**
 * Componente para exibir um link para um arquivo gerado
 * 
 * @param {Object} props - Propriedades do componente
 * @param {string} props.filename - Nome do arquivo
 * @param {string} props.path - Caminho relativo do arquivo
 * @param {string} props.sessionId - ID da sessão atual
 * @param {string} props.description - Descrição opcional do arquivo
 */
const FileLink = ({ filename, path, sessionId, description }) => {
  // Construir URLs para download e visualização
  const downloadUrl = buildApiUrl(`/workspace/files/${encodeURIComponent(filename)}/download?session_id=${sessionId || ''}`);
  const previewUrl = buildApiUrl(`/workspace/files/${encodeURIComponent(filename)}/preview?session_id=${sessionId || ''}`);
  
  // Determinar o tipo de arquivo para ícone apropriado
  const getFileIcon = () => {
    const ext = filename.split('.').pop()?.toLowerCase();
    
    switch (ext) {
      case 'pdf':
        return <FileText className="h-4 w-4 text-red-500" />;
      case 'doc':
      case 'docx':
        return <FileText className="h-4 w-4 text-blue-500" />;
      case 'xls':
      case 'xlsx':
        return <FileText className="h-4 w-4 text-green-500" />;
      case 'ppt':
      case 'pptx':
        return <FileText className="h-4 w-4 text-orange-500" />;
      case 'txt':
      case 'md':
        return <FileText className="h-4 w-4 text-gray-500" />;
      case 'json':
      case 'xml':
      case 'html':
      case 'css':
      case 'js':
        return <FileText className="h-4 w-4 text-purple-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className="my-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getFileIcon()}
          <span className="font-medium text-blue-700 dark:text-blue-300">{filename}</span>
        </div>
        <div className="flex items-center space-x-2">
          <a 
            href={previewUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            className="p-1 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200"
            title="Visualizar arquivo"
          >
            <ExternalLink className="h-4 w-4" />
          </a>
          <a 
            href={downloadUrl} 
            download={filename}
            className="p-1 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200"
            title="Baixar arquivo"
          >
            <Download className="h-4 w-4" />
          </a>
        </div>
      </div>
      {description && (
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{description}</p>
      )}
    </div>
  );
};

export default FileLink;


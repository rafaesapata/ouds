import { useState, useEffect, useRef } from 'react';
import { X, Download, File, FileText, Code, Image, Archive, Eye, Trash2, Upload, Plus } from 'lucide-react';
import { buildApiUrl } from '@/lib/api.js';

const FileManager = ({ isOpen, onClose, sessionId }) => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewContent, setPreviewContent] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      fetchFiles();
    }
  }, [isOpen, sessionId]);

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const response = await fetch('/service/api/workspace/files', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setFiles(data.files || []);
      } else {
        console.error('Erro ao buscar arquivos:', response.statusText);
      }
    } catch (error) {
      console.error('Erro ao buscar arquivos:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFileLanguage = (filename) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    
    switch (ext) {
      case 'js':
      case 'jsx':
        return 'javascript';
      case 'ts':
      case 'tsx':
        return 'typescript';
      case 'py':
        return 'python';
      case 'java':
        return 'java';
      case 'cpp':
      case 'c':
        return 'cpp';
      case 'html':
        return 'html';
      case 'css':
        return 'css';
      case 'json':
        return 'json';
      case 'xml':
        return 'xml';
      case 'md':
        return 'markdown';
      case 'sql':
        return 'sql';
      case 'sh':
        return 'bash';
      default:
        return 'text';
    }
  };

  const isPreviewableFile = (filename) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    const previewableExtensions = [
      'txt', 'md', 'json', 'js', 'jsx', 'ts', 'tsx', 'py', 'java', 
      'cpp', 'c', 'h', 'html', 'css', 'xml', 'sql', 'sh', 'log',
      'csv', 'yml', 'yaml', 'ini', 'conf', 'config'
    ];
    return previewableExtensions.includes(ext);
  };

  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    
    switch (ext) {
      case 'txt':
      case 'md':
      case 'readme':
        return <FileText className="h-5 w-5 text-blue-500" />;
      case 'js':
      case 'jsx':
      case 'ts':
      case 'tsx':
      case 'py':
      case 'java':
      case 'cpp':
      case 'c':
      case 'html':
      case 'css':
      case 'json':
      case 'xml':
      case 'sql':
      case 'sh':
      case 'yml':
      case 'yaml':
        return <Code className="h-5 w-5 text-green-500" />;
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'gif':
      case 'svg':
      case 'webp':
        return <Image className="h-5 w-5 text-purple-500" />;
      case 'zip':
      case 'rar':
      case 'tar':
      case 'gz':
        return <Archive className="h-5 w-5 text-orange-500" />;
      default:
        return <File className="h-5 w-5 text-gray-500" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const downloadFile = async (filename) => {
    try {
      const response = await fetch(`/service/api/workspace/files/${encodeURIComponent(filename)}/download`, {
        method: 'GET',
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        console.error('Erro ao baixar arquivo:', response.statusText);
      }
    } catch (error) {
      console.error('Erro ao baixar arquivo:', error);
    }
  };

  const previewFile = async (filename) => {
    if (!isPreviewableFile(filename)) {
      alert('Este tipo de arquivo não pode ser visualizado.');
      return;
    }

    try {
      const response = await fetch(`/service/api/workspace/files/${encodeURIComponent(filename)}/preview`, {
        method: 'GET',
      });

      if (response.ok) {
        const content = await response.text();
        setPreviewContent(content);
        setSelectedFile(filename);
        setShowPreview(true);
      } else {
        console.error('Erro ao visualizar arquivo:', response.statusText);
      }
    } catch (error) {
      console.error('Erro ao visualizar arquivo:', error);
    }
  };

  const deleteFile = async (filename) => {
    if (!confirm(`Tem certeza que deseja excluir o arquivo "${filename}"?`)) {
      return;
    }

    try {
      const response = await fetch(`/service/api/workspace/files/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setFiles(files.filter(file => file.name !== filename));
        if (selectedFile === filename) {
          setShowPreview(false);
          setSelectedFile(null);
        }
      } else {
        console.error('Erro ao excluir arquivo:', response.statusText);
      }
    } catch (error) {
      console.error('Erro ao excluir arquivo:', error);
    }
  };

  const handleFileUpload = async (file) => {
    if (file.size > 10 * 1024 * 1024) {
      alert('Arquivo muito grande. Máximo 10MB.');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/service/api/workspace/files/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        fetchFiles();
      } else {
        console.error('Erro ao enviar arquivo:', response.statusText);
      }
    } catch (error) {
      console.error('Erro ao enviar arquivo:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-6xl h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            📁 Gerenciador de Arquivos
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex flex-1 min-h-0">
          {/* File List */}
          <div className="w-1/2 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Arquivos do Workspace
                </h3>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                    className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    <Plus className="h-4 w-4" />
                    <span>Upload</span>
                  </button>
                  <button
                    onClick={fetchFiles}
                    className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400"
                  >
                    🔄 Atualizar
                  </button>
                </div>
              </div>

              {/* Upload Zone */}
              <div
                className={`mb-4 border-2 border-dashed rounded-lg p-4 text-center transition-colors ${
                  dragOver 
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                    : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
                } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                {uploading ? (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                    <span className="text-sm text-gray-600 dark:text-gray-400">Enviando...</span>
                  </div>
                ) : (
                  <div>
                    <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Arraste arquivos aqui ou{' '}
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="text-blue-600 hover:text-blue-800 underline"
                      >
                        clique para selecionar
                      </button>
                    </p>
                    <p className="text-xs text-gray-500 mt-1">Máximo 10MB por arquivo</p>
                  </div>
                )}
              </div>

              {/* Hidden file input */}
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileChange}
                style={{ display: 'none' }}
                accept=".txt,.md,.json,.csv,.xml,.html,.css,.js,.py,.java,.cpp,.c,.h,.log,.yml,.yaml,.sql,.sh"
              />

              {/* File List */}
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="text-sm text-gray-500 mt-2">Carregando arquivos...</p>
                </div>
              ) : files.length === 0 ? (
                <div className="text-center py-8">
                  <File className="h-12 w-12 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">Nenhum arquivo encontrado</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {files.map((file) => (
                    <div
                      key={file.name}
                      className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
                        selectedFile === file.name
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center space-x-3 flex-1 min-w-0">
                        {getFileIcon(file.name)}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {file.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {formatFileSize(file.size)} • {new Date(file.modified).toLocaleDateString('pt-BR')}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-1">
                        {isPreviewableFile(file.name) && (
                          <button
                            onClick={() => previewFile(file.name)}
                            className="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                            title="Visualizar"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                        )}
                        <button
                          onClick={() => downloadFile(file.name)}
                          className="p-1 text-gray-400 hover:text-green-600 dark:hover:text-green-400"
                          title="Baixar"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => deleteFile(file.name)}
                          className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                          title="Excluir"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Preview Panel */}
          <div className="w-1/2 overflow-y-auto">
            <div className="p-4">
              {showPreview && selectedFile ? (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-2">
                      {getFileIcon(selectedFile)}
                      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {selectedFile}
                      </h3>
                      <span className="text-xs text-gray-500 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                        {getFileLanguage(selectedFile)}
                      </span>
                    </div>
                    <button
                      onClick={() => setShowPreview(false)}
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      Fechar
                    </button>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
                    <div className="bg-gray-100 dark:bg-gray-800 px-3 py-2 border-b border-gray-200 dark:border-gray-700">
                      <span className="text-xs text-gray-600 dark:text-gray-400 font-mono">
                        {selectedFile} • {previewContent.split('\n').length} linhas
                      </span>
                    </div>
                    <div className="p-4 max-h-96 overflow-y-auto">
                      <pre className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap font-mono leading-relaxed">
                        {previewContent}
                      </pre>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <Eye className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Visualização de Arquivos
                  </h3>
                  <p className="text-sm text-gray-500 mb-4">
                    Selecione um arquivo de código ou texto para visualizar seu conteúdo
                  </p>
                  <div className="text-xs text-gray-400 space-y-1">
                    <p>Tipos suportados:</p>
                    <p>📝 Texto: .txt, .md, .log</p>
                    <p>💻 Código: .js, .py, .java, .html, .css, .json</p>
                    <p>⚙️ Config: .yml, .xml, .sql, .sh</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileManager;


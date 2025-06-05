import React, { useState, useEffect, useRef } from 'react';
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
      } else {
        console.error('Erro ao excluir arquivo:', response.statusText);
      }
    } catch (error) {
      console.error('Erro ao excluir arquivo:', error);
    }
  };

  const isTextFile = (filename) => {
    const textExtensions = ['txt', 'md', 'js', 'jsx', 'ts', 'tsx', 'py', 'java', 'cpp', 'c', 'html', 'css', 'json', 'xml', 'readme'];
    const ext = filename.split('.').pop()?.toLowerCase();
    return textExtensions.includes(ext);
  };

  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    
    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/service/api/workspace/files/upload', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Upload failed');
        }

        const result = await response.json();
        console.log('File uploaded:', result);
      }

      // Refresh file list after upload
      await fetchFiles();
      
    } catch (error) {
      console.error('Error uploading files:', error);
      alert(`Erro no upload: ${error.message}`);
    } finally {
      setUploading(false);
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
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFileUpload(droppedFiles);
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    handleFileUpload(selectedFiles);
    
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl h-3/4 flex flex-col">
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
        <div className="flex-1 flex overflow-hidden">
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
                multiple
                onChange={handleFileSelect}
                className="hidden"
              />

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
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                    >
                      <div className="flex items-center space-x-3 flex-1 min-w-0">
                        {getFileIcon(file.name)}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {file.name}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {formatFileSize(file.size)} • {new Date(file.modified).toLocaleDateString('pt-BR')}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-1">
                        {isTextFile(file.name) && (
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
                          title="Download"
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
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      📄 Preview: {selectedFile}
                    </h3>
                    <button
                      onClick={() => setShowPreview(false)}
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      Fechar
                    </button>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 max-h-96 overflow-y-auto">
                    <pre className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap font-mono">
                      {previewContent}
                    </pre>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Eye className="h-12 w-12 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">
                    Selecione um arquivo de texto para visualizar
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700">
          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <span>
              {files.length} arquivo{files.length !== 1 ? 's' : ''} encontrado{files.length !== 1 ? 's' : ''}
            </span>
            <span>
              Workspace: /workspace
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileManager;


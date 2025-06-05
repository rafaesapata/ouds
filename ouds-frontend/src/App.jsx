import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Send, User, Bot, Loader2, Settings, RotateCcw, FolderOpen, Paperclip } from 'lucide-react'
import { apiRequest, checkBackendHealth, API_ENDPOINTS, buildApiUrl } from '@/lib/api.js'
import { useTaskProgressWebSocket } from '@/lib/taskProgress.js'
import TaskProgress from '@/components/TaskProgress.jsx'
import FileManager from '@/components/FileManager.jsx'
import CommandQueue from '@/components/CommandQueue.jsx'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [workspaceId, setWorkspaceId] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [abortController, setAbortController] = useState(null)
  const [streamingMessage, setStreamingMessage] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [showFileManager, setShowFileManager] = useState(false)
  const [attachedFile, setAttachedFile] = useState(null)
  const [isUploadingFile, setIsUploadingFile] = useState(false)
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)
  
  // Extract workspace from URL
  useEffect(() => {
    const path = window.location.pathname;
    const workspaceMatch = path.match(/^\/workspace\/(.+)$/);
    if (workspaceMatch) {
      const workspace = workspaceMatch[1];
      setWorkspaceId(workspace);
      console.log('🏢 Workspace detected:', workspace);
    } else {
      setWorkspaceId('default');
    }
  }, []);
  
  // Use WebSocket hook for real-time task progress
  const { tasks, currentStep, totalSteps, resetTasks } = useTaskProgressWebSocket(sessionId)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingMessage])

  useEffect(() => {
    // Test API connection and initialize workspace
    const testConnection = async () => {
      console.log('🔍 Testing backend connection...');
      const healthCheck = await checkBackendHealth();
      
      if (healthCheck.status === 'ok') {
        setIsConnected(true);
        console.log('✅ Connected to OUDS API:', healthCheck.data);
        
        // Initialize workspace if detected
        if (workspaceId && workspaceId !== 'default') {
          try {
            const response = await fetch(`/service/workspace/${workspaceId}`);
            if (response.ok) {
              const workspaceData = await response.json();
              console.log('🏢 Workspace initialized:', workspaceData);
            }
          } catch (error) {
            console.error('❌ Failed to initialize workspace:', error);
          }
        }
      } else {
        console.error('❌ Failed to connect to OUDS API:', healthCheck.error);
        setIsConnected(false);
        
        // Try alternative connection test
        try {
          const response = await fetch(buildApiUrl('/'));
          if (response.ok) {
            const data = await response.json();
            setIsConnected(true);
            console.log('✅ Connected to OUDS API (alternative):', data);
          }
        } catch (error) {
          console.error('❌ Alternative connection also failed:', error);
        }
      }
    };
    
    if (workspaceId) {
      testConnection();
    }
  }, [workspaceId])

  const cancelRequest = () => {
    if (abortController) {
      console.log('🛑 Canceling request...');
      abortController.abort();
      setAbortController(null);
      setIsLoading(false);
      setIsStreaming(false);
      setStreamingMessage('');
      resetTasks();
      
      // Add cancellation message
      const cancelMessage = {
        id: Date.now(),
        role: 'assistant',
        content: 'Operação cancelada pelo usuário.',
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, cancelMessage]);
    }
  };

  const sendMessageWithStreaming = async () => {
    if ((!inputMessage.trim() && !attachedFile) || isLoading) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: attachedFile 
        ? `${inputMessage || 'Arquivo enviado'}\n\n📎 Arquivo anexado: ${attachedFile.name}\n${attachedFile.content ? `Conteúdo do arquivo:\n\`\`\`\n${attachedFile.content}\n\`\`\`` : `Arquivo enviado: ${attachedFile.name} (${(attachedFile.size / 1024).toFixed(1)} KB)`}`
        : inputMessage,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    const currentMessage = inputMessage;
    setInputMessage('')
    setIsLoading(true)
    setIsStreaming(true)
    setStreamingMessage('')

    // Create abort controller for cancellation
    const controller = new AbortController();
    setAbortController(controller);

    // Reset tasks for new request
    resetTasks();

    try {
      console.log('🎯 Starting streaming request...');
      
      const response = await fetch('/service/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: attachedFile 
            ? `${currentMessage || 'Arquivo enviado'}\n\n📎 Arquivo anexado: ${attachedFile.name}\n${attachedFile.content ? `Conteúdo do arquivo:\n\`\`\`\n${attachedFile.content}\n\`\`\`` : `Arquivo enviado: ${attachedFile.name} (${(attachedFile.size / 1024).toFixed(1)} KB)`}`
            : currentMessage,
          session_id: sessionId,
          workspace_id: workspaceId
        }),
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              console.log('📡 Received streaming data:', data);
              
              if (data.type === 'progress') {
                // Task progress updates are handled by WebSocket
                console.log('📋 Task progress update received');
              } else if (data.type === 'response') {
                if (data.partial) {
                  setStreamingMessage(data.content);
                } else {
                  // Final response
                  const assistantMessage = {
                    id: Date.now(),
                    role: 'assistant',
                    content: data.content,
                    timestamp: new Date().toISOString()
                  };
                  setMessages(prev => [...prev, assistantMessage]);
                  setStreamingMessage('');
                }
              } else if (data.type === 'complete') {
                console.log('✅ Streaming completed');
                setSessionId(data.session_id);
                break;
              } else if (data.type === 'error') {
                throw new Error(data.message);
              }
            } catch (parseError) {
              console.error('❌ Error parsing streaming data:', parseError);
            }
          }
        }
      }

    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('🛑 Request was cancelled');
        return;
      }
      
      console.error('❌ Streaming error:', error);
      
      const errorMessage = {
        id: Date.now(),
        role: 'assistant',
        content: `Erro na comunicação: ${error.message}`,
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      setStreamingMessage('');
      setAbortController(null);
      // Clear attached file after sending
      setAttachedFile(null);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    const currentMessage = inputMessage;
    setInputMessage('')
    setIsLoading(true)

    // Create abort controller for cancellation
    const controller = new AbortController();
    setAbortController(controller);

    // Reset tasks for new request
    resetTasks()

    // Add debug task to show progress
    console.log('🎯 Starting new request, should show TaskProgress...');
    console.log('📡 Request details:', {
      message: currentMessage,
      sessionId: sessionId,
      endpoint: API_ENDPOINTS.CHAT,
      url: buildApiUrl(API_ENDPOINTS.CHAT)
    });

    try {
      // Add timeout to the request
      const timeoutId = setTimeout(() => {
        console.log('⏰ Request timeout after 60 seconds');
        controller.abort();
      }, 60000); // 60 seconds timeout

      console.log('📤 Sending request to:', buildApiUrl(API_ENDPOINTS.CHAT));

      // Use the new API system with abort signal
      const data = await apiRequest(API_ENDPOINTS.CHAT, {
        method: 'POST',
        signal: controller.signal,
        body: JSON.stringify({
          message: currentMessage,
          session_id: sessionId
        })
      });
      
      clearTimeout(timeoutId);
      console.log('📥 Received response:', data);
      
      if (!sessionId && data.session_id) {
        console.log('🆔 Setting session ID:', data.session_id);
        setSessionId(data.session_id)
      }

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response || data.message || 'Resposta vazia do backend',
        timestamp: data.timestamp || new Date().toISOString()
      }

      console.log('💬 Adding assistant message:', assistantMessage);
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('🛑 Request was cancelled');
        return; // Don't show error message for cancelled requests
      }
      
      console.error('❌ Error sending message:', error)
      console.error('❌ Error details:', {
        name: error.name,
        message: error.message,
        stack: error.stack
      });

      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `Desculpe, ocorreu um erro ao processar sua mensagem: ${error.message}. Verifique a configuração do backend no arquivo .env.`,
        timestamp: new Date().toISOString(),
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      setAbortController(null)
    }
  };

  const clearChat = () => {
    setMessages([]);
    setSessionId(null);
    setStreamingMessage('');
    setIsStreaming(false);
    setAttachedFile(null);
    resetTasks();
    console.log('🔄 Chat cleared, starting new conversation');
  };

  const handleFileAttach = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsUploadingFile(true);
    try {
      // Upload file to workspace
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/service/api/workspace/files/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const result = await response.json();
      
      // Try to read file content for text files
      let fileContent = '';
      if (file.type.startsWith('text/') || file.name.endsWith('.txt') || file.name.endsWith('.md') || file.name.endsWith('.json')) {
        try {
          const previewResponse = await fetch(`/service/api/workspace/files/${encodeURIComponent(file.name)}/preview`);
          if (previewResponse.ok) {
            fileContent = await previewResponse.text();
          }
        } catch (error) {
          console.warn('Could not read file content:', error);
        }
      }

      setAttachedFile({
        name: file.name,
        size: file.size,
        type: file.type,
        content: fileContent,
        uploadPath: result.saved_path
      });

      console.log('📎 File attached:', file.name);
    } catch (error) {
      console.error('❌ File upload error:', error);
      alert(`Erro ao enviar arquivo: ${error.message}`);
    } finally {
      setIsUploadingFile(false);
      // Clear the input so the same file can be selected again
      event.target.value = '';
    }
  };

  const removeAttachedFile = () => {
    setAttachedFile(null);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessageWithStreaming()
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessageWithStreaming()
  }

  return (
    <div className="h-screen bg-white dark:bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Bot className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
                Oráculo - Assistente Inteligente UDS
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {isConnected ? 'Conectado' : 'Desconectado'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {messages.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearChat}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Nova conversa
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowFileManager(true)}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              title="Gerenciador de Arquivos"
            >
              <FolderOpen className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col min-h-0">
        <ScrollArea className="flex-1 px-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-12">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                <Bot className="h-8 w-8 text-gray-400" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Como posso ajudar você hoje?
              </h2>
              <p className="text-gray-500 dark:text-gray-400 max-w-md">
                Digite uma mensagem abaixo para começar nossa conversa.
              </p>
            </div>
          ) : (
            <div className="py-4 space-y-6">
              {messages.map((message) => (
                <div key={message.id} className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      message.role === 'user' 
                        ? 'bg-blue-600' 
                        : message.isError 
                        ? 'bg-red-500' 
                        : 'bg-gray-600'
                    }`}>
                      {message.role === 'user' ? (
                        <User className="h-4 w-4 text-white" />
                      ) : (
                        <Bot className="h-4 w-4 text-white" />
                      )}
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {message.role === 'user' ? 'Você' : 'Oráculo'}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(message.timestamp).toLocaleTimeString('pt-BR', {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </span>
                    </div>
                    <div className={`prose prose-sm max-w-none ${
                      message.isError 
                        ? 'text-red-600 dark:text-red-400' 
                        : 'text-gray-700 dark:text-gray-300'
                    }`}>
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Streaming message */}
              {isStreaming && streamingMessage && (
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center bg-gray-600">
                      <Bot className="h-4 w-4 text-white" />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        Oráculo
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center">
                        <span className="animate-pulse mr-1">●</span>
                        processando...
                      </span>
                    </div>
                    <div className="prose prose-sm max-w-none text-gray-700 dark:text-gray-300">
                      <p className="whitespace-pre-wrap">
                        {streamingMessage}
                        <span className="animate-pulse">|</span>
                      </p>
                    </div>
                  </div>
                </div>
              )}
              
              {isLoading && !isStreaming && (
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
                      <Bot className="h-4 w-4 text-white" />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        Oráculo
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 text-gray-500 dark:text-gray-400">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Aguardando resposta...</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
          {/* Task Progress - Debug version */}
          {(isLoading || tasks.length > 0) && (
            <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">
                🎯 Task Progress {currentStep && totalSteps && `- Step ${currentStep}/${totalSteps}`}
              </div>
              
              {/* Debug info */}
              <div className="text-xs text-blue-600 dark:text-blue-300 mb-2">
                Debug: isLoading={isLoading.toString()}, tasks.length={tasks.length}, sessionId={sessionId || 'null'}
              </div>
              
              {/* Progress bar */}
              {currentStep && totalSteps && (
                <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2 mb-3">
                  <div 
                    className="bg-blue-600 dark:bg-blue-400 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(currentStep / totalSteps) * 100}%` }}
                  ></div>
                </div>
              )}
              
              {/* Tasks list */}
              {tasks.length > 0 ? (
                <div className="space-y-2">
                  {tasks.map((task, index) => (
                    <div key={task.id || index} className="text-sm">
                      <div className="flex items-center space-x-2">
                        <span className={`w-2 h-2 rounded-full ${
                          task.status === 'running' ? 'bg-blue-500 animate-pulse' :
                          task.status === 'completed' ? 'bg-green-500' :
                          task.status === 'error' ? 'bg-red-500' : 'bg-gray-400'
                        }`}></span>
                        <span className="font-medium">{task.title || 'Processing...'}</span>
                        <span className="text-xs text-gray-500">{task.subtitle}</span>
                      </div>
                      
                      {task.thoughts && (
                        <div className="ml-4 mt-1 text-xs text-gray-600 dark:text-gray-400">
                          ✨ {task.thoughts}
                        </div>
                      )}
                      
                      {task.tools && task.tools.length > 0 && (
                        <div className="ml-4 mt-1 text-xs text-gray-600 dark:text-gray-400">
                          🛠️ Tools: {task.tools.join(', ')}
                        </div>
                      )}
                      
                      {task.error && (
                        <div className="ml-4 mt-1 text-xs text-red-600 dark:text-red-400">
                          ❌ {task.error}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : isLoading && (
                <div className="text-sm text-blue-600 dark:text-blue-300">
                  <div className="flex items-center space-x-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Aguardando resposta do backend...</span>
                  </div>
                </div>
              )}
            </div>
          )}
          
          <TaskProgress 
            isVisible={isLoading || tasks.length > 0}
            tasks={tasks}
            currentStep={currentStep}
            totalSteps={totalSteps}
          />
          
          <CommandQueue 
            sessionId={sessionId}
            isVisible={true}
          />
          
          {/* Attached file preview */}
          {attachedFile && (
            <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Paperclip className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-800">{attachedFile.name}</span>
                  <span className="text-xs text-blue-600">({(attachedFile.size / 1024).toFixed(1)} KB)</span>
                  {attachedFile.content && (
                    <span className="text-xs text-green-600">✓ Conteúdo lido</span>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={removeAttachedFile}
                  className="text-blue-600 hover:text-blue-800 h-6 w-6 p-0"
                >
                  ×
                </Button>
              </div>
            </div>
          )}
          
          <div className="flex items-end space-x-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleFileAttach}
              disabled={isLoading || !isConnected || isUploadingFile}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              title="Anexar arquivo"
            >
              {isUploadingFile ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Paperclip className="h-4 w-4" />
              )}
            </Button>
            <div className="flex-1">
              <Input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Digite sua mensagem..."
                disabled={isLoading || !isConnected}
                className="resize-none border-gray-300 dark:border-gray-600 focus:border-blue-500 dark:focus:border-blue-400"
                rows={1}
              />
            </div>
            <Button
              onClick={isLoading ? cancelRequest : sendMessageWithStreaming}
              disabled={!isConnected || (!isLoading && !inputMessage.trim() && !attachedFile)}
              className={`px-4 py-2 ${
                isLoading 
                  ? 'bg-red-600 hover:bg-red-700 text-white' 
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
              title={isLoading ? 'Cancelar operação' : 'Enviar mensagem'}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Cancelar
                </>
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
          
          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileChange}
            style={{ display: 'none' }}
            accept=".txt,.md,.json,.csv,.xml,.html,.css,.js,.py,.java,.cpp,.c,.h,.log"
          />
          
          {!isConnected && (
            <div className="mt-2 text-sm text-red-500 dark:text-red-400">
              ⚠️ Não foi possível conectar ao servidor. Verifique a configuração do backend no arquivo .env
            </div>
          )}
          
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center space-y-1">
            <div>Oráculo pode cometer erros. Considere verificar informações importantes.</div>
            <div className="flex items-center justify-center space-x-2">
              <span>Oráculo - Assistente Inteligente UDS</span>
              <span>•</span>
              <span>v1.3.0</span>
              {workspaceId && workspaceId !== 'default' && (
                <>
                  <span>•</span>
                  <span className="text-blue-600 font-medium">Workspace: {workspaceId}</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* File Manager Modal */}
      <FileManager 
        isOpen={showFileManager}
        onClose={() => setShowFileManager(false)}
        sessionId={sessionId}
      />
    </div>
  )
}

export default App


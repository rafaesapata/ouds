import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Send, User, Bot, Loader2, Settings, RotateCcw } from 'lucide-react'
import './App.css'

const API_BASE_URL = 'http://localhost:8000'

function App() {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Test API connection
    fetch(`${API_BASE_URL}/`)
      .then(response => response.json())
      .then(data => {
        setIsConnected(true)
        console.log('Connected to OUDS API:', data)
      })
      .catch(error => {
        console.error('Failed to connect to OUDS API:', error)
        setIsConnected(false)
      })
  }, [])

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          session_id: sessionId
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      if (!sessionId) {
        setSessionId(data.session_id)
      }

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response,
        timestamp: data.timestamp
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Desculpe, ocorreu um erro ao processar sua mensagem. Verifique se o servidor OUDS está rodando.',
        timestamp: new Date().toISOString(),
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = () => {
    setMessages([])
    setSessionId(null)
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
                OUDS - Oráculo UDS
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
                        {message.role === 'user' ? 'Você' : 'OUDS'}
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
              
              {isLoading && (
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
                      <Bot className="h-4 w-4 text-white" />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        OUDS
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 text-gray-500 dark:text-gray-400">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Digitando...</span>
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
          <div className="flex items-end space-x-3">
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
              onClick={sendMessage}
              disabled={isLoading || !inputMessage.trim() || !isConnected}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
          
          {!isConnected && (
            <div className="mt-2 text-sm text-red-500 dark:text-red-400">
              ⚠️ Não foi possível conectar ao servidor. Verifique se está rodando em localhost:8000
            </div>
          )}
          
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
            OUDS pode cometer erros. Considere verificar informações importantes.
          </div>
        </div>
      </div>
    </div>
  )
}

export default App


import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Bug, Server, Eye, Trash2, Download } from 'lucide-react'
import { apiRequest, API_ENDPOINTS } from '@/lib/api'

const DebugPanel = ({ isOpen, onClose, workspaceId }) => {
  const [logs, setLogs] = useState([])
  const [systemVars, setSystemVars] = useState({})
  const [systemStatus, setSystemStatus] = useState({})
  const [loading, setLoading] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadDebugInfo()
    }
  }, [isOpen])

  useEffect(() => {
    let interval
    if (autoRefresh && isOpen) {
      interval = setInterval(loadDebugInfo, 2000) // Atualizar a cada 2 segundos
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [autoRefresh, isOpen])

  const loadDebugInfo = async () => {
    setLoading(true)
    try {
      const response = await apiRequest(API_ENDPOINTS.admin.getDebugInfo, {
        method: 'GET',
        headers: { 'X-Workspace-ID': workspaceId }
      })
      
      if (response.success) {
        setLogs(response.data.recent_logs || [])
        setSystemVars(response.data.system_variables || {})
        setSystemStatus(response.data.system_status || {})
      }
    } catch (error) {
      console.error('Erro ao carregar informações de debug:', error)
    } finally {
      setLoading(false)
    }
  }

  const clearLogs = async () => {
    try {
      await apiRequest(API_ENDPOINTS.admin.clearLogs, {
        method: 'POST',
        headers: { 'X-Workspace-ID': workspaceId }
      })
      setLogs([])
    } catch (error) {
      console.error('Erro ao limpar logs:', error)
    }
  }

  const downloadLogs = async () => {
    try {
      const response = await apiRequest(API_ENDPOINTS.admin.downloadLogs, {
        method: 'GET',
        headers: { 'X-Workspace-ID': workspaceId }
      })
      
      if (response.success) {
        const blob = new Blob([response.data], { type: 'text/plain' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `ouds-logs-${new Date().toISOString().split('T')[0]}.txt`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
    } catch (error) {
      console.error('Erro ao baixar logs:', error)
    }
  }

  const getLogLevelColor = (level) => {
    switch (level.toLowerCase()) {
      case 'error': return 'bg-red-100 text-red-800'
      case 'warning': return 'bg-yellow-100 text-yellow-800'
      case 'info': return 'bg-blue-100 text-blue-800'
      case 'debug': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getSourceColor = (source) => {
    switch (source.toLowerCase()) {
      case 'frontend': return 'bg-green-100 text-green-800'
      case 'backend': return 'bg-purple-100 text-purple-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-2">
            <Bug className="h-5 w-5" />
            <h2 className="text-xl font-semibold">Painel de Debug</h2>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              <Eye className="h-4 w-4 mr-2" />
              {autoRefresh ? 'Pausar' : 'Auto-refresh'}
            </Button>
            <Button variant="ghost" onClick={onClose}>×</Button>
          </div>
        </div>

        <div className="p-6">
          <Tabs defaultValue="logs" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="logs">Logs do Sistema</TabsTrigger>
              <TabsTrigger value="variables">Variáveis</TabsTrigger>
              <TabsTrigger value="status">Status do Sistema</TabsTrigger>
            </TabsList>

            <TabsContent value="logs" className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium">Logs em Tempo Real</h3>
                <div className="flex space-x-2">
                  <Button size="sm" variant="outline" onClick={downloadLogs}>
                    <Download className="h-4 w-4 mr-2" />
                    Baixar
                  </Button>
                  <Button size="sm" variant="outline" onClick={clearLogs}>
                    <Trash2 className="h-4 w-4 mr-2" />
                    Limpar
                  </Button>
                </div>
              </div>

              <ScrollArea className="h-96 border rounded-lg p-4">
                <div className="space-y-2">
                  {logs.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">Nenhum log disponível</p>
                  ) : (
                    logs.map((log, index) => (
                      <div key={index} className="flex items-start space-x-2 text-sm">
                        <span className="text-gray-500 font-mono text-xs">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        <Badge className={`text-xs ${getLogLevelColor(log.level)}`}>
                          {log.level}
                        </Badge>
                        <Badge className={`text-xs ${getSourceColor(log.source)}`}>
                          {log.source}
                        </Badge>
                        <span className="flex-1">{log.message}</span>
                      </div>
                    ))
                  )}
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="variables" className="space-y-4">
              <h3 className="text-lg font-medium">Variáveis Carregadas</h3>
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Configurações do Sistema</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {Object.entries(systemVars).map(([key, value]) => (
                      <div key={key} className="flex justify-between text-sm">
                        <span className="font-medium">{key}:</span>
                        <span className="text-gray-600 font-mono">
                          {typeof value === 'string' && value.length > 30 
                            ? `${value.substring(0, 30)}...` 
                            : String(value)
                          }
                        </span>
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Variáveis de Ambiente</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium">NODE_ENV:</span>
                      <span className="text-gray-600 font-mono">{process.env.NODE_ENV || 'development'}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="font-medium">VITE_API_URL:</span>
                      <span className="text-gray-600 font-mono">{import.meta.env.VITE_API_URL || 'http://localhost:8000'}</span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="status" className="space-y-4">
              <h3 className="text-lg font-medium">Status do Sistema</h3>
              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center">
                      <Server className="h-4 w-4 mr-2" />
                      Backend
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Status:</span>
                        <Badge className={systemStatus.backend?.status === 'online' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                          {systemStatus.backend?.status || 'unknown'}
                        </Badge>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Uptime:</span>
                        <span className="text-gray-600">{systemStatus.backend?.uptime || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Memória:</span>
                        <span className="text-gray-600">{systemStatus.backend?.memory || 'N/A'}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">LLM Connections</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Text LLM:</span>
                        <Badge className={systemStatus.llm?.text_status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                          {systemStatus.llm?.text_status || 'unknown'}
                        </Badge>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Vision LLM:</span>
                        <Badge className={systemStatus.llm?.vision_status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                          {systemStatus.llm?.vision_status || 'unknown'}
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Performance</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Requests/min:</span>
                        <span className="text-gray-600">{systemStatus.performance?.requests_per_minute || '0'}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Avg Response:</span>
                        <span className="text-gray-600">{systemStatus.performance?.avg_response_time || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Active Sessions:</span>
                        <span className="text-gray-600">{systemStatus.performance?.active_sessions || '0'}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}

export default DebugPanel


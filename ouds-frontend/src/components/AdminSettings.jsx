import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { AlertCircle, CheckCircle, Settings, Trash2, Plus, TestTube } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { apiRequest, API_ENDPOINTS } from '@/lib/api'

const AdminSettings = ({ isOpen, onClose, workspaceId }) => {
  const [llmConfigs, setLlmConfigs] = useState([])
  const [systemVars, setSystemVars] = useState({})
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testingLLM, setTestingLLM] = useState(null)
  const [editingLLM, setEditingLLM] = useState(null)
  const [showAddLLM, setShowAddLLM] = useState(false)

  // Carregar configurações ao abrir
  useEffect(() => {
    if (isOpen) {
      loadConfigurations()
    }
  }, [isOpen])

  const loadConfigurations = async () => {
    setLoading(true)
    try {
      const response = await apiRequest(API_ENDPOINTS.admin.getConfig, {
        method: 'GET',
        headers: { 'X-Workspace-ID': workspaceId }
      })
      
      if (response.success) {
        setLlmConfigs(response.data.llm_configurations || [])
        setSystemVars(response.data.system_variables || {})
      }
    } catch (error) {
      console.error('Erro ao carregar configurações:', error)
    } finally {
      setLoading(false)
    }
  }

  const saveLLMConfig = async (config) => {
    setSaving(true)
    try {
      const response = await apiRequest(API_ENDPOINTS.admin.updateLLM, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Workspace-ID': workspaceId 
        },
        body: JSON.stringify(config)
      })
      
      if (response.success) {
        await loadConfigurations()
        setEditingLLM(null)
        setShowAddLLM(false)
      }
    } catch (error) {
      console.error('Erro ao salvar configuração LLM:', error)
    } finally {
      setSaving(false)
    }
  }

  const testLLMConnection = async (config) => {
    setTestingLLM(config.id)
    try {
      const response = await apiRequest(API_ENDPOINTS.admin.testLLM, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Workspace-ID': workspaceId 
        },
        body: JSON.stringify(config)
      })
      
      // Atualizar status do LLM baseado no teste
      const updatedConfig = {
        ...config,
        status: response.success ? 'active' : 'error'
      }
      await saveLLMConfig(updatedConfig)
      
    } catch (error) {
      console.error('Erro ao testar LLM:', error)
    } finally {
      setTestingLLM(null)
    }
  }

  const deleteLLMConfig = async (llmId) => {
    try {
      const response = await apiRequest(`${API_ENDPOINTS.admin.deleteLLM}/${llmId}`, {
        method: 'DELETE',
        headers: { 'X-Workspace-ID': workspaceId }
      })
      
      if (response.success) {
        await loadConfigurations()
      }
    } catch (error) {
      console.error('Erro ao deletar configuração LLM:', error)
    }
  }

  const LLMConfigForm = ({ config, onSave, onCancel }) => {
    const [formData, setFormData] = useState(config || {
      id: `llm_${Date.now()}`,
      name: '',
      type: 'text',
      provider: 'openai',
      model: 'gpt-4',
      base_url: 'https://api.openai.com/v1',
      api_key: '',
      api_type: '',
      max_tokens: 4096,
      temperature: 0.7,
      status: 'inactive',
      is_default: false
    })

    const handleSubmit = (e) => {
      e.preventDefault()
      onSave({
        ...formData,
        created_at: config?.created_at || new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
    }

    return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="name">Nome</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
            />
          </div>
          <div>
            <Label htmlFor="type">Tipo</Label>
            <Select value={formData.type} onValueChange={(value) => setFormData({...formData, type: value})}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="text">Text</SelectItem>
                <SelectItem value="vision">Vision</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="provider">Provedor</Label>
            <Select value={formData.provider} onValueChange={(value) => setFormData({...formData, provider: value})}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="anthropic">Anthropic</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="model">Modelo</Label>
            <Input
              id="model"
              value={formData.model}
              onChange={(e) => setFormData({...formData, model: e.target.value})}
              required
            />
          </div>
        </div>

        <div>
          <Label htmlFor="base_url">URL Base</Label>
          <Input
            id="base_url"
            value={formData.base_url}
            onChange={(e) => setFormData({...formData, base_url: e.target.value})}
            required
          />
        </div>

        <div>
          <Label htmlFor="api_key">Chave da API</Label>
          <Input
            id="api_key"
            type="password"
            value={formData.api_key}
            onChange={(e) => setFormData({...formData, api_key: e.target.value})}
            required
          />
        </div>

        <div>
          <Label htmlFor="api_type">Tipo da API (opcional)</Label>
          <Input
            id="api_type"
            value={formData.api_type}
            onChange={(e) => setFormData({...formData, api_type: e.target.value})}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="max_tokens">Máximo de Tokens</Label>
            <Input
              id="max_tokens"
              type="number"
              value={formData.max_tokens}
              onChange={(e) => setFormData({...formData, max_tokens: parseInt(e.target.value)})}
              required
            />
          </div>
          <div>
            <Label htmlFor="temperature">Temperatura</Label>
            <Input
              id="temperature"
              type="number"
              step="0.1"
              min="0"
              max="2"
              value={formData.temperature}
              onChange={(e) => setFormData({...formData, temperature: parseFloat(e.target.value)})}
              required
            />
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Switch
            id="is_default"
            checked={formData.is_default}
            onCheckedChange={(checked) => setFormData({...formData, is_default: checked})}
          />
          <Label htmlFor="is_default">Padrão para este tipo</Label>
        </div>

        <div className="flex justify-end space-x-2">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancelar
          </Button>
          <Button type="submit" disabled={saving}>
            {saving ? 'Salvando...' : 'Salvar'}
          </Button>
        </div>
      </form>
    )
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <h2 className="text-xl font-semibold">Configurações Administrativas</h2>
          </div>
          <Button variant="ghost" onClick={onClose}>×</Button>
        </div>

        <div className="p-6">
          <Tabs defaultValue="llm" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="llm">Configurações LLM</TabsTrigger>
              <TabsTrigger value="system">Variáveis do Sistema</TabsTrigger>
            </TabsList>

            <TabsContent value="llm" className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium">Configurações de LLM</h3>
                <Button onClick={() => setShowAddLLM(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Adicionar LLM
                </Button>
              </div>

              {showAddLLM && (
                <Card>
                  <CardHeader>
                    <CardTitle>Adicionar Nova Configuração LLM</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <LLMConfigForm
                      onSave={saveLLMConfig}
                      onCancel={() => setShowAddLLM(false)}
                    />
                  </CardContent>
                </Card>
              )}

              <ScrollArea className="h-96">
                <div className="space-y-4">
                  {llmConfigs.map((config) => (
                    <Card key={config.id}>
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="flex items-center space-x-2">
                              <span>{config.name}</span>
                              <Badge variant={config.status === 'active' ? 'default' : 'secondary'}>
                                {config.status}
                              </Badge>
                              {config.is_default && <Badge variant="outline">Padrão</Badge>}
                            </CardTitle>
                            <CardDescription>
                              {config.provider} - {config.model} ({config.type})
                            </CardDescription>
                          </div>
                          <div className="flex space-x-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => testLLMConnection(config)}
                              disabled={testingLLM === config.id}
                            >
                              <TestTube className="h-4 w-4" />
                              {testingLLM === config.id ? 'Testando...' : 'Testar'}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setEditingLLM(config)}
                            >
                              <Settings className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => deleteLLMConfig(config.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                      {editingLLM?.id === config.id && (
                        <CardContent>
                          <Separator className="mb-4" />
                          <LLMConfigForm
                            config={config}
                            onSave={saveLLMConfig}
                            onCancel={() => setEditingLLM(null)}
                          />
                        </CardContent>
                      )}
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="system" className="space-y-4">
              <h3 className="text-lg font-medium">Variáveis do Sistema</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Workspace Admin</Label>
                  <Input value={systemVars.admin_workspace || ''} readOnly />
                </div>
                <div>
                  <Label>Workspace Root</Label>
                  <Input value={systemVars.workspace_root || ''} readOnly />
                </div>
                <div>
                  <Label>Log Level</Label>
                  <Input value={systemVars.log_level || ''} readOnly />
                </div>
                <div>
                  <Label>Versão</Label>
                  <Input value={systemVars.version || ''} readOnly />
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}

export default AdminSettings


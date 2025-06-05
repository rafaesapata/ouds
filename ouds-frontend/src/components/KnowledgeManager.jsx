import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Brain, 
  Search, 
  Plus, 
  BarChart3, 
  Settings, 
  Lightbulb,
  Database,
  Cpu,
  TrendingUp,
  Clock,
  Target,
  Zap
} from 'lucide-react';

const KnowledgeManager = ({ workspaceId = 'default' }) => {
  const [knowledgeStats, setKnowledgeStats] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [llmStats, setLlmStats] = useState(null);
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(false);

  // Carregar estatísticas do workspace
  useEffect(() => {
    loadWorkspaceStats();
    loadLlmStats();
    loadInsights();
  }, [workspaceId]);

  const loadWorkspaceStats = async () => {
    try {
      const response = await fetch(`/service/api/knowledge/workspace/${workspaceId}/stats`);
      const data = await response.json();
      if (data.success) {
        setKnowledgeStats(data.stats);
      }
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  };

  const loadLlmStats = async () => {
    try {
      const response = await fetch('/service/api/llm/stats');
      const data = await response.json();
      if (data.success) {
        setLlmStats(data.stats);
      }
    } catch (error) {
      console.error('Erro ao carregar estatísticas das LLMs:', error);
    }
  };

  const loadInsights = async () => {
    try {
      const response = await fetch(`/service/api/evolution/workspace/${workspaceId}/insights`);
      const data = await response.json();
      if (data.success) {
        setInsights(data.insights);
      }
    } catch (error) {
      console.error('Erro ao carregar insights:', error);
    }
  };

  const searchKnowledge = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/service/api/knowledge/workspace/${workspaceId}/search?q=${encodeURIComponent(searchQuery)}&limit=10`);
      const data = await response.json();
      if (data.success) {
        setSearchResults(data.results);
      }
    } catch (error) {
      console.error('Erro ao buscar conhecimento:', error);
    } finally {
      setLoading(false);
    }
  };

  const addKnowledge = async (content, type = 'fact', tags = []) => {
    try {
      const response = await fetch(`/service/api/knowledge/workspace/${workspaceId}/add`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          type,
          tags,
          source: 'manual'
        }),
      });
      
      const data = await response.json();
      if (data.success) {
        loadWorkspaceStats(); // Recarregar estatísticas
        return true;
      }
    } catch (error) {
      console.error('Erro ao adicionar conhecimento:', error);
    }
    return false;
  };

  const cleanupWorkspace = async () => {
    try {
      const response = await fetch(`/service/api/knowledge/workspace/${workspaceId}/cleanup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          days_threshold: 90
        }),
      });
      
      const data = await response.json();
      if (data.success) {
        loadWorkspaceStats();
        alert(`Limpeza concluída: ${data.removed_count} entradas removidas`);
      }
    } catch (error) {
      console.error('Erro na limpeza:', error);
    }
  };

  const getTypeColor = (type) => {
    const colors = {
      fact: 'bg-blue-100 text-blue-800',
      preference: 'bg-green-100 text-green-800',
      context: 'bg-purple-100 text-purple-800',
      pattern: 'bg-orange-100 text-orange-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const getInsightColor = (type) => {
    const colors = {
      low_usage: 'bg-yellow-100 text-yellow-800',
      high_usage: 'bg-green-100 text-green-800',
      pattern_trend: 'bg-blue-100 text-blue-800',
      no_recent_activity: 'bg-red-100 text-red-800',
      low_learning_rate: 'bg-orange-100 text-orange-800',
      high_learning_rate: 'bg-purple-100 text-purple-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Brain className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Base de Conhecimento</h1>
            <p className="text-gray-600">Workspace: {workspaceId}</p>
          </div>
        </div>
        <Button onClick={cleanupWorkspace} variant="outline" size="sm">
          <Settings className="h-4 w-4 mr-2" />
          Limpar Antigos
        </Button>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Visão Geral</TabsTrigger>
          <TabsTrigger value="search">Buscar</TabsTrigger>
          <TabsTrigger value="llms">LLMs</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        {/* Visão Geral */}
        <TabsContent value="overview" className="space-y-6">
          {knowledgeStats && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total de Conhecimento</CardTitle>
                  <Database className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{knowledgeStats.total_knowledge_entries}</div>
                  <p className="text-xs text-muted-foreground">
                    Entradas na base de conhecimento
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Conversas</CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{knowledgeStats.total_conversations}</div>
                  <p className="text-xs text-muted-foreground">
                    Conversas processadas
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Uso Médio</CardTitle>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{knowledgeStats.avg_knowledge_usage?.toFixed(1)}</div>
                  <p className="text-xs text-muted-foreground">
                    Vezes por entrada
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Última Atividade</CardTitle>
                  <Target className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-sm font-bold">
                    {knowledgeStats.last_updated ? 
                      new Date(knowledgeStats.last_updated).toLocaleDateString() : 
                      'N/A'
                    }
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Última atualização
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Distribuição por Tipo */}
          {knowledgeStats?.knowledge_by_type && (
            <Card>
              <CardHeader>
                <CardTitle>Distribuição por Tipo</CardTitle>
                <CardDescription>
                  Tipos de conhecimento armazenado no workspace
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(knowledgeStats.knowledge_by_type).map(([type, count]) => (
                    <Badge key={type} className={getTypeColor(type)}>
                      {type}: {count}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Buscar Conhecimento */}
        <TabsContent value="search" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Buscar Conhecimento</CardTitle>
              <CardDescription>
                Pesquise na base de conhecimento do workspace
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex space-x-2">
                <Input
                  placeholder="Digite sua busca..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && searchKnowledge()}
                />
                <Button onClick={searchKnowledge} disabled={loading}>
                  <Search className="h-4 w-4 mr-2" />
                  Buscar
                </Button>
              </div>

              {searchResults.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold">Resultados ({searchResults.length})</h3>
                  {searchResults.map((result) => (
                    <Card key={result.id} className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-sm text-gray-900">{result.content}</p>
                          <div className="flex items-center space-x-2 mt-2">
                            <Badge className={getTypeColor(result.type)}>
                              {result.type}
                            </Badge>
                            <span className="text-xs text-gray-500">
                              Confiança: {(result.confidence * 100).toFixed(0)}%
                            </span>
                            <span className="text-xs text-gray-500">
                              Usado: {result.usage_count}x
                            </span>
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* LLMs */}
        <TabsContent value="llms" className="space-y-6">
          {llmStats && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(llmStats).map(([provider, stats]) => (
                <Card key={provider}>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Cpu className="h-5 w-5" />
                      <span>{stats.name}</span>
                    </CardTitle>
                    <CardDescription>
                      {stats.enabled ? 'Ativo' : 'Inativo'}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Requisições:</span>
                      <span className="text-sm font-medium">{stats.metrics.total_requests}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Taxa de Sucesso:</span>
                      <span className="text-sm font-medium">
                        {stats.metrics.total_requests > 0 ? 
                          ((stats.metrics.successful_requests / stats.metrics.total_requests) * 100).toFixed(1) : 0
                        }%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Tempo Médio:</span>
                      <span className="text-sm font-medium">
                        {stats.metrics.avg_response_time?.toFixed(2)}s
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Custo Total:</span>
                      <span className="text-sm font-medium">
                        ${stats.metrics.total_cost?.toFixed(4)}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Insights */}
        <TabsContent value="insights" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Lightbulb className="h-5 w-5" />
                <span>Insights de Evolução</span>
              </CardTitle>
              <CardDescription>
                Análises automáticas sobre o desenvolvimento do workspace
              </CardDescription>
            </CardHeader>
            <CardContent>
              {insights.length > 0 ? (
                <div className="space-y-4">
                  {insights.map((insight, index) => (
                    <Card key={index} className="p-4">
                      <div className="flex items-start space-x-3">
                        <Zap className="h-5 w-5 text-yellow-500 mt-0.5" />
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <Badge className={getInsightColor(insight.insight_type)}>
                              {insight.insight_type}
                            </Badge>
                            <span className="text-xs text-gray-500">
                              Confiança: {(insight.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                          <p className="text-sm text-gray-900 mb-2">{insight.description}</p>
                          <p className="text-xs text-blue-600 font-medium">
                            💡 {insight.recommended_action}
                          </p>
                          {insight.supporting_evidence.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs text-gray-500">Evidências:</p>
                              <ul className="text-xs text-gray-600 list-disc list-inside">
                                {insight.supporting_evidence.map((evidence, i) => (
                                  <li key={i}>{evidence}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">
                  Nenhum insight disponível ainda. Continue usando o sistema para gerar análises.
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default KnowledgeManager;


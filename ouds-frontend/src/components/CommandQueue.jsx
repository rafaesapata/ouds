import React, { useState, useEffect } from 'react';
import { Clock, X, Play, Pause, CheckCircle, AlertCircle } from 'lucide-react';
import { buildApiUrl } from '@/lib/api.js';

const CommandQueue = ({ sessionId, isVisible }) => {
  const [queueData, setQueueData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isVisible && sessionId) {
      fetchQueueStatus();
      // Poll for updates every 2 seconds
      const interval = setInterval(fetchQueueStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [isVisible, sessionId]);

  const fetchQueueStatus = async () => {
    if (!sessionId) return;
    
    try {
      setLoading(true);
      const response = await fetch(`/service/api/sessions/${sessionId}/queue`);
      
      if (response.ok) {
        const data = await response.json();
        setQueueData(data);
      } else {
        console.error('Erro ao buscar status da fila:', response.statusText);
      }
    } catch (error) {
      console.error('Erro ao buscar status da fila:', error);
    } finally {
      setLoading(false);
    }
  };

  const cancelCommand = async (commandId) => {
    try {
      const response = await fetch(buildApiUrl(`/api/sessions/${sessionId}/queue/${commandId}`), {
        method: 'DELETE',
      });

      if (response.ok) {
        // Refresh queue status
        await fetchQueueStatus();
      } else {
        console.error('Erro ao cancelar comando:', response.statusText);
      }
    } catch (error) {
      console.error('Erro ao cancelar comando:', error);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'processing':
        return <Play className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending':
        return 'Aguardando';
      case 'processing':
        return 'Processando';
      case 'completed':
        return 'Concluído';
      case 'failed':
        return 'Falhou';
      default:
        return 'Desconhecido';
    }
  };

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  if (!isVisible || !queueData) {
    return null;
  }

  const { queue, current_processing, total_pending } = queueData;
  const hasActivity = current_processing || queue.length > 0;

  if (!hasActivity) {
    return null;
  }

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm mb-4">
      <div className="p-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white flex items-center">
            <Clock className="h-4 w-4 mr-2" />
            Fila de Comandos
          </h3>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {total_pending} pendente{total_pending !== 1 ? 's' : ''}
          </div>
        </div>
      </div>

      <div className="p-3 space-y-2">
        {/* Current Processing */}
        {current_processing && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-2 flex-1 min-w-0">
                {getStatusIcon(current_processing.status)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                    🔄 Processando agora
                  </p>
                  <p className="text-sm text-blue-700 dark:text-blue-300 truncate">
                    {current_processing.message}
                  </p>
                  <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                    Iniciado às {formatTime(current_processing.created_at)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Queue Items */}
        {queue.map((command, index) => (
          <div
            key={command.id}
            className="bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-3"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-2 flex-1 min-w-0">
                {getStatusIcon(command.status)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      #{index + 1} na fila
                    </p>
                    <span className="text-xs px-2 py-1 bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded">
                      {getStatusText(command.status)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-300 truncate mt-1">
                    {command.message}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Adicionado às {formatTime(command.created_at)}
                  </p>
                </div>
              </div>
              <button
                onClick={() => cancelCommand(command.id)}
                className="ml-2 p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                title="Cancelar comando"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}

        {/* Empty State */}
        {!current_processing && queue.length === 0 && (
          <div className="text-center py-4">
            <Clock className="h-8 w-8 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Nenhum comando na fila
            </p>
          </div>
        )}
      </div>

      {/* Refresh Button */}
      <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700">
        <button
          onClick={fetchQueueStatus}
          disabled={loading}
          className="w-full text-xs text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 disabled:opacity-50"
        >
          {loading ? 'Atualizando...' : '🔄 Atualizar status'}
        </button>
      </div>
    </div>
  );
};

export default CommandQueue;


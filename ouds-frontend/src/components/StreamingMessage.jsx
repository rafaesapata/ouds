import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Bot } from 'lucide-react';
import { Card } from '@/components/ui/card';

/**
 * Componente para exibir mensagens em streaming
 * 
 * @param {string} content - Conteúdo da mensagem em streaming
 * @param {boolean} isStreaming - Indica se o streaming está ativo
 */
const StreamingMessage = ({ content, isStreaming }) => {
  if (!content && !isStreaming) return null;
  
  return (
    <div className="flex items-start gap-3 mb-4">
      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
        <Bot className="h-5 w-5 text-blue-600" />
      </div>
      <Card className="p-4 bg-blue-50 rounded-lg flex-1 max-w-[85%]">
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown>{content || '...'}</ReactMarkdown>
          {isStreaming && !content && (
            <div className="flex items-center gap-1 mt-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse delay-150"></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse delay-300"></div>
            </div>
          )}
          {isStreaming && content && (
            <div className="inline-block w-1 h-4 bg-blue-500 ml-1 animate-pulse"></div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default StreamingMessage;


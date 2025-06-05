import React, { useState } from 'react';
import { Check, Copy } from 'lucide-react';

/**
 * Componente para exibir blocos de código com botão de copiar
 * 
 * @param {Object} props - Propriedades do componente
 * @param {string} props.code - Código a ser exibido
 * @param {string} props.language - Linguagem do código (opcional)
 */
const CodeBlock = ({ code, language }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    
    // Reset copied state after 2 seconds
    setTimeout(() => {
      setCopied(false);
    }, 2000);
  };

  return (
    <div className="relative group">
      <pre className="bg-gray-100 dark:bg-gray-800 p-3 rounded-lg overflow-x-auto">
        {language && (
          <div className="absolute top-0 right-0 bg-gray-200 dark:bg-gray-700 px-2 py-1 text-xs font-mono rounded-bl">
            {language}
          </div>
        )}
        <code className="text-sm font-mono">{code}</code>
      </pre>
      
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 p-1.5 bg-gray-200 dark:bg-gray-700 rounded opacity-0 group-hover:opacity-100 transition-opacity"
        title={copied ? "Copiado!" : "Copiar código"}
      >
        {copied ? (
          <Check className="h-4 w-4 text-green-500" />
        ) : (
          <Copy className="h-4 w-4 text-gray-600 dark:text-gray-300" />
        )}
      </button>
    </div>
  );
};

export default CodeBlock;


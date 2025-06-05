// OUDS - Configuração da API
// ===========================

// URL fixa da API (via proxy do frontend)
const API_CONFIG = {
  // URL base da API (sempre via proxy /service)
  BASE_URL: 'http://o.udstec.io/service',
  
  // Timeout padrão para requisições
  TIMEOUT: 30000,
  
  // Headers padrão
  HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
}

// Endpoints da API (com proxy /service → backend)
export const API_ENDPOINTS = {
  // Chat endpoints
  CHAT: '/service/api/chat',                    // /service/api/chat → (rewrite) → /api/chat
  CHAT_STREAM: '/service/chat/stream',          // /service/chat/stream → (rewrite) → /chat/stream
  
  // Root/Health
  ROOT: '/service/',                            // /service/ → (rewrite) → /
  
  // Sessions
  SESSIONS: '/service/api/sessions',            // /service/api/sessions → (rewrite) → /api/sessions
  DELETE_SESSION: '/service/api/sessions',      // /service/api/sessions/{id} → (rewrite) → /api/sessions/{id}
  SESSION_HISTORY: '/service/api/sessions',     // /service/api/sessions/{id}/history → (rewrite) → /api/sessions/{id}/history
  SESSION_PROGRESS: '/service/api/sessions',    // /service/api/sessions/{id}/progress → (rewrite) → /api/sessions/{id}/progress
  
  // Command Queue
  SESSION_QUEUE: '/service/api/sessions',       // /service/api/sessions/{id}/queue → (rewrite) → /api/sessions/{id}/queue
  
  // WebSockets
  WEBSOCKET: '/service/ws',                     // /service/ws/{id} → (rewrite) → /ws/{id}
  WEBSOCKET_PROGRESS: '/service/ws/progress',   // /service/ws/progress/{id} → (rewrite) → /ws/progress/{id}
  
  // Workspace
  WORKSPACE_FILES: '/service/api/workspace/files',        // /service/api/workspace/files → (rewrite) → /api/workspace/files
  WORKSPACE_DOWNLOAD: '/service/api/workspace/files',     // /service/api/workspace/files/{filename}/download → (rewrite) → /api/workspace/files/{filename}/download
  WORKSPACE_PREVIEW: '/service/api/workspace/files',      // /service/api/workspace/files/{filename}/preview → (rewrite) → /api/workspace/files/{filename}/preview
  WORKSPACE_UPLOAD: '/service/api/workspace/files/upload', // /service/api/workspace/files/upload → (rewrite) → /api/workspace/files/upload
  
  // GitHub
  GITHUB_CONFIG: '/service/api/github/config',   // /service/api/github/config → (rewrite) → /api/github/config
  GITHUB_REPOS: '/service/api/github/repos',     // /service/api/github/repos → (rewrite) → /api/github/repos
  GITHUB_CLONE: '/service/api/github/clone',     // /service/api/github/clone → (rewrite) → /api/github/clone
  GITHUB_COMMIT: '/service/api/github/commit'    // /service/api/github/commit → (rewrite) → /api/github/commit
}

// Função para construir URL completa da API
export function buildApiUrl(endpoint) {
  // Se o endpoint já começa com /service, usa direto
  if (endpoint.startsWith('/service')) {
    return `http://o.udstec.io${endpoint}`;
  }
  
  // Para endpoints específicos, mapear corretamente
  const endpointMap = {
    // Chat
    'chat': '/service/api/chat',
    'chat/stream': '/service/chat/stream',
    
    // Root
    '': '/service/',
    '/': '/service/',
    
    // Sessions
    'sessions': '/service/api/sessions',
    
    // WebSocket
    'ws': '/service/ws',
    
    // Workspace
    'workspace/files': '/service/api/workspace/files',
    
    // GitHub
    'github/config': '/service/api/github/config',
    'github/repos': '/service/api/github/repos',
    'github/clone': '/service/api/github/clone',
    'github/commit': '/service/api/github/commit'
  };
  
  // Se tem mapeamento específico, usa ele
  if (endpointMap[endpoint]) {
    return `http://o.udstec.io${endpointMap[endpoint]}`;
  }
  
  // Senão, adiciona /service/api por padrão
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `http://o.udstec.io/service/api/${cleanEndpoint}`;
}

// Função para fazer requisições à API
export async function apiRequest(endpoint, options = {}) {
  const url = buildApiUrl(endpoint);
  
  const defaultOptions = {
    method: 'GET',
    headers: API_CONFIG.HEADERS,
    timeout: API_CONFIG.TIMEOUT,
    ...options
  };

  try {
    console.log(`🌐 API Request: ${defaultOptions.method} ${url}`);
    console.log('📋 Request details:', {
      endpoint,
      url,
      method: defaultOptions.method,
      headers: defaultOptions.headers,
      hasBody: !!defaultOptions.body,
      bodyPreview: defaultOptions.body ? defaultOptions.body.substring(0, 100) + '...' : null
    });
    
    const response = await fetch(url, defaultOptions);
    
    console.log('📡 Response received:', {
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries()),
      url: response.url
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Response error body:', errorText);
      throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
    }
    
    const data = await response.json();
    console.log(`✅ API Response: ${response.status}`, data);
    
    return data;
  } catch (error) {
    console.error(`❌ API Error: ${error.message}`);
    console.error('❌ Full error details:', {
      name: error.name,
      message: error.message,
      stack: error.stack,
      url: url
    });
    throw error;
  }
}

// Função para verificar saúde do backend (aceita 404 como válido)
export async function checkBackendHealth() {
  try {
    // Usa endpoint raiz que retorna {"detail":"Not Found"} - isso é esperado
    const response = await fetch('http://o.udstec.io/service/');
    
    // Aceita tanto 200 quanto 404 como indicação de que o backend está funcionando
    if (response.ok || response.status === 404) {
      const data = await response.text();
      console.log('✅ Backend respondeu:', response.status, data);
      return { status: 'ok', data, statusCode: response.status };
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    console.error('❌ Backend não responde:', error.message);
    return { status: 'error', error: error.message };
  }
}

// Exportar configuração para debug
export { API_CONFIG };


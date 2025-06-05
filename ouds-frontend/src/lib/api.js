// OUDS - Configuração da API
// ===========================

// URL fixa da API (via proxy do frontend)
const API_CONFIG = {
  // URL base da API (sempre via proxy /api)
  BASE_URL: 'http://o.udstec.io/api',
  
  // Timeout padrão para requisições
  TIMEOUT: 30000,
  
  // Headers padrão
  HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
}

// Endpoints da API (com /api/api/ para compensar o rewrite)
export const API_ENDPOINTS = {
  CHAT: '/api/api/chat',                    // /api/api/chat → (rewrite) → /api/chat
  ROOT: '/api/',                            // /api/ → (rewrite) → /
  SESSIONS: '/api/api/sessions',            // /api/api/sessions → (rewrite) → /api/sessions
  DELETE_SESSION: '/api/api/sessions',      // /api/api/sessions/{id} → (rewrite) → /api/sessions/{id}
  SESSION_HISTORY: '/api/api/sessions',     // /api/api/sessions/{id}/history → (rewrite) → /api/sessions/{id}/history
  WEBSOCKET: '/api/ws'                      // /api/ws/{id} → (rewrite) → /ws/{id}
}

// Função para construir URL completa da API
export function buildApiUrl(endpoint) {
  // Se o endpoint já começa com /api, usa direto
  if (endpoint.startsWith('/api')) {
    return `http://o.udstec.io${endpoint}`;
  }
  
  // Para endpoints que precisam de /api/api/ (compensar rewrite)
  const needsDoubleApi = ['chat', 'sessions'];
  if (needsDoubleApi.includes(endpoint)) {
    return `http://o.udstec.io/api/api/${endpoint}`;
  }
  
  // Para WebSocket (não tem /api prefix no backend)
  if (endpoint === 'ws' || endpoint.startsWith('ws/')) {
    return `http://o.udstec.io/api/${endpoint}`;
  }
  
  // Senão, adiciona /api
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `http://o.udstec.io/api${cleanEndpoint}`;
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
    
    const response = await fetch(url, defaultOptions);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`✅ API Response: ${response.status}`, data);
    
    return data;
  } catch (error) {
    console.error(`❌ API Error: ${error.message}`);
    throw error;
  }
}

// Função para verificar saúde do backend (aceita 404 como válido)
export async function checkBackendHealth() {
  try {
    // Usa endpoint raiz que retorna {"detail":"Not Found"} - isso é esperado
    const response = await fetch('http://o.udstec.io/api/');
    
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


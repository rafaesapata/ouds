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

// Endpoints da API (todos via /api)
export const API_ENDPOINTS = {
  CHAT: '/api/chat',
  ROOT: '/api/',
  SESSIONS: '/api/sessions'
}

// Função para construir URL completa da API
export function buildApiUrl(endpoint) {
  // Se o endpoint já começa com /api, usa direto
  if (endpoint.startsWith('/api')) {
    return `http://o.udstec.io${endpoint}`;
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

// Função para verificar saúde do backend (usa endpoint raiz)
export async function checkBackendHealth() {
  try {
    // Usa endpoint raiz que existe
    const response = await fetch('http://o.udstec.io/api/');
    if (response.ok) {
      const data = await response.text();
      return { status: 'ok', data };
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    return { status: 'error', error: error.message };
  }
}

// Exportar configuração para debug
export { API_CONFIG };


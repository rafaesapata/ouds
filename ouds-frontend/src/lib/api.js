// OUDS - Configuração da API
// ===========================

// Configuração da URL base da API a partir das variáveis de ambiente
const API_CONFIG = {
  // URL base da API (definida no build time pelo Vite)
  BASE_URL: typeof __OUDS_API_URL__ !== 'undefined' ? __OUDS_API_URL__ : 'http://localhost:8000',
  
  // Timeout padrão para requisições
  TIMEOUT: 30000,
  
  // Headers padrão
  HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
}

// Endpoints da API
export const API_ENDPOINTS = {
  CHAT: '/api/chat',
  HEALTH: '/health',
  DOCS: '/docs',
  OPENAPI: '/openapi.json'
}

// Função para construir URL completa da API
export function buildApiUrl(endpoint) {
  const baseUrl = API_CONFIG.BASE_URL.replace(/\/$/, ''); // Remove trailing slash
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
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

// Função para verificar saúde do backend
export async function checkBackendHealth() {
  try {
    const data = await apiRequest(API_ENDPOINTS.HEALTH);
    return { status: 'ok', data };
  } catch (error) {
    return { status: 'error', error: error.message };
  }
}

// Exportar configuração para debug
export { API_CONFIG };


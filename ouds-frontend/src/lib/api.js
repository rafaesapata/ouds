// OUDS - Configuração da API
// ===========================

// Configuração da URL base da API a partir das variáveis de ambiente
const API_CONFIG = {
  // URL base da API (definida no build time pelo Vite)
  BASE_URL: typeof __OUDS_API_URL__ !== 'undefined' ? __OUDS_API_URL__ : 'http://localhost:8000',
  
  // Configurações específicas do backend
  BACKEND: {
    HOST: typeof __VITE_BACKEND_HOST__ !== 'undefined' ? __VITE_BACKEND_HOST__ : 'localhost',
    PORT: typeof __VITE_BACKEND_PORT__ !== 'undefined' ? __VITE_BACKEND_PORT__ : '8000',
    PROTOCOL: typeof __VITE_BACKEND_PROTOCOL__ !== 'undefined' ? __VITE_BACKEND_PROTOCOL__ : 'http'
  },
  
  // Versão do OUDS
  VERSION: typeof __OUDS_VERSION__ !== 'undefined' ? __OUDS_VERSION__ : '1.0.23'
};

// Construir URL completa do backend
API_CONFIG.FULL_URL = `${API_CONFIG.BACKEND.PROTOCOL}://${API_CONFIG.BACKEND.HOST}:${API_CONFIG.BACKEND.PORT}`;

// Endpoints da API
export const API_ENDPOINTS = {
  // Chat endpoints
  CHAT: '/api/chat',
  CHAT_STREAM: '/api/chat/stream',
  
  // Health check
  HEALTH: '/health',
  
  // Documentação
  DOCS: '/docs',
  OPENAPI: '/openapi.json',
  
  // Outros endpoints
  STATUS: '/api/status',
  VERSION: '/api/version'
};

// Função para construir URL completa
export const buildApiUrl = (endpoint) => {
  // Se estivermos usando proxy (desenvolvimento), usar path relativo
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return endpoint;
  }
  
  // Se estivermos em produção, usar URL completa
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

// Função para fazer requisições à API
export const apiRequest = async (endpoint, options = {}) => {
  const url = buildApiUrl(endpoint);
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  };
  
  try {
    console.log(`🌐 API Request: ${options.method || 'GET'} ${url}`);
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
};

// Função para verificar conectividade com o backend
export const checkBackendHealth = async () => {
  try {
    const response = await apiRequest(API_ENDPOINTS.HEALTH);
    return { status: 'ok', data: response };
  } catch (error) {
    return { status: 'error', error: error.message };
  }
};

// Exportar configuração para uso em outros componentes
export default API_CONFIG;

// Log da configuração no console (apenas em desenvolvimento)
if (import.meta.env.DEV) {
  console.log('🔧 OUDS API Configuration:', API_CONFIG);
  console.log('🌐 API Endpoints:', API_ENDPOINTS);
}


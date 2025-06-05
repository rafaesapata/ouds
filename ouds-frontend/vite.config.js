import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Carregar variáveis de ambiente
  const env = loadEnv(mode, process.cwd(), '')
  
  // Processar hosts permitidos do .env
  const allowedHosts = env.VITE_ALLOWED_HOSTS 
    ? env.VITE_ALLOWED_HOSTS.split(',').map(host => host.trim())
    : ['localhost', '127.0.0.1'];
  
  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
      extensions: ['.js', '.jsx', '.ts', '.tsx', '.json']
    },
    server: {
      host: env.OUDS_FRONTEND_HOST || '0.0.0.0',
      port: parseInt(env.OUDS_FRONTEND_PORT) || 5173,
      open: false, // CRÍTICO: Nunca abrir browser automaticamente (evita erro xdg-open ENOENT)
      strictPort: true, // Falha se a porta estiver ocupada
      allowedHosts: allowedHosts, // Hosts permitidos configurados via .env
      proxy: {
        // Proxy para API do backend
        '/api': {
          target: env.VITE_API_URL || env.OUDS_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, ''),
          configure: (proxy, options) => {
            proxy.on('error', (err, req, res) => {
              console.log('❌ Proxy error:', err.message);
            });
            proxy.on('proxyReq', (proxyReq, req, res) => {
              console.log('🔄 Proxying:', req.method, req.url, '→', options.target + req.url.replace('/api', ''));
            });
            proxy.on('proxyRes', (proxyRes, req, res) => {
              console.log('✅ Proxy response:', proxyRes.statusCode, req.url);
            });
          }
        },
        // Proxy direto para endpoints específicos do backend
        '/docs': {
          target: env.VITE_API_URL || env.OUDS_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false
        },
        '/openapi.json': {
          target: env.VITE_API_URL || env.OUDS_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false
        },
        '/health': {
          target: env.VITE_API_URL || env.OUDS_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false
        }
      }
    },
    preview: {
      host: env.OUDS_FRONTEND_HOST || 'localhost',
      port: parseInt(env.OUDS_FRONTEND_PORT) || 5173,
      open: false, // Também desabilitar no preview
      strictPort: true,
      allowedHosts: allowedHosts // Também aplicar no preview
    },
    define: {
      // Disponibilizar variáveis de ambiente para o frontend
      __OUDS_API_URL__: JSON.stringify(env.VITE_API_URL || env.OUDS_API_URL || 'http://localhost:8000'),
      __OUDS_VERSION__: JSON.stringify(env.OUDS_VERSION || '1.0.23'),
      __VITE_BACKEND_HOST__: JSON.stringify(env.VITE_BACKEND_HOST || 'localhost'),
      __VITE_BACKEND_PORT__: JSON.stringify(env.VITE_BACKEND_PORT || '8000'),
      __VITE_BACKEND_PROTOCOL__: JSON.stringify(env.VITE_BACKEND_PROTOCOL || 'http'),
      __VITE_ALLOWED_HOSTS__: JSON.stringify(allowedHosts),
    }
  }
})


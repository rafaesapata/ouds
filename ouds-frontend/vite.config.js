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
      port: parseInt(env.OUDS_FRONTEND_PORT) || 80,
      open: false, // CRÍTICO: Nunca abrir browser automaticamente (evita erro xdg-open ENOENT)
      strictPort: true, // Falha se a porta estiver ocupada
      allowedHosts: allowedHosts, // Hosts permitidos configurados via .env
      hmr: {
        port: parseInt(env.VITE_HMR_PORT) || 80,
        host: env.VITE_HMR_HOST || 'localhost',
        clientPort: parseInt(env.VITE_HMR_PORT) || 80
      },
      proxy: {
        // Proxy simples: /api → localhost:8000
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, ''),
          configure: (proxy, options) => {
            console.log('🔧 Proxy /api → http://localhost:8000');
            proxy.on('error', (err, req, res) => {
              console.log('❌ Proxy error:', err.message);
            });
            proxy.on('proxyReq', (proxyReq, req, res) => {
              console.log('🔄 Proxying:', req.method, req.url, '→', 'http://localhost:8000' + req.url.replace('/api', ''));
            });
            proxy.on('proxyRes', (proxyRes, req, res) => {
              console.log('✅ Proxy response:', proxyRes.statusCode, req.url);
            });
          }
        }
      }
    },
    preview: {
      host: env.OUDS_FRONTEND_HOST || 'localhost',
      port: parseInt(env.OUDS_FRONTEND_PORT) || 80,
      open: false, // Também desabilitar no preview
      strictPort: true,
      allowedHosts: allowedHosts // Também aplicar no preview
    },
    define: {
      // Disponibilizar variáveis de ambiente para o frontend
      __OUDS_VERSION__: JSON.stringify(env.OUDS_VERSION || '1.0.25'),
      __VITE_ALLOWED_HOSTS__: JSON.stringify(allowedHosts),
    }
  }
})


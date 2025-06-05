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
      __OUDS_API_URL__: JSON.stringify(env.VITE_API_URL || 'http://localhost:8000'),
      __OUDS_VERSION__: JSON.stringify(env.OUDS_VERSION || '1.0.24'),
      __VITE_ALLOWED_HOSTS__: JSON.stringify(allowedHosts),
    }
  }
})


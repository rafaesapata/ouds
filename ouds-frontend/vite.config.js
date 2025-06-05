import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Carregar variáveis de ambiente
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
      extensions: ['.js', '.jsx', '.ts', '.tsx', '.json']
    },
    server: {
      host: env.OUDS_FRONTEND_HOST || 'localhost',
      port: parseInt(env.OUDS_FRONTEND_PORT) || 5173,
      open: env.OUDS_FRONTEND_OPEN === 'true' || false,
    },
    preview: {
      host: env.OUDS_FRONTEND_HOST || 'localhost',
      port: parseInt(env.OUDS_FRONTEND_PORT) || 5173,
    },
    define: {
      // Disponibilizar variáveis de ambiente para o frontend
      __OUDS_API_URL__: JSON.stringify(env.OUDS_API_URL || 'http://localhost:8000'),
      __OUDS_VERSION__: JSON.stringify(env.OUDS_VERSION || '1.0.0'),
    }
  }
})


import { fileURLToPath, URL } from 'node:url'
import { Config } from '@en/config';
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  const usePythonAi = env.VITE_USE_PYTHON_AI === 'true'
  const aiPort = usePythonAi ? 3001 : 3002

  return {
    server: {
      port: Config.ports.web,
      proxy:{
        '/api':{
          target: `http://localhost:${Config.ports.server}`,
          changeOrigin: true
        },
        '/ai':{
          target: `http://localhost:${aiPort}`,
          changeOrigin: true
        },
        '/socket.io':{
          target: `http://localhost:${aiPort}`,
          changeOrigin: true,
          ws: true
        }
      }
    },
    plugins: [
      vue(),
      tailwindcss(),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    }
  }
})

import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'

const REQUIRED_ENV = ['VITE_API_BASE_URL']

const requireEnv = (): Plugin => ({
  name: 'require-env',
  configResolved(config) {
    const missing = REQUIRED_ENV.filter(key => !config.env[key])
    if (missing.length) {
      throw new Error(
        `Missing required environment variables:\n${missing.map(k => `  - ${k}`).join('\n')}\n` +
        `Check your .env.${config.mode} file or CI environment.`
      )
    }
  },
})

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), requireEnv()],
})

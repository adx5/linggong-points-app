import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// GitHub Pages 项目页子路径，必须与仓库名一致：/linggong-points-app/
// 如果以后换仓库名，改这里（或改 workflow 里的 --base）
const REPO_NAME = 'linggong-points-app'

export default defineConfig({
  base: `/${REPO_NAME}/`,
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
})

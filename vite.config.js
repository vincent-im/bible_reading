import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteSingleFile } from 'vite-plugin-singlefile'

// https://vitejs.dev/config/
// 기본 빌드: 일반 정적 자산 / `--mode standalone`: 모든 JS·CSS를 인라인한 단일 HTML
export default defineConfig(({ mode }) => {
  const standalone = mode === 'standalone'
  return {
    base: './', // 상대경로 → file:// 및 임의 하위경로 배포 모두 호환
    plugins: standalone ? [react(), viteSingleFile()] : [react()],
    server: {
      host: true,
      port: 5173,
    },
  }
})

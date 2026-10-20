import { createSSRApp } from 'vue'
import App from './App.vue'
import { APP_VERSION } from './common/version.js'

export function createApp() {
  const app = createSSRApp(App)
  app.config.globalProperties.$version = APP_VERSION
  return { app }
}

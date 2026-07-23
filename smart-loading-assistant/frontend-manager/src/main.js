import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import Tres from '@tresjs/core'
import './style.css'
import App from './App.vue'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(Tres)
app.mount('#app')

import { createRouter, createWebHistory } from 'vue-router'
import ManagerView from '../views/ManagerView.vue'
import OperatorView from '../views/OperatorView.vue'
import LoginView from '../views/LoginView.vue'
import { useAuthStore } from '../stores/useAuthStore'

const routes = [
  { path: '/', redirect: '/manager' },
  { path: '/login', component: LoginView },
  { path: '/manager', component: ManagerView, meta: { requiresAuth: true } },
  { path: '/operator', component: OperatorView, meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', redirect: '/manager' }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.token) {
    next('/login')
  } else {
    next()
  }
})

export default router

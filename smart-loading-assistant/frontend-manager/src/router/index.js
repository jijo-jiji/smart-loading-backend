import { createRouter, createWebHistory } from 'vue-router'
import ManagerView from '../views/ManagerView.vue'
import OperatorView from '../views/OperatorView.vue'

const routes = [
  { path: '/', redirect: '/manager' },
  { path: '/manager', component: ManagerView },
  { path: '/operator', component: OperatorView },
  { path: '/:pathMatch(.*)*', redirect: '/manager' }
]

export default createRouter({
  history: createWebHistory(),
  routes,
})

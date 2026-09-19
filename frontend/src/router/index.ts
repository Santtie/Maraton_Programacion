import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/registro',
      name: 'signup',
      component: () => import('../views/SignupView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      name: 'menu',
      component: () => import('../views/MainMenuView.vue'),
    },
    {
      path: '/consulta',
      name: 'consulta',
      component: () => import('../views/ChatView.vue'),
    },
    {
      path: '/peticion',
      name: 'peticion-tipos',
      component: () => import('../views/PeticionTiposView.vue'),
    },
    {
      path: '/peticion/:tipo',
      name: 'peticion-form',
      component: () => import('../views/PeticionFormView.vue'),
      props: true,
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.public && auth.isAuthenticated) {
    return { name: 'menu' }
  }
})

export default router

import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      meta: { public: true },
      component: () => import('@/pages/login/index.vue'),
    },
    {
      path: '/register',
      name: 'register',
      meta: { public: true },
      component: () => import('@/pages/register/index.vue'),
    },
    {
      path: '/',
      component: () => import('@/components/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'explain',
          component: () => import('@/pages/explain/index.vue'),
        },
        {
          path: 'history',
          name: 'history',
          component: () => import('@/pages/history/index.vue'),
        },
        {
          path: 'history/:id',
          name: 'history-detail',
          component: () => import('@/pages/history/detail.vue'),
        },
      ],
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const store = useUserStore()
  if (to.meta.requiresAuth && !store.isLoggedIn) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }
  if (to.meta.public && store.isLoggedIn && (to.name === 'login' || to.name === 'register')) {
    next({ name: 'explain' })
    return
  }
  next()
})

export default router

import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'
import AdminUsersView from '../views/AdminUsersView.vue'
import ItemsView from '../views/ItemsView.vue'
import { api } from '../components/api'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomeView
  },
  {
    path: '/reset',
    name: 'ResetPassword',
    component: ResetPasswordView
  },
  {
    path: '/wg_tools',
    name: 'WireguardTools',
    component: ItemsView,
    meta: { requiresUser: true }
  },
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: AdminUsersView,
    meta: { requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from) => {
  if (to.meta.requiresUser || to.meta.requiresAdmin){
    try {
      const response = await api.get('/api/users/me')
      const user = response.data
      if (user && user.level >= 3) {
        return true
      } else if (user) {
        if (to.meta.requiresAdmin){
            return { 
                path: '/', 
                query: {
                    requiredadmin: true
                }
            }
        }
        return true
      } else {
        // ここ来る？
        return { 
            path: '/', 
            query: {
                redirect: to.fullPath,
                requiredlogin: true
            }
        }
      }
    } catch (error) {
      return { 
        path: '/', 
        query: {
            redirect: to.fullPath,
            requiredlogin: true
        }
      }
    }
  } else {
    return true
  }
})

export default router
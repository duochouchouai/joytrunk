import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import OfficialLayout from '../layouts/OfficialLayout.vue'
import HomeView from '../views/HomeView.vue'
import ChatView from '../views/ChatView.vue'
import EmployeesView from '../views/EmployeesView.vue'
import EmployeeLogsView from '../views/EmployeeLogsView.vue'
import SettingsView from '../views/SettingsView.vue'
import OfficialLandingView from '../views/OfficialLandingView.vue'
import OfficialDocsView from '../views/OfficialDocsView.vue'
import OfficialPricingView from '../views/OfficialPricingView.vue'
import OfficialAboutView from '../views/OfficialAboutView.vue'
import OfficialPluginsView from '../views/OfficialPluginsView.vue'
import OfficialLoginView from '../views/OfficialLoginView.vue'
import OfficialImView from '../views/OfficialImView.vue'
import TokenView from '../views/TokenView.vue'

const routes = [
  {
    path: '/',
    component: OfficialLayout,
    children: [
      { path: '', name: 'official-home', component: OfficialLandingView },
      { path: 'plugins', name: 'official-plugins', component: OfficialPluginsView },
      { path: 'docs', name: 'official-docs', component: OfficialDocsView },
      { path: 'pricing', name: 'official-pricing', component: OfficialPricingView },
      { path: 'about', name: 'official-about', component: OfficialAboutView },
    ],
  },
  { path: '/login', name: 'login', component: OfficialLoginView, meta: { fullPage: true } },
  {
    path: '/app',
    component: MainLayout,
    children: [
      { path: '', redirect: '/app/im' },
      { path: 'im', name: 'official-im', component: OfficialImView },
      { path: 'token', name: 'token', component: TokenView },
      { path: 'overview', name: 'home', component: HomeView },
      { path: 'chat', name: 'chat', component: ChatView },
      { path: 'employees', name: 'employees', component: EmployeesView },
      { path: 'employees/:id/logs', name: 'employee-logs', component: EmployeeLogsView },
      { path: 'settings', name: 'settings', component: SettingsView },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = typeof localStorage !== 'undefined'
    ? (localStorage.getItem('joytrunk_token') || localStorage.getItem('joytrunk_owner_id'))
    : null
  if (to.path.startsWith('/app') && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router

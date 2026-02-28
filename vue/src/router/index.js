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
import OfficialLoginView from '../views/OfficialLoginView.vue'
import OfficialImView from '../views/OfficialImView.vue'

const routes = [
  {
    path: '/',
    component: OfficialLayout,
    children: [
      { path: '', name: 'official-home', component: OfficialLandingView },
      { path: 'docs', name: 'official-docs', component: OfficialDocsView },
      { path: 'pricing', name: 'official-pricing', component: OfficialPricingView },
    ],
  },
  { path: '/login', name: 'login', component: OfficialLoginView, meta: { fullPage: true } },
  {
    path: '/app',
    component: MainLayout,
    children: [
      { path: '', redirect: '/app/im' },
      { path: 'im', name: 'official-im', component: OfficialImView },
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

export default router

import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import HomeView from '../views/HomeView.vue'
import ChatView from '../views/ChatView.vue'
import EmployeesView from '../views/EmployeesView.vue'
import EmployeeLogsView from '../views/EmployeeLogsView.vue'
import EmployeeMemoryView from '../views/EmployeeMemoryView.vue'
import SettingsView from '../views/SettingsView.vue'
import LoginView from '../views/LoginView.vue'
import NotFoundView from '../views/NotFoundView.vue'

const routes = [
  { path: '/login', name: 'login', component: LoginView, meta: { fullPage: true } },
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', name: 'home', component: HomeView },
      { path: 'chat', name: 'chat', component: ChatView },
      { path: 'employees', name: 'employees', component: EmployeesView },
      { path: 'employees/:id/logs', name: 'employee-logs', component: EmployeeLogsView },
      { path: 'employees/:id/memory', name: 'employee-memory', component: EmployeeMemoryView },
      { path: 'settings', name: 'settings', component: SettingsView },
      { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

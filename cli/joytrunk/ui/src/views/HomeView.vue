<template>
  <div class="page">
    <h1 class="page-title">{{ t('home.title') }}</h1>
    <p v-if="!team" class="muted">{{ t('common.loading') }}</p>
    <div v-else class="cards">
      <div class="card">
        <h2 class="card-title">{{ t('home.currentTeam') }}</h2>
        <p class="owner-line"><strong>{{ t('home.owner') }}</strong> {{ team.owner.name }}</p>
        <p class="emp-count">{{ t('home.employeeCount', { n: team.employees.length }) }}</p>
        <ul v-if="team.employees.length" class="emp-list">
          <li v-for="e in team.employees" :key="e.id">
            {{ e.name }}
            <span v-if="e.persona || e.role" class="muted"> · {{ [e.persona, e.role].filter(Boolean).join(' / ') }}</span>
          </li>
        </ul>
        <p v-else class="muted">{{ t('home.noEmployees') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const team = inject('team')
</script>

<style scoped>
.page { max-width: 640px; }
.page-title { margin: 0 0 1.25rem; font-size: 1.5rem; font-weight: 600; color: var(--jt-text); }
.cards { display: flex; flex-direction: column; gap: 1rem; }
.card { background: var(--jt-card-bg); border-radius: var(--jt-radius); box-shadow: var(--jt-card-shadow); padding: 1.25rem 1.5rem; }
.card-title { margin: 0 0 0.75rem; font-size: 1rem; font-weight: 600; }
.owner-line { margin: 0 0 0.25rem; }
.emp-count { margin: 0 0 0.5rem; font-size: 0.875rem; color: var(--jt-text-muted); }
.emp-list { list-style: none; padding: 0; margin: 0; }
.emp-list li { padding: 0.35rem 0; font-size: 0.9375rem; }
.muted { color: var(--jt-text-muted); font-size: 0.875rem; }
</style>

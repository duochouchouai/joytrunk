<template>
  <div class="page">
    <h1 class="page-title">{{ t('employees.title') }}</h1>
    <div class="card">
      <h2 class="card-title">{{ t('employees.create') }}</h2>
      <form @submit.prevent="createEmp" class="form">
        <label class="field">
          <span class="field-label">{{ t('employees.name') }}</span>
          <input v-model="newName" type="text" class="field-input" :placeholder="t('employees.namePlaceholder')" required />
        </label>
        <label class="field">
          <span class="field-label">{{ t('employees.persona') }}</span>
          <input v-model="newPersona" type="text" class="field-input" :placeholder="t('employees.personaPlaceholder')" />
        </label>
        <label class="field">
          <span class="field-label">{{ t('employees.role') }}</span>
          <input v-model="newRole" type="text" class="field-input" :placeholder="t('employees.rolePlaceholder')" />
        </label>
        <label class="field">
          <span class="field-label">{{ t('employees.specialty') }}</span>
          <input v-model="newSpecialty" type="text" class="field-input" :placeholder="t('employees.specialtyPlaceholder')" />
        </label>
        <button type="submit" class="btn primary" :disabled="creating">{{ t('employees.createBtn') }}</button>
      </form>
      <p v-if="createError" class="error">{{ createError }}</p>
    </div>
    <div class="card">
      <h2 class="card-title">{{ t('employees.list') }}</h2>
      <p v-if="!team" class="muted">{{ t('common.loading') }}</p>
      <ul v-else-if="team.employees.length" class="emp-list">
        <li v-for="e in team.employees" :key="e.id">
          <span class="emp-name">{{ e.name }}</span>
          <span v-if="e.persona || e.role" class="muted">{{ [e.persona, e.role].filter(Boolean).join(' · ') }}</span>
        </li>
      </ul>
      <p v-else class="muted">{{ t('employees.noEmployees') }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../api'

const { t } = useI18n()
const team = inject('team')
const refreshTeam = inject('refreshTeam')
const newName = ref('')
const newPersona = ref('')
const newRole = ref('')
const newSpecialty = ref('')
const creating = ref(false)
const createError = ref('')

async function createEmp() {
  creating.value = true
  createError.value = ''
  try {
    await api.employees.create({ name: newName.value, persona: newPersona.value || undefined, role: newRole.value || undefined, specialty: newSpecialty.value || undefined })
    newName.value = ''
    newPersona.value = ''
    newRole.value = ''
    newSpecialty.value = ''
    await refreshTeam()
  } catch (e) {
    createError.value = e.message || t('employees.createFailed')
  } finally {
    creating.value = false
  }
}
</script>

<style scoped>
.page { max-width: 560px; }
.page-title { margin: 0 0 1.25rem; font-size: 1.5rem; font-weight: 600; }
.card { background: var(--jt-card-bg); border-radius: var(--jt-radius); box-shadow: var(--jt-card-shadow); padding: 1.25rem 1.5rem; margin-bottom: 1rem; }
.card-title { margin: 0 0 1rem; font-size: 1rem; font-weight: 600; }
.form { margin-bottom: 0.5rem; }
.field { display: block; margin-bottom: 0.75rem; }
.field-label { display: block; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.35rem; }
.field-input { width: 100%; max-width: 320px; padding: 0.5rem 0.75rem; border: 1px solid var(--jt-border); border-radius: 6px; font-size: 0.9375rem; }
.btn { padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.9375rem; cursor: pointer; border: none; }
.btn.primary { background: var(--jt-primary); color: #fff; }
.btn.primary:hover:not(:disabled) { background: var(--jt-primary-hover); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.error { color: #b91c1c; font-size: 0.875rem; margin-top: 0.5rem; }
.emp-list { list-style: none; padding: 0; margin: 0; }
.emp-list li { padding: 0.5rem 0; border-bottom: 1px solid var(--jt-border); display: flex; flex-direction: column; gap: 0.15rem; }
.emp-list li:last-child { border-bottom: none; }
.emp-name { font-weight: 500; }
.muted { font-size: 0.875rem; color: var(--jt-text-muted); }
</style>

<template>
  <div class="page" :class="{ 'page-mobile': isMobile }">
    <template v-if="isMobile">
      <MobileTitleBar :title="t('home.title')" />
      <div class="mobile-content">
        <template v-if="!team && !me">
          <p class="muted">{{ t('common.loading') }}</p>
        </template>
        <template v-else>
          <section class="section-card">
            <h2 class="section-title">{{ t('home.currentTeam') }}</h2>
            <div class="prefs-card">
              <div class="pref-row">
                <span class="pref-label">{{ t('home.owner') }}</span>
                <span class="pref-value">{{ ownerName }}</span>
              </div>
              <div class="pref-row">
                <span class="pref-label">{{ t('home.employeeCountLabel') }}</span>
                <span class="pref-value">{{ employeeCount }}</span>
              </div>
            </div>
            <ul v-if="employees.length" class="emp-list">
              <li v-for="e in employees" :key="e.id" class="emp-item">
                {{ e.name }}
                <span v-if="e.persona || e.role" class="muted"> · {{ [e.persona, e.role].filter(Boolean).join(' / ') }}</span>
              </li>
            </ul>
            <p v-else class="muted emp-empty">{{ t('home.noEmployees') }}</p>
          </section>
        </template>
      </div>
    </template>
    <template v-else>
      <h1 class="page-title">{{ t('home.title') }}</h1>
      <template v-if="!team && !me">
        <p class="muted">{{ t('common.loading') }}</p>
      </template>
      <template v-else>
        <section class="section-card">
          <h2 class="section-title">{{ t('home.currentTeam') }}</h2>
          <div class="prefs-card">
            <div class="pref-row">
              <span class="pref-label">{{ t('home.owner') }}</span>
              <span class="pref-value">{{ ownerName }}</span>
            </div>
            <div class="pref-row">
              <span class="pref-label">{{ t('home.employeeCountLabel') }}</span>
              <span class="pref-value">{{ employeeCount }}</span>
            </div>
          </div>
          <ul v-if="employees.length" class="emp-list">
            <li v-for="e in employees" :key="e.id" class="emp-item">
              {{ e.name }}
              <span v-if="e.persona || e.role" class="muted"> · {{ [e.persona, e.role].filter(Boolean).join(' / ') }}</span>
            </li>
          </ul>
          <p v-else class="muted emp-empty">{{ t('home.noEmployees') }}</p>
        </section>
      </template>
    </template>
  </div>
</template>

<script setup>
import { inject, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import MobileTitleBar from '../components/MobileTitleBar.vue'

const { t } = useI18n()
const team = inject('team', null)
const me = inject('me', null)
const isMobile = inject('isMobile', null)

const isOfficial = import.meta.env.VITE_APP_MODE === 'official'

const ownerName = computed(() => {
  if (isOfficial && me.value?.name) return me.value.name
  return team.value?.owner?.name ?? t('nav.owner')
})

const employees = computed(() => team.value?.employees ?? [])

const employeeCount = computed(() => employees.value.length)
</script>

<style scoped>
.page {
  max-width: 520px;
  margin: 0 auto;
  padding-bottom: 2rem;
}
.page-mobile {
  max-width: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  min-height: 100%;
  overflow: auto;
}
.page-mobile .mobile-content {
  flex: 1;
  padding: 1rem;
  padding-bottom: 2rem;
}
.page-title {
  margin: 0 0 1.75rem;
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--jt-text);
}

.section-card {
  padding: 1.75rem 1.5rem;
  margin-bottom: 1.5rem;
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.section-title {
  margin: 0 0 1rem;
  font-size: 1.0625rem;
  font-weight: 600;
  color: var(--jt-text);
}

.prefs-card {
  background: var(--jt-bg);
  border: 1px solid var(--jt-border);
  border-radius: 14px;
  overflow: visible;
  margin-bottom: 1rem;
}

.pref-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  gap: 1rem;
  border-bottom: 1px solid var(--jt-border);
}

.pref-row:last-child {
  border-bottom: none;
}

.pref-label {
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--jt-text);
}

.pref-value {
  font-size: 0.9375rem;
  color: var(--jt-text-muted, #64748b);
}

.emp-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.emp-item {
  padding: 0.5rem 0;
  font-size: 0.9375rem;
  color: var(--jt-text);
}

.emp-empty {
  margin: 0;
  font-size: 0.875rem;
}

.muted {
  color: var(--jt-text-muted, #64748b);
}
</style>

<template>
  <div v-if="show" class="im-create-conversation-overlay" @click.self="emit('close')">
    <div class="im-create-conversation">
      <h3 class="title">{{ t('official.im.newConversation') }}</h3>
      <p v-if="myUid != null" class="my-uid">{{ t('official.im.myUid') }}：<code>{{ myUid }}</code></p>
      <div class="tabs">
        <button type="button" class="tab" :class="{ active: mode === 'direct' }" @click="mode = 'direct'">
          {{ t('official.im.tabDirect') }}
        </button>
        <button type="button" class="tab" :class="{ active: mode === 'group' }" @click="mode = 'group'">
          {{ t('official.im.tabGroup') }}
        </button>
      </div>
      <form v-if="mode === 'direct'" @submit.prevent="submitDirect">
        <div class="field">
          <span class="field-label">{{ t('official.im.createPeerLabel') }}</span>
          <div class="direct-target-options">
            <label class="radio-wrap">
              <input v-model="directTarget" type="radio" value="uid" />
              <span>{{ t('official.im.directTargetUid') }}</span>
            </label>
            <label class="radio-wrap">
              <input v-model="directTarget" type="radio" value="joytrunk" />
              <span>{{ t('official.im.directTargetJoytrunk') }}</span>
            </label>
          </div>
        </div>
        <div v-if="directTarget === 'uid'" class="field">
          <label>{{ t('official.im.createPeerLabel') }}</label>
          <input v-model.trim="peerUid" type="text" :placeholder="t('official.im.createPeerPlaceholder')" />
        </div>
        <div v-else class="field">
          <label>{{ t('official.im.selectEmployeeLabel') }}</label>
          <select v-model="selectedEmployeeId" class="employee-select" :disabled="cliEmployeesLoading">
            <option value="">{{ t('official.im.selectEmployeePlaceholder') }}</option>
            <option v-for="emp in cliEmployees" :key="emp.id" :value="emp.id">{{ emp.name || emp.id }}</option>
          </select>
          <p v-if="!cliEmployeesLoading && cliEmployees.length === 0" class="hint">{{ t('official.im.noCliEmployees') }}</p>
        </div>
        <div v-if="error" class="error">{{ error }}</div>
        <div class="actions">
          <button type="button" class="btn secondary" @click="emit('close')">{{ t('common.cancel') }}</button>
          <button
            type="submit"
            class="btn primary"
            :disabled="!canSubmitDirect || submitting"
          >
            {{ submitting ? t('common.loading') : t('official.im.create') }}
          </button>
        </div>
      </form>
      <form v-else @submit.prevent="submitGroup">
        <div class="field">
          <label>{{ t('official.im.groupTitleLabel') }}</label>
          <input v-model.trim="groupTitle" type="text" :placeholder="t('official.im.groupTitlePlaceholder')" />
        </div>
        <div class="field">
          <label>{{ t('official.im.groupMemberUidsLabel') }}</label>
          <input v-model.trim="groupMemberUids" type="text" :placeholder="t('official.im.groupMemberUidsPlaceholder')" />
        </div>
        <div v-if="error" class="error">{{ error }}</div>
        <div class="actions">
          <button type="button" class="btn secondary" @click="emit('close')">{{ t('common.cancel') }}</button>
          <button type="submit" class="btn primary" :disabled="!parsedMemberUids.length || submitting">
            {{ submitting ? t('common.loading') : t('official.im.create') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { api } from '../../api';

const props = defineProps({
  show: { type: Boolean, default: false },
});

const emit = defineEmits(['close', 'created']);

const { t } = useI18n();
const mode = ref('direct');
const directTarget = ref('uid');
const peerUid = ref('');
const selectedEmployeeId = ref('');
const cliEmployees = ref([]);
const cliEmployeesLoading = ref(false);
const groupTitle = ref('');
const groupMemberUids = ref('');
const error = ref(null);
const submitting = ref(false);
const myUid = ref(null);

const canSubmitDirect = computed(() => {
  if (directTarget.value === 'uid') return !!peerUid.value?.trim();
  return !!selectedEmployeeId.value?.trim();
});

const parsedMemberUids = computed(() => {
  const raw = (groupMemberUids.value || '').split(/[\s,，]+/).map((s) => s.trim()).filter(Boolean);
  return [...new Set(raw)];
});

watch(
  () => props.show,
  async (v) => {
    if (v) {
      peerUid.value = '';
      directTarget.value = 'uid';
      selectedEmployeeId.value = '';
      groupTitle.value = '';
      groupMemberUids.value = '';
      error.value = null;
      myUid.value = null;
      cliEmployees.value = [];
      try {
        const me = await api.users.me();
        myUid.value = me?.uid != null ? String(me.uid) : null;
      } catch {
        myUid.value = null;
      }
      cliEmployeesLoading.value = true;
      try {
        const data = await api.cli.employees();
        cliEmployees.value = Array.isArray(data?.employees) ? data.employees : [];
      } catch {
        cliEmployees.value = [];
      } finally {
        cliEmployeesLoading.value = false;
      }
    }
  }
);

async function submitDirect() {
  if (!canSubmitDirect.value || submitting.value) return;
  submitting.value = true;
  error.value = null;
  try {
    const body = { type: 'direct' };
    if (directTarget.value === 'joytrunk') {
      body.peer_uid = 'joytrunk';
      body.employee_id = selectedEmployeeId.value.trim();
    } else {
      body.peer_uid = peerUid.value.trim();
    }
    const data = await api.im.createConversation(body);
    if (data.id) {
      emit('created', data.id);
      emit('close');
    }
  } catch (e) {
    error.value = e.message || t('official.im.createFailed');
  } finally {
    submitting.value = false;
  }
}

async function submitGroup() {
  const uids = parsedMemberUids.value;
  if (!uids.length || submitting.value) return;
  submitting.value = true;
  error.value = null;
  try {
    const data = await api.im.createConversation({
      type: 'group',
      title: groupTitle.value || undefined,
      member_uids: uids,
    });
    if (data.id) {
      emit('created', data.id);
      emit('close');
    }
  } catch (e) {
    error.value = e.message || t('official.im.createFailed');
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.im-create-conversation-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.im-create-conversation { background: var(--jt-bg); border-radius: 12px; padding: 1.5rem; min-width: 320px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); }
.title { margin: 0 0 1rem; font-size: 1.125rem; }
.my-uid { margin: 0 0 0.75rem; font-size: 0.875rem; color: var(--jt-text-muted); }
.my-uid code { font-family: ui-monospace, monospace; background: var(--jt-card-bg); padding: 0.2rem 0.4rem; border-radius: 4px; user-select: all; }
.tabs { display: flex; gap: 0.25rem; margin-bottom: 1rem; }
.tab { padding: 0.4rem 0.75rem; font-size: 0.875rem; border: 1px solid var(--jt-border); background: var(--jt-card-bg); color: var(--jt-text-muted); border-radius: 8px; cursor: pointer; }
.tab.active { background: var(--jt-primary); color: #fff; border-color: var(--jt-primary); }
.field { margin-bottom: 1rem; }
.field label { display: block; font-size: 0.875rem; margin-bottom: 0.35rem; color: var(--jt-text-muted); }
.field .field-label { display: block; font-size: 0.875rem; margin-bottom: 0.35rem; color: var(--jt-text-muted); }
.direct-target-options { display: flex; gap: 1rem; margin-bottom: 0.5rem; }
.radio-wrap { display: inline-flex; align-items: center; gap: 0.35rem; font-size: 0.9375rem; cursor: pointer; color: var(--jt-text); }
.radio-wrap input { margin: 0; }
.employee-select { width: 100%; padding: 0.5rem 0.75rem; border: 1px solid var(--jt-border); border-radius: 8px; font-size: 0.9375rem; background: var(--jt-bg); color: var(--jt-text); }
.hint { font-size: 0.8125rem; color: var(--jt-text-muted); margin: 0.35rem 0 0; }
.field input { width: 100%; padding: 0.5rem 0.75rem; border: 1px solid var(--jt-border); border-radius: 8px; font-size: 0.9375rem; }
.error { font-size: 0.875rem; color: var(--jt-error, #c00); margin-bottom: 0.5rem; }
.actions { display: flex; gap: 0.5rem; justify-content: flex-end; }
.btn { padding: 0.5rem 1rem; border-radius: 8px; font-size: 0.9375rem; cursor: pointer; border: none; }
.btn.primary { background: var(--jt-primary); color: #fff; }
.btn.secondary { background: var(--jt-card-bg); color: var(--jt-text); border: 1px solid var(--jt-border); }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
</style>

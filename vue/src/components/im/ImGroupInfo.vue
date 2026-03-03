<template>
  <div v-if="show" class="im-group-info-overlay" @click.self="emit('close')">
    <div class="im-group-info">
      <h3 class="title">{{ conversation?.title || t('official.im.groupInfoTitle') }}</h3>
      <div v-if="loading" class="muted">{{ t('common.loading') }}</div>
      <template v-else>
        <div v-if="canManage" class="form-section">
          <label class="label">{{ t('official.im.editGroupName') }}</label>
          <input v-model.trim="editTitle" type="text" class="input" />
          <label class="label">{{ t('official.im.editGroupAvatar') }}</label>
          <div class="avatar-row">
            <div v-if="displayAvatarUrl" class="avatar-wrap">
              <img :src="displayAvatarUrl" alt="" class="avatar-img" @error="onAvatarImgError" />
            </div>
            <div v-else class="avatar-placeholder">群</div>
            <div class="avatar-input-wrap">
              <input
                v-model.trim="editAvatarUrl"
                type="text"
                class="input"
                :placeholder="t('official.im.groupAvatarPlaceholder')"
              />
              <button type="button" class="btn-link btn-clear-avatar" @click="editAvatarUrl = ''">{{ t('official.im.groupAvatarClear') }}</button>
            </div>
          </div>
          <label class="label">{{ t('official.im.editAnnouncement') }}</label>
          <textarea v-model.trim="editAnnouncement" class="textarea" rows="2"></textarea>
          <button type="button" class="btn primary" @click="doSave">{{ t('official.im.save') }}</button>
        </div>
        <div v-if="canManage" class="form-section">
          <label class="label">{{ t('official.im.addMembers') }}</label>
          <input v-model.trim="addMemberUids" type="text" class="input" :placeholder="t('official.im.addMembersPlaceholder')" />
          <button type="button" class="btn secondary" :disabled="!parsedAddUids.length" @click="doAddMembers">
            {{ t('official.im.addMembers') }}
          </button>
        </div>
        <ul class="member-list">
          <li v-for="p in participants" :key="p.user_id" class="member-item">
            <span class="member-name">{{ p.name || ('UID ' + (p.uid || p.user_id)) }}</span>
            <span class="member-meta">
              <span class="member-role">{{ roleLabel(p.role) }}</span>
              <span v-if="isMuted(p)" class="muted-tag">{{ t('official.im.mutedLabel') }}</span>
              <button
                v-if="canManage && Number(p.user_id) !== Number(currentUserId) && p.role !== 'owner'"
                type="button"
                class="btn-link"
                @click="doRemove(p.user_id)"
              >
                {{ t('official.im.removeMember') }}
              </button>
              <template v-if="canManage && Number(p.user_id) !== Number(currentUserId) && p.role !== 'owner'">
                <button v-if="myRole === 'owner'" type="button" class="btn-link" @click="doSetRole(p, p.role === 'admin' ? 'member' : 'admin')">
                  {{ p.role === 'admin' ? t('official.im.cancelAdmin') : t('official.im.setAdmin') }}
                </button>
                <button v-if="myRole === 'owner'" type="button" class="btn-link" @click="doTransfer(p)">
                  {{ t('official.im.transferOwner') }}
                </button>
                <button v-if="!isMuted(p)" type="button" class="btn-link" @click="doMute(p, '1h')">{{ t('official.im.mute') }} 1h</button>
                <button v-if="!isMuted(p)" type="button" class="btn-link" @click="doMute(p, '24h')">24h</button>
                <button v-if="!isMuted(p)" type="button" class="btn-link" @click="doMute(p, 'forever')">{{ t('official.im.muteForever') }}</button>
                <button v-if="!isMuted(p)" type="button" class="btn-link" @click="openCustomMute(p)">{{ t('official.im.muteCustom') }}</button>
                <button v-if="isMuted(p)" type="button" class="btn-link" @click="doMute(p, null)">{{ t('official.im.unmute') }}</button>
              </template>
            </span>
            <div v-if="customMuteTargetUserId === p.user_id" class="custom-mute-form">
              <input
                v-model.number="customMuteValue"
                type="number"
                min="1"
                class="input custom-mute-input"
                :placeholder="t('official.im.muteCustomPlaceholder')"
              />
              <select v-model="customMuteUnit" class="select custom-mute-unit">
                <option value="minutes">{{ t('official.im.muteUnitMinutes') }}</option>
                <option value="hours">{{ t('official.im.muteUnitHours') }}</option>
                <option value="days">{{ t('official.im.muteUnitDays') }}</option>
              </select>
              <button type="button" class="btn primary btn-sm" @click="submitCustomMute(p)">
                {{ t('official.im.mute') }}
              </button>
            </div>
          </li>
        </ul>
        <div class="actions">
          <button v-if="myRole && myRole !== 'owner'" type="button" class="btn secondary" @click="doLeave">
            {{ t('official.im.leaveGroup') }}
          </button>
          <button v-if="myRole === 'owner'" type="button" class="btn danger" @click="doDismiss">
            {{ t('official.im.dismissGroup') }}
          </button>
          <button type="button" class="btn secondary" @click="emit('close')">{{ t('common.cancel') }}</button>
        </div>
        <div v-if="error" class="error">{{ error }}</div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { api } from '../../api';
import { validateImageUrl } from '../../utils/im';

const props = defineProps({
  show: { type: Boolean, default: false },
  conversationId: { type: [Number, String], default: null },
  conversation: { type: Object, default: null },
  currentUserId: { type: [Number, String], default: null },
});

const emit = defineEmits(['close', 'leave', 'dismiss', 'updated']);

const { t } = useI18n();
const participants = ref([]);
const myRole = ref(null);
const loading = ref(false);
const error = ref(null);
const addMemberUids = ref('');
const editTitle = ref('');
const editAnnouncement = ref('');
const editAvatarUrl = ref('');
const initialAvatarUrl = ref('');
const avatarImgError = ref(false);
const customMuteTargetUserId = ref(null);
const customMuteValue = ref('');
const customMuteUnit = ref('minutes');

const effectiveAvatarUrl = computed(() => (editAvatarUrl.value || props.conversation?.avatar_url || '').trim());
const displayAvatarUrl = computed(() => {
  if (!effectiveAvatarUrl.value || !validateImageUrl(effectiveAvatarUrl.value) || avatarImgError.value) return '';
  return effectiveAvatarUrl.value;
});

const canManage = computed(() => myRole.value === 'owner' || myRole.value === 'admin');
const parsedAddUids = computed(() => {
  const raw = (addMemberUids.value || '').split(/[\s,，]+/).map((s) => s.trim()).filter(Boolean);
  return [...new Set(raw)];
});

watch(
  () => props.conversation,
  (c) => {
    editTitle.value = c?.title ?? '';
    editAnnouncement.value = c?.announcement ?? '';
    const url = c?.avatar_url ?? '';
    editAvatarUrl.value = url;
    initialAvatarUrl.value = url;
    avatarImgError.value = false;
  },
  { immediate: true }
);

watch(
  () => props.show,
  (visible) => {
    if (!visible) {
      customMuteTargetUserId.value = null;
      customMuteValue.value = '';
      editAvatarUrl.value = initialAvatarUrl.value;
      avatarImgError.value = false;
    }
  }
);

function onAvatarImgError() {
  avatarImgError.value = true;
}

function roleLabel(role) {
  if (role === 'owner') return t('official.im.roleOwner');
  if (role === 'admin') return t('official.im.roleAdmin');
  return t('official.im.roleMember');
}

function isMuted(p) {
  if (!p.muted_until) return false;
  return new Date(p.muted_until).getTime() > Date.now();
}

watch(
  () => [props.show, props.conversationId],
  async ([show, id]) => {
    if (!show || !id) {
      participants.value = [];
      myRole.value = null;
      error.value = null;
      return;
    }
    loading.value = true;
    error.value = null;
    try {
      const list = await api.im.participants(id);
      participants.value = Array.isArray(list) ? list : [];
      const me = participants.value.find((p) => Number(p.user_id) === Number(props.currentUserId));
      myRole.value = me ? me.role : null;
      editTitle.value = props.conversation?.title ?? '';
      editAnnouncement.value = props.conversation?.announcement ?? '';
    } catch (e) {
      error.value = e.message || t('official.im.createFailed');
      participants.value = [];
      myRole.value = null;
    } finally {
      loading.value = false;
    }
  },
  { immediate: true }
);

async function doLeave() {
  if (!props.conversationId) return;
  error.value = null;
  try {
    await api.im.leave(props.conversationId);
    emit('leave');
    emit('close');
  } catch (e) {
    error.value = e.message || t('official.im.createFailed');
  }
}

async function doDismiss() {
  if (!props.conversationId) return;
  if (!confirm(t('official.im.dismissGroup') + '？')) return;
  error.value = null;
  try {
    await api.im.dismiss(props.conversationId);
    emit('dismiss');
    emit('close');
  } catch (e) {
    error.value = e.message || t('official.im.createFailed');
  }
}

async function doAddMembers() {
  if (!props.conversationId || !parsedAddUids.value.length) return;
  error.value = null;
  try {
    await api.im.addParticipants(props.conversationId, { member_uids: parsedAddUids.value });
    addMemberUids.value = '';
    const list = await api.im.participants(props.conversationId);
    participants.value = Array.isArray(list) ? list : [];
    emit('updated');
  } catch (e) {
    error.value = e.message || t('official.im.createFailed');
  }
}

async function doRemove(userId) {
  if (!props.conversationId) return;
  error.value = null;
  try {
    await api.im.removeParticipant(props.conversationId, userId);
    const list = await api.im.participants(props.conversationId);
    participants.value = Array.isArray(list) ? list : [];
    emit('updated');
  } catch (e) {
    error.value = e.message || t('official.im.createFailed');
  }
}

async function doSave() {
  if (!props.conversationId) return;
  error.value = null;
  const payload = {
    title: editTitle.value || undefined,
    announcement: editAnnouncement.value !== undefined ? editAnnouncement.value : undefined,
  };
  if (editAvatarUrl.value.trim() !== initialAvatarUrl.value.trim()) {
    payload.avatar_url = editAvatarUrl.value.trim() === '' ? null : editAvatarUrl.value.trim();
  }
  try {
    await api.im.updateConversation(props.conversationId, payload);
    initialAvatarUrl.value = editAvatarUrl.value.trim();
    emit('updated');
  } catch (e) {
    error.value = e.message || t('official.im.createFailed');
  }
}

async function doSetRole(p, role) {
  if (!props.conversationId) return;
  error.value = null;
  try {
    await api.im.updateParticipant(props.conversationId, p.user_id, { role });
    const list = await api.im.participants(props.conversationId);
    participants.value = Array.isArray(list) ? list : [];
    emit('updated');
  } catch (e) {
    error.value = e.message || t('official.im.createFailed');
  }
}

async function doTransfer(p) {
  if (!props.conversationId || !confirm(t('official.im.transferOwner') + '？')) return;
  error.value = null;
  try {
    await api.im.updateParticipant(props.conversationId, p.user_id, { role: 'owner' });
    const list = await api.im.participants(props.conversationId);
    participants.value = Array.isArray(list) ? list : [];
    const me = participants.value.find((x) => Number(x.user_id) === Number(props.currentUserId));
    myRole.value = me ? me.role : null;
    emit('updated');
  } catch (e) {
    error.value = e.message || t('official.im.createFailed');
  }
}

const MAX_MUTE_DAYS = 365;

function muteUntil(duration) {
  if (!duration) return null;
  const d = new Date();
  if (duration === '1h') {
    d.setHours(d.getHours() + 1);
    return d.toISOString();
  }
  if (duration === '24h') {
    d.setHours(d.getHours() + 24);
    return d.toISOString();
  }
  if (duration === 'forever') {
    d.setFullYear(d.getFullYear() + 100);
    return d.toISOString();
  }
  if (duration && typeof duration === 'object' && 'value' in duration && 'unit' in duration) {
    const value = Number(duration.value);
    if (!Number.isInteger(value) || value < 1) return null;
    const unit = duration.unit;
    let minutes = 0;
    if (unit === 'minutes') minutes = value;
    else if (unit === 'hours') minutes = value * 60;
    else if (unit === 'days') minutes = value * 24 * 60;
    else return null;
    if (minutes > MAX_MUTE_DAYS * 24 * 60) return null;
    d.setMinutes(d.getMinutes() + minutes);
    return d.toISOString();
  }
  return null;
}

function openCustomMute(p) {
  customMuteTargetUserId.value = p.user_id;
  customMuteValue.value = '';
  customMuteUnit.value = 'minutes';
  error.value = null;
}

function validateCustomMute() {
  const raw = customMuteValue.value;
  const num = typeof raw === 'string' ? parseInt(raw, 10) : Number(raw);
  if (!Number.isInteger(num) || num < 1) return false;
  const unit = customMuteUnit.value;
  let minutes = 0;
  if (unit === 'minutes') minutes = num;
  else if (unit === 'hours') minutes = num * 60;
  else if (unit === 'days') minutes = num * 24 * 60;
  else return false;
  return minutes <= MAX_MUTE_DAYS * 24 * 60;
}

async function submitCustomMute(p) {
  if (!validateCustomMute()) {
    error.value = t('official.im.muteCustomInvalid');
    return;
  }
  const value = typeof customMuteValue.value === 'string' ? parseInt(customMuteValue.value, 10) : customMuteValue.value;
  await doMute(p, { value, unit: customMuteUnit.value });
  customMuteTargetUserId.value = null;
  customMuteValue.value = '';
}

async function doMute(p, duration) {
  if (!props.conversationId) return;
  error.value = null;
  const until = muteUntil(duration);
  if (typeof duration === 'object' && duration !== null && 'unit' in duration && until === null) {
    error.value = t('official.im.muteCustomInvalid');
    return;
  }
  try {
    await api.im.updateParticipant(props.conversationId, p.user_id, { muted_until: until });
    const list = await api.im.participants(props.conversationId);
    participants.value = Array.isArray(list) ? list : [];
    emit('updated');
  } catch (e) {
    error.value = e.message || t('official.im.createFailed');
  }
}
</script>

<style scoped>
.im-group-info-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.im-group-info { background: var(--jt-bg); border-radius: 12px; padding: 1.5rem; min-width: 280px; max-width: 90vw; max-height: 80vh; overflow: auto; box-shadow: 0 4px 20px rgba(0,0,0,0.15); }
.title { margin: 0 0 1rem; font-size: 1.125rem; }
.member-list { list-style: none; padding: 0; margin: 0 0 1rem; max-height: 240px; overflow: auto; }
.member-item { display: flex; justify-content: space-between; align-items: center; padding: 0.4rem 0; border-bottom: 1px solid var(--jt-border); font-size: 0.9375rem; }
.member-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.member-meta { flex-shrink: 0; margin-left: 0.5rem; display: flex; align-items: center; gap: 0.35rem; }
.member-role { font-size: 0.75rem; color: var(--jt-text-muted); }
.muted-tag { font-size: 0.7rem; color: var(--jt-error, #c00); margin-left: 0.25rem; }
.btn-link { background: none; border: none; cursor: pointer; font-size: 0.75rem; color: var(--jt-primary); padding: 0; }
.btn-link:hover { text-decoration: underline; }
.form-section { margin-bottom: 1rem; }
.form-section .label { display: block; font-size: 0.8125rem; margin-bottom: 0.25rem; color: var(--jt-text-muted); }
.form-section .input, .form-section .textarea { width: 100%; padding: 0.4rem 0.5rem; border: 1px solid var(--jt-border); border-radius: 6px; font-size: 0.9375rem; margin-bottom: 0.5rem; }
.form-section .textarea { resize: vertical; }
.btn.primary { background: var(--jt-primary); color: #fff; }
.actions { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.btn { padding: 0.5rem 1rem; border-radius: 8px; font-size: 0.9375rem; cursor: pointer; border: none; }
.btn.secondary { background: var(--jt-card-bg); color: var(--jt-text); border: 1px solid var(--jt-border); }
.btn.danger { background: var(--jt-error, #c00); color: #fff; }
.error { font-size: 0.875rem; color: var(--jt-error, #c00); margin-top: 0.5rem; }
.muted { font-size: 0.875rem; color: var(--jt-text-muted); }
.custom-mute-form { display: flex; align-items: center; gap: 0.35rem; margin-top: 0.35rem; flex-wrap: wrap; }
.custom-mute-input { width: 4rem; min-width: 4rem; padding: 0.25rem 0.35rem; font-size: 0.8125rem; }
.custom-mute-unit { padding: 0.25rem 0.35rem; font-size: 0.8125rem; border: 1px solid var(--jt-border); border-radius: 6px; background: var(--jt-bg); }
.btn-sm { padding: 0.25rem 0.5rem; font-size: 0.8125rem; }
.avatar-row { display: flex; align-items: flex-start; gap: 0.75rem; margin-bottom: 0.5rem; }
.avatar-wrap, .avatar-placeholder { flex-shrink: 0; width: var(--jt-avatar-size-sm, 2.5rem); height: var(--jt-avatar-size-sm, 2.5rem); border-radius: var(--jt-avatar-radius, 8px); overflow: hidden; }
.avatar-placeholder { background: var(--jt-border, #e5e7eb); color: #6b7280; font-size: 16px; display: flex; align-items: center; justify-content: center; }
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-input-wrap { flex: 1; min-width: 0; }
.btn-clear-avatar { font-size: 0.8125rem; margin-top: 0.25rem; }
</style>

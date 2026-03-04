<template>
  <section class="im-chat-pane">
    <template v-if="conversationId">
      <div v-if="conversation" class="chat-header">
        <div class="chat-header-inner">
          <button v-if="showBack" type="button" class="chat-back" :aria-label="t('common.back')" @click="$emit('back')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          </button>
          <span class="chat-title">{{ conversation.title || ('会话 ' + conversationId) }}</span>
          <button v-if="conversation.type === 'group'" type="button" class="btn-group-info" @click="$emit('openGroupInfo')">
            {{ t('official.im.groupInfoTitle') }}
          </button>
        </div>
      </div>
      <div class="messages-wrap" ref="scrollRef" @scroll="onScroll">
        <div v-if="loadingMore" class="load-more">
          <span class="muted">{{ t('common.loading') }}</span>
        </div>
        <button
          v-else-if="(nextCursor || hasMore) && !loading"
          type="button"
          class="btn-load-more"
          :disabled="loadingMore"
          @click="loadMore"
        >
          {{ t('official.im.loadMore') }}
        </button>
        <div v-else-if="!hasMore && messages.length > 0" class="all-loaded muted">
          {{ t('official.im.allLoaded') }}
        </div>
        <div v-if="loading && messages.length === 0" class="muted center">{{ t('common.loading') }}</div>
        <div v-else class="messages">
          <ImMessageBubble
            v-for="m in messages"
            :key="m.id"
            :message="m"
            :is-self="currentUserId != null && m.sender_id === currentUserId"
            :avatar-url="getSenderAvatar(m).avatarUrl"
            :initial="getSenderAvatar(m).initial"
          />
        </div>
      </div>
      <form @submit.prevent="sendMessage" class="input-row">
        <input
          ref="fileInputRef"
          type="file"
          accept="image/*"
          class="input-file-hidden"
          @change="onImageFileChange"
        />
        <button
          type="button"
          class="btn-tool"
          :disabled="sending || isMuted"
          :title="t('official.im.sendImage')"
          @click="triggerImageInput"
        >
          <svg class="btn-tool-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
        </button>
        <div class="input-wrap">
          <input
            ref="inputRef"
            v-model="inputText"
            type="text"
            class="input"
            :class="{ 'input-muted': isMuted }"
            :placeholder="isMuted ? t('official.im.mutedHint') : t('official.im.inputPlaceholder')"
            :disabled="sending || isMuted"
            @input="onInput"
            @keydown="onInputKeydown"
          />
          <div
            v-if="showMentionPicker && conversation?.type === 'group'"
            ref="pickerRef"
            class="mention-picker"
            role="listbox"
          >
            <button
              v-for="(opt, idx) in filteredMentionOptions"
              :key="opt.type === 'everyone' ? 'everyone' : opt.member.user_id"
              type="button"
              class="mention-item"
              :class="{ 'mention-item-active': idx === selectedMentionIndex }"
              role="option"
              @click="chooseMention(opt)"
            >
              {{ opt.type === 'everyone' ? t('official.im.mentionEveryone') : getMemberDisplayName(opt.member) }}
            </button>
            <div v-if="filteredMentionOptions.length === 0" class="mention-empty">{{ t('official.im.mentionNoMatch') }}</div>
          </div>
        </div>
        <button type="submit" class="btn-send" :disabled="sending || !inputText.trim() || isMuted">
          <span v-if="sending" class="btn-send-loading"></span>
          <span v-else>{{ t('official.im.send') }}</span>
        </button>
      </form>
      <div v-if="isMuted" class="muted-hint">{{ mutedHintText }}</div>
      <div v-if="sendError" class="send-error">
        {{ t('official.im.sendFailed') }}
        <button type="button" class="btn-retry" @click="sendError = null">×</button>
      </div>
    </template>
    <div v-else class="empty">
      <div class="empty-card">
        <span class="empty-icon">💬</span>
        <p class="empty-text">{{ t('official.im.noConversations') }}</p>
        <p class="empty-hint">{{ t('official.im.emptyHint') }}</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, watch, nextTick, computed, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { api } from '../../api';
import { isMuted as isMutedUtil } from '../../utils/im';
import ImMessageBubble from './ImMessageBubble.vue';

const props = defineProps({
  conversationId: { type: [Number, String], default: null },
  currentUserId: { type: [Number, String], default: null },
  conversation: { type: Object, default: null },
  mockMessages: { type: Array, default: null },
  me: { type: Object, default: null },
  senderMap: { type: Object, default: () => ({}) },
  /** 移动端时在头部显示返回按钮 */
  showBack: { type: Boolean, default: false },
});

const emit = defineEmits(['read', 'openGroupInfo', 'back']);

const { t } = useI18n();
const scrollRef = ref(null);
const messages = ref([]);
const nextCursor = ref(undefined);
const hasMore = ref(true);
const loading = ref(false);
const loadingMore = ref(false);
const sending = ref(false);
const inputText = ref('');
const sendError = ref(null);
const currentUserMutedUntil = ref(null);
const groupParticipants = ref([]);
const showMentionPicker = ref(false);
const mentionStart = ref(0);
const filterQuery = ref('');
const selectedMentionIndex = ref(0);
const pickerRef = ref(null);
const inputRef = ref(null);
const fileInputRef = ref(null);
let mutedCheckTimer = null;

const MENTION_EVERYONE = '@所有人';
const MENTION_EVERYONE_LABEL = '所有人';

function getMemberDisplayName(p) {
  return p?.name || ('UID ' + (p?.uid ?? p?.user_id ?? ''));
}

/** 根据消息发送者返回头像 URL 与首字（用于气泡旁头像） */
function getSenderAvatar(message) {
  const isSelf = props.currentUserId != null && message.sender_id === props.currentUserId;
  if (isSelf) {
    return {
      avatarUrl: props.me?.avatar_url ?? null,
      initial: (props.me?.name || '我').trim().charAt(0) || '我',
    };
  }
  const fromMap = props.senderMap?.[message.sender_id];
  if (fromMap) {
    return {
      avatarUrl: fromMap.avatar_url ?? null,
      initial: (fromMap.name || '?').trim().charAt(0) || '?',
    };
  }
  const fromParticipant = props.groupParticipants?.find(
    (p) => Number(p.user_id) === Number(message.sender_id)
  );
  if (fromParticipant) {
    return {
      avatarUrl: fromParticipant.avatar_url ?? null,
      initial: (getMemberDisplayName(fromParticipant) || '?').trim().charAt(0) || '?',
    };
  }
  return { avatarUrl: null, initial: '?' };
}

/** 从光标前找到最近一个 @ 的起始下标；若 @ 与光标之间有空格则返回 -1 */
function getMentionContextStart(value, cursor) {
  if (!value || cursor <= 0) return -1;
  let i = cursor - 1;
  while (i >= 0 && value[i] !== '@') {
    if (value[i] === ' ' || value[i] === '\n') return -1;
    i--;
  }
  return i >= 0 ? i : -1;
}

function onInput() {
  const el = inputRef.value;
  if (!el || props.conversation?.type !== 'group') {
    showMentionPicker.value = false;
    return;
  }
  const raw = inputText.value;
  const cursor = el.selectionStart ?? raw.length;
  const start = getMentionContextStart(raw, cursor);
  if (start === -1) {
    showMentionPicker.value = false;
    return;
  }
  mentionStart.value = start;
  filterQuery.value = raw.slice(start + 1, cursor);
  showMentionPicker.value = true;
  selectedMentionIndex.value = 0;
}

const filteredMentionOptions = computed(() => {
  const q = (filterQuery.value || '').trim().toLowerCase();
  const options = [];
  if (MENTION_EVERYONE_LABEL.includes(q) || q === '') {
    options.push({ type: 'everyone' });
  }
  const nameMatches = groupParticipants.value.filter((p) => {
    const name = getMemberDisplayName(p);
    return !q || name.toLowerCase().includes(q);
  });
  nameMatches.forEach((member) => options.push({ type: 'member', member }));
  return options;
});

watch(showMentionPicker, (open) => {
  if (open) selectedMentionIndex.value = 0;
});

watch(filteredMentionOptions, (opts) => {
  const max = Math.max(0, opts.length - 1);
  if (selectedMentionIndex.value > max) selectedMentionIndex.value = max;
}, { flush: 'sync' });

watch(selectedMentionIndex, (idx) => {
  nextTick(() => {
    const picker = pickerRef.value;
    const btn = picker?.querySelectorAll('.mention-item')[idx];
    if (btn) btn.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  });
}, { flush: 'post' });

function onInputKeydown(ev) {
  if (!showMentionPicker.value || filteredMentionOptions.value.length === 0) return;
  const opts = filteredMentionOptions.value;
  if (ev.key === 'ArrowDown') {
    ev.preventDefault();
    selectedMentionIndex.value = (selectedMentionIndex.value + 1) % opts.length;
    return;
  }
  if (ev.key === 'ArrowUp') {
    ev.preventDefault();
    selectedMentionIndex.value = (selectedMentionIndex.value - 1 + opts.length) % opts.length;
    return;
  }
  if (ev.key === 'Enter') {
    ev.preventDefault();
    chooseMention(opts[selectedMentionIndex.value]);
    return;
  }
  if (ev.key === 'Escape') {
    ev.preventDefault();
    showMentionPicker.value = false;
  }
}

function chooseMention(opt) {
  const el = inputRef.value;
  const raw = inputText.value;
  const end = el ? (el.selectionEnd ?? raw.length) : raw.length;
  const start = mentionStart.value;
  const text = opt.type === 'everyone' ? MENTION_EVERYONE : '@' + getMemberDisplayName(opt.member);
  inputText.value = raw.slice(0, start) + text + ' ' + raw.slice(end);
  showMentionPicker.value = false;
  nextTick(() => {
    if (el) {
      el.focus();
      const pos = start + text.length + 1;
      el.setSelectionRange(pos, pos);
    }
  });
}

const isMuted = computed(() => isMutedUtil(currentUserMutedUntil.value));

const mutedHintText = computed(() => {
  if (!currentUserMutedUntil.value) return t('official.im.mutedHint');
  const until = new Date(currentUserMutedUntil.value);
  if (until.getTime() <= Date.now()) return t('official.im.mutedHint');
  return t('official.im.mutedHintUntil', {
    time: until.toLocaleString(undefined, { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
  });
});

const scrollTops = new Map();

const DEFAULT_LIMIT = 20;

async function loadMessages(append = false) {
  if (!props.conversationId) return;
    if (append) {
      if (!nextCursor.value || loadingMore.value) return;
      loadingMore.value = true;
  } else {
    loading.value = true;
  }
  sendError.value = null;
  try {
    const params = { limit: DEFAULT_LIMIT };
    if (append && nextCursor.value) params.before = nextCursor.value;
    const data = await api.im.messages(props.conversationId, params);
    const items = Array.isArray(data.items) ? data.items : [];
    const nextHasMore = data.has_more != null ? !!data.has_more : (data.next_cursor != null);
    if (append) {
      const oldHeight = scrollRef.value?.scrollHeight ?? 0;
      const oldTop = scrollRef.value?.scrollTop ?? 0;
      messages.value = [...items, ...messages.value];
      nextCursor.value = data.next_cursor ?? null;
      hasMore.value = nextHasMore;
      await nextTick();
      if (scrollRef.value && items.length > 0) {
        const newHeight = scrollRef.value.scrollHeight;
        scrollRef.value.scrollTop = newHeight - oldHeight + oldTop;
      }
    } else {
      messages.value = items;
      nextCursor.value = data.next_cursor ?? null;
      hasMore.value = nextHasMore;
      await nextTick();
      if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight;
      const latestId = data.latest_msg_id != null ? data.latest_msg_id : (items.length ? Math.max(...items.map((m) => m.id)) : null);
      if (latestId != null) {
        api.im.markRead(props.conversationId, { last_read_msg_id: latestId }).then(() => emit('read')).catch(() => {});
      }
    }
  } catch {
    if (!append) messages.value = [];
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
}

function loadMore() {
  loadMessages(true);
}

function onScroll() {
  if (!props.conversationId || !scrollRef.value) return;
  scrollTops.set(props.conversationId, scrollRef.value.scrollTop);
}

function triggerImageInput() {
  fileInputRef.value?.click();
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function onImageFileChange(e) {
  const file = e.target?.files?.[0];
  e.target.value = '';
  if (!file || !file.type.startsWith('image/') || !props.conversationId || sending.value || isMuted.value) return;
  sending.value = true;
  sendError.value = null;
  const isMock = Array.isArray(props.mockMessages);
  try {
    const dataUrl = await readFileAsDataUrl(file);
    if (isMock) {
      const newMsg = {
        id: Date.now(),
        sender_id: props.currentUserId,
        content: '[图片]',
        created_at: new Date().toISOString(),
        image_url: dataUrl,
      };
      messages.value.push(newMsg);
      await nextTick();
      if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight;
    } else {
      const msg = await api.im.send(props.conversationId, { content: '[图片]', image_url: dataUrl });
      messages.value.push(msg);
      await nextTick();
      if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight;
      const latestId = msg.id;
      if (latestId != null) api.im.markRead(props.conversationId, { last_read_msg_id: latestId }).then(() => emit('read')).catch(() => {});
    }
  } catch (err) {
    sendError.value = true;
  } finally {
    sending.value = false;
  }
}

watch(
  () => props.conversationId,
  (id) => {
    messages.value = [];
    nextCursor.value = undefined;
    hasMore.value = true;
    currentUserMutedUntil.value = null;
    groupParticipants.value = [];
    if (mutedCheckTimer) {
      clearInterval(mutedCheckTimer);
      mutedCheckTimer = null;
    }
    if (!id) return;
    const isMock = Array.isArray(props.mockMessages);
    if (isMock && props.mockMessages) {
      messages.value = [...props.mockMessages];
      hasMore.value = false;
      loading.value = false;
      loadingMore.value = false;
      nextTick(() => {
        if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight;
      });
      return;
    }
    const saved = scrollTops.get(id);
    loadMessages(false).then(() => {
      nextTick(() => {
        if (scrollRef.value && saved != null) scrollRef.value.scrollTop = saved;
        else if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight;
      });
    });
    if (id && props.conversation?.type === 'group' && Number(props.conversation?.id) === Number(id)) {
      api.im
        .participants(id)
        .then((list) => {
          const arr = Array.isArray(list) ? list : [];
          groupParticipants.value = arr;
          const me = arr.find((p) => Number(p.user_id) === Number(props.currentUserId));
          currentUserMutedUntil.value = me?.muted_until ?? null;
        })
        .catch((e) => {
          console.warn('Failed to load participants', e);
          currentUserMutedUntil.value = null;
          groupParticipants.value = [];
        });
    }
    mutedCheckTimer = setInterval(() => {
      if (currentUserMutedUntil.value && new Date(currentUserMutedUntil.value).getTime() <= Date.now()) {
        currentUserMutedUntil.value = null;
      }
    }, 60000);
  },
  { immediate: true }
);

watch(
  () => props.mockMessages,
  (mock) => {
    if (props.conversationId && Array.isArray(mock)) {
      messages.value = [...mock];
      hasMore.value = false;
      loading.value = false;
      nextTick(() => {
        if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight;
      });
    }
  },
  { flush: 'post' }
);

watch(
  () => [props.conversation?.id, props.conversation?.type],
  ([convId, type]) => {
    if (props.conversationId && type === 'group' && Number(convId) === Number(props.conversationId)) {
      api.im
        .participants(props.conversationId)
        .then((list) => {
          const arr = Array.isArray(list) ? list : [];
          groupParticipants.value = arr;
          const me = arr.find((p) => Number(p.user_id) === Number(props.currentUserId));
          currentUserMutedUntil.value = me?.muted_until ?? null;
        })
        .catch((e) => {
          console.warn('Failed to load participants', e);
          currentUserMutedUntil.value = null;
          groupParticipants.value = [];
        });
    }
  }
);

onUnmounted(() => {
  if (mutedCheckTimer) clearInterval(mutedCheckTimer);
});

/** 从 content 解析出被 @ 的用户 id 列表，供发消息时传给后端 */
function parseMentionUserIds(content, participants) {
  if (!content || !Array.isArray(participants) || participants.length === 0) return null;
  const MENTION_EVERYONE = '@所有人';
  const regex = /(@所有人|@[^\s@]+)/g;
  const set = new Set();
  let m;
  while ((m = regex.exec(content)) !== null) {
    const token = m[1];
    if (token === MENTION_EVERYONE) {
      participants.forEach((p) => set.add(Number(p.user_id)));
    } else {
      const displayName = token.slice(1);
      const found = participants.find((p) => getMemberDisplayName(p) === displayName);
      if (found) set.add(Number(found.user_id));
    }
  }
  return set.size ? Array.from(set) : null;
}

async function sendMessage() {
  const text = inputText.value.trim();
  if (!text || !props.conversationId || sending.value || isMuted.value) return;
  sending.value = true;
  sendError.value = null;
  const isMock = Array.isArray(props.mockMessages);
  try {
    if (isMock) {
      const newMsg = {
        id: Date.now(),
        sender_id: props.currentUserId,
        content: text,
        created_at: new Date().toISOString(),
      };
      messages.value.push(newMsg);
      inputText.value = '';
      await nextTick();
      if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight;
    } else {
      const body = { content: text };
      if (props.conversation?.type === 'group' && groupParticipants.value.length > 0) {
        const mentionIds = parseMentionUserIds(text, groupParticipants.value);
        if (mentionIds && mentionIds.length > 0) body.mention_user_ids = mentionIds;
      }
      const msg = await api.im.send(props.conversationId, body);
      messages.value.push(msg);
      inputText.value = '';
      await nextTick();
      if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight;
    }
  } catch (e) {
    sendError.value = true;
    if (e?.code === 'MUTED') {
      const d = new Date();
      d.setHours(d.getHours() + 24);
      currentUserMutedUntil.value = d.toISOString();
    }
  } finally {
    sending.value = false;
  }
}
</script>

<style scoped>
.im-chat-pane { flex: 1; display: flex; flex-direction: column; min-width: 0; background: var(--jt-bg); }
.chat-header {
  flex-shrink: 0;
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid var(--jt-border);
  background: var(--jt-card-bg);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.chat-header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}
.chat-back {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  margin: -8px 0 -8px -8px;
  padding: 0;
  border: none;
  background: none;
  color: var(--jt-text);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: background 0.15s;
}
.chat-back:hover { background: color-mix(in srgb, var(--jt-primary) 10%, transparent); }
.chat-back svg { width: 22px; height: 22px; }
.chat-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
  font-size: 1rem;
  letter-spacing: -0.01em;
  color: var(--jt-text);
}
.btn-group-info {
  padding: 0.4rem 0.75rem;
  font-size: 0.8125rem;
  border-radius: 8px;
  border: 1px solid var(--jt-border);
  background: var(--jt-bg);
  color: var(--jt-text);
  cursor: pointer;
  font-weight: 500;
  transition: border-color 0.15s, background 0.15s;
}
.btn-group-info:hover { border-color: var(--jt-primary); background: color-mix(in srgb, var(--jt-primary) 8%, transparent); }
.messages-wrap {
  flex: 1;
  overflow: auto;
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--jt-bg);
}
.load-more, .btn-load-more, .all-loaded { margin-bottom: 0.75rem; font-size: 0.875rem; }
.btn-load-more {
  padding: 0.4rem 0.85rem;
  border-radius: 10px;
  border: 1px solid var(--jt-border);
  background: var(--jt-card-bg);
  cursor: pointer;
  color: var(--jt-text);
  font-size: 0.8125rem;
  transition: border-color 0.15s, background 0.15s;
}
.btn-load-more:hover:not(:disabled) { border-color: var(--jt-primary); background: color-mix(in srgb, var(--jt-primary) 8%, transparent); }
.messages { width: 100%; max-width: 720px; display: flex; flex-direction: column; gap: 0.25rem; }
.center { text-align: center; padding: 1.5rem; }
.input-row {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.25rem 1.25rem;
  border-top: 1px solid var(--jt-border);
  background: var(--jt-card-bg);
}
.input-wrap { flex: 1; position: relative; min-width: 0; }
.input {
  width: 100%;
  padding: 0.65rem 1rem;
  border: 1px solid var(--jt-border);
  border-radius: 12px;
  font-size: 0.9375rem;
  box-sizing: border-box;
  background: var(--jt-bg);
  color: var(--jt-text);
  transition: border-color 0.15s, box-shadow 0.15s;
}
.input::placeholder { color: var(--jt-text-muted); }
.input:focus {
  outline: none;
  border-color: var(--jt-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--jt-primary) 15%, transparent);
}
.mention-picker {
  position: absolute;
  left: 0;
  bottom: 100%;
  margin-bottom: 0.35rem;
  max-height: 12rem;
  overflow: auto;
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
  border-radius: 12px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
  z-index: 10;
  display: flex;
  flex-direction: column;
  min-width: 11rem;
}
.mention-item {
  display: block;
  width: 100%;
  padding: 0.5rem 0.85rem;
  text-align: left;
  border: none;
  background: none;
  color: var(--jt-text);
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.1s;
}
.mention-item:hover { background: var(--jt-bg); }
.mention-item-active { background: color-mix(in srgb, var(--jt-primary) 15%, transparent); color: var(--jt-primary); font-weight: 500; }
.mention-empty { padding: 0.5rem 0.85rem; font-size: 0.875rem; color: var(--jt-text-muted); }
.input.input-muted { background: var(--jt-card-bg); cursor: not-allowed; opacity: 0.85; }
.btn-send {
  flex-shrink: 0;
  padding: 0.65rem 1.25rem;
  border-radius: 12px;
  background: var(--jt-primary);
  color: #fff;
  border: none;
  cursor: pointer;
  font-size: 0.9375rem;
  font-weight: 500;
  transition: opacity 0.15s, transform 0.05s;
}
.btn-send:hover:not(:disabled) { opacity: 0.92; }
.btn-send:active:not(:disabled) { transform: scale(0.98); }
.btn-send:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-send-loading {
  display: inline-block;
  width: 1em;
  height: 1em;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.muted-hint { padding: 0 1.25rem 0.35rem; font-size: 0.75rem; color: var(--jt-text-muted); line-height: 1.2; background: var(--jt-card-bg); }
.send-error {
  padding: 0 1.25rem 0.75rem;
  font-size: 0.875rem;
  color: var(--jt-error, #dc2626);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--jt-card-bg);
}
.btn-retry { background: none; border: none; cursor: pointer; font-size: 1.25rem; color: inherit; padding: 0 0.25rem; }
.empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: var(--jt-bg);
}
.empty-card {
  text-align: center;
  padding: 2.5rem 2rem;
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  max-width: 320px;
}
.empty-icon { font-size: 3rem; display: block; margin-bottom: 0.75rem; opacity: 0.7; }
.empty-text { margin: 0 0 0.35rem; font-size: 1rem; font-weight: 500; color: var(--jt-text); }
.empty-hint { margin: 0; font-size: 0.875rem; color: var(--jt-text-muted); }
.muted { color: var(--jt-text-muted); }
.input-file-hidden { position: absolute; width: 0; height: 0; opacity: 0; pointer-events: none; }
.btn-tool {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--jt-border);
  border-radius: 10px;
  background: var(--jt-bg);
  color: var(--jt-text-muted);
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}
.btn-tool:hover:not(:disabled) { color: var(--jt-primary); border-color: var(--jt-primary); }
.btn-tool:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-tool-icon { width: 22px; height: 22px; }
</style>

<template>
  <section class="im-chat-pane">
    <template v-if="conversationId">
      <div v-if="conversation" class="chat-header">
        <span class="chat-title">{{ conversation.title || ('会话 ' + conversationId) }}</span>
        <button v-if="conversation.type === 'group'" type="button" class="btn-group-info" @click="$emit('openGroupInfo')">
          {{ t('official.im.groupInfoTitle') }}
        </button>
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
          />
        </div>
      </div>
      <form @submit.prevent="sendMessage" class="input-row">
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
        <button type="submit" class="btn primary" :disabled="sending || !inputText.trim() || isMuted">
          {{ sending ? t('common.loading') : t('official.im.send') }}
        </button>
      </form>
      <div v-if="isMuted" class="muted-hint">{{ mutedHintText }}</div>
      <div v-if="sendError" class="send-error">
        {{ t('official.im.sendFailed') }}
        <button type="button" class="btn-retry" @click="sendError = null">×</button>
      </div>
    </template>
    <div v-else class="empty">{{ t('official.im.noConversations') }}</div>
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
});

const emit = defineEmits(['read', 'openGroupInfo']);

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
let mutedCheckTimer = null;

const MENTION_EVERYONE = '@所有人';
const MENTION_EVERYONE_LABEL = '所有人';

function getMemberDisplayName(p) {
  return p?.name || ('UID ' + (p?.uid ?? p?.user_id ?? ''));
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
  try {
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
.im-chat-pane { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.chat-header { display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 1rem; border-bottom: 1px solid var(--jt-border); background: var(--jt-card-bg); }
.chat-title { font-weight: 500; font-size: 0.9375rem; }
.btn-group-info { padding: 0.35rem 0.6rem; font-size: 0.8125rem; border-radius: 6px; border: 1px solid var(--jt-border); background: var(--jt-bg); color: var(--jt-text); cursor: pointer; }
.messages-wrap { flex: 1; overflow: auto; padding: 1rem; display: flex; flex-direction: column; align-items: center; }
.load-more, .btn-load-more, .all-loaded { margin-bottom: 0.5rem; font-size: 0.875rem; }
.btn-load-more { padding: 0.35rem 0.75rem; border-radius: 8px; border: 1px solid var(--jt-border); background: var(--jt-bg); cursor: pointer; color: var(--jt-text); }
.messages { width: 100%; display: flex; flex-direction: column; gap: 0.75rem; }
.center { text-align: center; padding: 1rem; }
.input-row { display: flex; align-items: flex-start; gap: 0.5rem; padding: 1rem; border-top: 1px solid var(--jt-border); }
.input-wrap { flex: 1; position: relative; min-width: 0; }
.input { width: 100%; padding: 0.5rem 0.75rem; border: 1px solid var(--jt-border); border-radius: 8px; font-size: 0.9375rem; box-sizing: border-box; }
.mention-picker { position: absolute; left: 0; bottom: 100%; margin-bottom: 0.25rem; max-height: 12rem; overflow: auto; background: var(--jt-card-bg); border: 1px solid var(--jt-border); border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); z-index: 10; display: flex; flex-direction: column; min-width: 10rem; }
.mention-item { display: block; width: 100%; padding: 0.4rem 0.75rem; text-align: left; border: none; background: none; color: var(--jt-text); font-size: 0.875rem; cursor: pointer; }
.mention-item:hover { background: var(--jt-border); }
.mention-item-active { background: var(--jt-primary); color: #fff; }
.mention-empty { padding: 0.4rem 0.75rem; font-size: 0.875rem; color: var(--jt-text-muted, #999); }
.input.input-muted { background: var(--jt-card-bg, #f1f5f9); cursor: not-allowed; }
.btn.primary { padding: 0.5rem 1rem; border-radius: 8px; background: var(--jt-primary); color: #fff; border: none; cursor: pointer; font-size: 0.9375rem; }
.btn.primary:disabled { opacity: 0.6; cursor: not-allowed; }
.muted-hint { padding: 0 1rem 0.25rem; font-size: 0.75rem; color: var(--jt-text-muted, #999); line-height: 1.2; }
.send-error { padding: 0 1rem 0.5rem; font-size: 0.875rem; color: var(--jt-error, #c00); display: flex; align-items: center; gap: 0.5rem; }
.btn-retry { background: none; border: none; cursor: pointer; font-size: 1.25rem; color: inherit; }
.empty { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--jt-text-muted); font-size: 0.9375rem; }
.muted { color: var(--jt-text-muted); }
</style>

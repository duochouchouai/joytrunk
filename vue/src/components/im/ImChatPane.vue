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
        <input
          v-model="inputText"
          type="text"
          class="input"
          :placeholder="t('official.im.inputPlaceholder')"
          :disabled="sending"
        />
        <button type="submit" class="btn primary" :disabled="sending || !inputText.trim()">
          {{ sending ? t('common.loading') : t('official.im.send') }}
        </button>
      </form>
      <div v-if="sendError" class="send-error">
        {{ t('official.im.sendFailed') }}
        <button type="button" class="btn-retry" @click="sendError = null">×</button>
      </div>
    </template>
    <div v-else class="empty">{{ t('official.im.noConversations') }}</div>
  </section>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { api } from '../../api';
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
    if (!id) return;
    const saved = scrollTops.get(id);
    loadMessages(false).then(() => {
      nextTick(() => {
        if (scrollRef.value && saved != null) scrollRef.value.scrollTop = saved;
        else if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight;
      });
    });
  },
  { immediate: true }
);

async function sendMessage() {
  const text = inputText.value.trim();
  if (!text || !props.conversationId || sending.value) return;
  sending.value = true;
  sendError.value = null;
  try {
    const msg = await api.im.send(props.conversationId, { content: text });
    messages.value.push(msg);
    inputText.value = '';
    await nextTick();
    if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight;
  } catch {
    sendError.value = true;
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
.input-row { display: flex; gap: 0.5rem; padding: 1rem; border-top: 1px solid var(--jt-border); }
.input { flex: 1; padding: 0.5rem 0.75rem; border: 1px solid var(--jt-border); border-radius: 8px; font-size: 0.9375rem; }
.btn.primary { padding: 0.5rem 1rem; border-radius: 8px; background: var(--jt-primary); color: #fff; border: none; cursor: pointer; font-size: 0.9375rem; }
.btn.primary:disabled { opacity: 0.6; cursor: not-allowed; }
.send-error { padding: 0 1rem 0.5rem; font-size: 0.875rem; color: var(--jt-error, #c00); display: flex; align-items: center; gap: 0.5rem; }
.btn-retry { background: none; border: none; cursor: pointer; font-size: 1.25rem; color: inherit; }
.empty { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--jt-text-muted); font-size: 0.9375rem; }
.muted { color: var(--jt-text-muted); }
</style>

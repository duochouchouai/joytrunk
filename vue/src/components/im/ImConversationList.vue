<template>
  <aside class="im-conversation-list">
    <h2 class="panel-title">{{ t('official.im.title') }}</h2>
    <button v-if="showNewButton" type="button" class="btn-new" @click="$emit('newConversation')">
      {{ t('official.im.newConversation') }}
    </button>
    <div v-if="loading" class="muted">{{ t('common.loading') }}</div>
    <ul v-else-if="conversations.length" class="list">
      <li
        v-for="c in conversations"
        :key="c.id"
        class="item"
        :class="{ active: currentId === c.id }"
        @click="$emit('select', c.id)"
      >
        <span class="item-name">
          {{ c.title || '会话 ' + c.id }}
          <span v-if="(c.unread_count || 0) > 0" class="unread-badge">{{ c.unread_count > 99 ? '99+' : c.unread_count }}</span>
        </span>
        <span v-if="(c.mention_unread_count || 0) > 0" class="item-mention-hint">{{ t('official.im.mentionHint') }}</span>
        <span v-if="c.announcement" class="item-announcement">{{ truncateText(c.announcement, ANNOUNCEMENT_LEN) }}</span>
        <span v-if="c.last_message" class="item-preview">{{ preview(c.last_message) }}</span>
        <span v-if="c.updated_at" class="item-time">{{ formatTime(c.updated_at) }}</span>
      </li>
    </ul>
    <div v-else class="muted">{{ t('official.im.noConversations') }}</div>
  </aside>
</template>

<script setup>
import { useI18n } from 'vue-i18n';
import { truncateText } from '../../utils/im';

defineProps({
  conversations: { type: Array, default: () => [] },
  currentId: { type: [Number, String], default: null },
  loading: { type: Boolean, default: false },
  showNewButton: { type: Boolean, default: true },
});

defineEmits(['select', 'newConversation']);

const { t } = useI18n();

const PREVIEW_LEN = 40;
const ANNOUNCEMENT_LEN = 20;

function preview(msg) {
  if (!msg || !msg.content) return '';
  const text = String(msg.content).replace(/\n/g, ' ');
  return text.length > PREVIEW_LEN ? text.slice(0, PREVIEW_LEN) + '...' : text;
}

function formatTime(val) {
  if (!val) return '';
  const d = new Date(val);
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  if (sameDay) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  return d.toLocaleDateString();
}
</script>

<style scoped>
.im-conversation-list {
  width: 260px;
  min-width: 260px;
  border-right: 1px solid var(--jt-border);
  padding: 1rem;
  background: var(--jt-bg);
  display: flex;
  flex-direction: column;
}
.panel-title { margin: 0 0 0.75rem; font-size: 1rem; font-weight: 600; color: var(--jt-text); }
.btn-new { margin-bottom: 0.75rem; padding: 0.5rem 0.75rem; border-radius: 8px; background: var(--jt-primary); color: #fff; border: none; cursor: pointer; font-size: 0.875rem; }
.list { list-style: none; padding: 0; margin: 0; flex: 1; overflow: auto; }
.item { padding: 8px 12px; min-height: 64px; border-radius: 8px; cursor: pointer; font-size: 0.9375rem; display: flex; flex-direction: column; gap: 0.15rem; }
.item:hover { background: var(--jt-card-bg); }
.item.active { background: rgba(15, 118, 110, 0.12); color: var(--jt-primary); font-weight: 500; }
.item-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; display: flex; align-items: center; gap: 0.35rem; }
.item-mention-hint { display: block; font-size: 0.75rem; color: var(--jt-primary); font-weight: 500; }
.unread-badge { flex-shrink: 0; min-width: 1.1em; padding: 0.1em 0.35em; font-size: 0.7rem; font-weight: 600; background: var(--jt-primary); color: #fff; border-radius: 10px; }
.item-announcement { display: block; font-size: 0.75rem; color: var(--jt-text-muted, #999); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; line-height: 1.2; margin: 2px 0; }
.item-preview { font-size: 0.8125rem; color: var(--jt-text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.item-time { font-size: 0.75rem; color: var(--jt-text-muted); }
.muted { font-size: 0.875rem; color: var(--jt-text-muted); }
</style>

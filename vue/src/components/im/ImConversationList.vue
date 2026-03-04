<template>
  <aside class="im-conversation-list" :class="{ 'im-conversation-list-headless': hidePanelHead }">
    <div v-if="!hidePanelHead" class="panel-head">
      <h2 class="panel-title">{{ t('official.im.title') }}</h2>
      <button v-if="showNewButton" type="button" class="btn-new" @click="$emit('newConversation')">
        <span class="btn-new-icon">+</span>
        {{ t('official.im.newConversation') }}
      </button>
    </div>
    <div v-if="loading" class="loading-state">
      <span class="loading-dot"></span>
      <span class="loading-dot"></span>
      <span class="loading-dot"></span>
      <span class="muted">{{ t('common.loading') }}</span>
    </div>
    <ul v-else-if="conversations.length" class="list">
      <li
        v-for="c in conversations"
        :key="c.id"
        class="item"
        :class="{ active: currentId === c.id }"
        @click="$emit('select', c.id)"
      >
        <span class="item-avatar">{{ (c.title || '').charAt(0) || '?' }}</span>
        <div class="item-body">
          <div class="item-row">
            <span class="item-name">{{ c.title || '会话 ' + c.id }}</span>
            <span v-if="(c.unread_count || 0) > 0" class="unread-badge">{{ (c.unread_count || 0) > 99 ? '99+' : c.unread_count }}</span>
            <span v-else-if="c.updated_at" class="item-time">{{ formatTime(c.updated_at) }}</span>
          </div>
          <span v-if="(c.mention_unread_count || 0) > 0" class="item-mention-hint">{{ t('official.im.mentionHint') }}</span>
          <span v-if="c.announcement" class="item-announcement">{{ truncateText(c.announcement, ANNOUNCEMENT_LEN) }}</span>
          <span v-if="c.last_message" class="item-preview">{{ preview(c.last_message) }}</span>
        </div>
      </li>
    </ul>
    <div v-else class="empty-state">
      <span class="empty-icon">💬</span>
      <span class="muted">{{ t('official.im.noConversations') }}</span>
    </div>
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
  /** 为 true 时不渲染顶部标题和新建按钮（由父组件提供，如移动端） */
  hidePanelHead: { type: Boolean, default: false },
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
  width: 280px;
  min-width: 280px;
  border-right: 1px solid var(--jt-border);
  padding: 0;
  background: var(--jt-card-bg);
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.03);
}
.panel-head {
  padding: 1rem 1rem 0.75rem;
  border-bottom: 1px solid var(--jt-border);
}
.panel-title {
  margin: 0 0 0.75rem;
  font-size: 1.0625rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--jt-text);
}
.btn-new {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  width: 100%;
  padding: 0.5rem 0.75rem;
  border-radius: 10px;
  background: var(--jt-primary);
  color: #fff;
  border: none;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: opacity 0.15s, transform 0.05s;
}
.btn-new:hover { opacity: 0.92; }
.btn-new:active { transform: scale(0.98); }
.btn-new-icon {
  font-size: 1.1em;
  line-height: 1;
  opacity: 0.95;
}
.loading-state {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1.5rem 1rem;
}
.loading-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--jt-primary);
  animation: bounce 0.6s ease-in-out infinite;
}
.loading-dot:nth-child(2) { animation-delay: 0.1s; }
.loading-dot:nth-child(3) { animation-delay: 0.2s; }
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
.list { list-style: none; padding: 0.5rem 0; margin: 0; flex: 1; overflow: auto; }
.im-conversation-list-headless .list {
  padding-top: 0.5rem;
}
/* 移动端/无头部时列表左右铺满，去掉项左右 margin */
.im-conversation-list-headless {
  border-right: none;
  box-shadow: none;
}
.im-conversation-list-headless .item {
  margin-left: 0;
  margin-right: 0;
  border-radius: 0;
}
.item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  margin: 0 0.5rem;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.15s;
}
.item:hover { background: color-mix(in srgb, var(--jt-primary) 6%, transparent); }
.item.active {
  background: color-mix(in srgb, var(--jt-primary) 12%, transparent);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--jt-primary) 20%, transparent);
}
.item.active .item-name { color: var(--jt-primary); font-weight: 600; }
.item-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--jt-primary) 0%, color-mix(in srgb, var(--jt-primary) 75%, #555) 100%);
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  line-height: 1;
}
.item-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.item-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}
.item-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
  font-size: 0.9375rem;
  color: var(--jt-text);
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.item-time {
  font-size: 0.7rem;
  color: var(--jt-text-muted);
  flex-shrink: 0;
}
.unread-badge {
  flex-shrink: 0;
  min-width: 1.25rem;
  height: 1.25rem;
  padding: 0 0.35rem;
  border-radius: 10px;
  background: #ef4444;
  color: #fff;
  font-size: 0.7rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}
.item-mention-hint { display: block; font-size: 0.75rem; color: var(--jt-primary); font-weight: 500; }
.item-announcement {
  display: block;
  font-size: 0.75rem;
  color: var(--jt-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.2;
}
.item-preview {
  font-size: 0.8125rem;
  color: var(--jt-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 2rem 1rem;
}
.empty-icon { font-size: 2rem; opacity: 0.6; }
.muted { font-size: 0.875rem; color: var(--jt-text-muted); }
</style>

<template>
  <div class="im-message" :class="{ self: isSelf }">
    <div class="bubble">
      <span class="text">
        <template v-for="(part, i) in contentParts" :key="i">
          <span v-if="part.mention" class="mention">{{ part.text }}</span>
          <template v-else>{{ part.text }}</template>
        </template>
      </span>
      <span class="time">{{ formatTime(message.created_at) }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  message: { type: Object, required: true },
  isSelf: { type: Boolean, default: false },
});

const MENTION_EVERYONE = '@所有人';
const MENTION_REG = /(@所有人|@[^\s@]+)/g;

function isMentionPart(text) {
  return text === MENTION_EVERYONE || (text.startsWith('@') && /^@[^\s@]+$/.test(text));
}

const contentParts = computed(() => {
  const content = props.message?.content;
  if (typeof content !== 'string') return [];
  const parts = content.split(MENTION_REG).filter((p) => p.length > 0);
  return parts.map((text) => ({ text, mention: isMentionPart(text) }));
});

function formatTime(val) {
  if (!val) return '';
  return new Date(val).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
</script>

<style scoped>
.im-message { display: flex; justify-content: flex-start; }
.im-message.self { justify-content: flex-end; }
.bubble {
  max-width: 80%;
  padding: 0.5rem 0.75rem;
  border-radius: 10px;
  font-size: 0.9375rem;
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
}
.im-message.self .bubble { background: var(--jt-primary); color: #fff; border-color: var(--jt-primary); }
.text { white-space: pre-wrap; word-break: break-word; }
.text :deep(.mention) { color: var(--jt-primary); font-weight: 600; }
.im-message.self .bubble .text :deep(.mention) { color: rgba(255,255,255,0.95); }
.time { display: block; font-size: 0.75rem; opacity: 0.85; margin-top: 0.2rem; }
</style>

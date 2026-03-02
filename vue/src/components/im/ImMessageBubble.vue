<template>
  <div class="im-message" :class="{ self: isSelf }">
    <div class="bubble">
      <span class="text">{{ message.content }}</span>
      <span class="time">{{ formatTime(message.created_at) }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  message: { type: Object, required: true },
  isSelf: { type: Boolean, default: false },
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
.time { display: block; font-size: 0.75rem; opacity: 0.85; margin-top: 0.2rem; }
</style>

<template>
  <div class="im-message" :class="{ self: isSelf }">
    <div class="avatar-wrap" v-if="!isSelf">
      <img v-if="avatarUrl" :src="avatarUrl" alt="" class="avatar-img" @error="avatarError = true" />
      <span v-else class="avatar-initial">{{ displayInitial }}</span>
    </div>
    <div class="bubble">
      <template v-if="message.image_url">
        <div v-if="parsed.thinkBlocks.length" class="think-section">
          <button
            type="button"
            class="think-toggle"
            :aria-expanded="thinkExpanded"
            @click="thinkExpanded = !thinkExpanded"
          >
            <span class="think-toggle-icon">{{ thinkExpanded ? '▼' : '▶' }}</span>
            <span class="think-toggle-label">{{ thinkExpanded ? '收起思考过程' : '展开思考过程' }}</span>
            <span class="think-toggle-count">({{ parsed.thinkBlocks.length }})</span>
          </button>
          <div v-show="thinkExpanded" class="think-content">
            <div
              v-for="(block, i) in parsed.thinkBlocks"
              :key="'t-' + i"
              class="think-block"
            >{{ block }}</div>
          </div>
        </div>
        <a :href="message.image_url" target="_blank" rel="noopener" class="bubble-image-wrap">
          <img v-if="!imageError" :src="message.image_url" alt="" class="bubble-image" @error="imageError = true" />
          <span v-else class="bubble-image-fail">[图片]</span>
        </a>
        <template v-if="message.content">
          <span v-if="parsed.visible" class="text">
            <span
              v-for="(part, i) in partsForText(parsed.visible)"
              :key="'v-' + i"
              :class="{ mention: part.mention }"
            >{{ part.text }}</span>
          </span>
        </template>
      </template>
      <template v-else>
        <div v-if="parsed.thinkBlocks.length" class="think-section">
          <button
            type="button"
            class="think-toggle"
            :aria-expanded="thinkExpanded"
            @click="thinkExpanded = !thinkExpanded"
          >
            <span class="think-toggle-icon">{{ thinkExpanded ? '▼' : '▶' }}</span>
            <span class="think-toggle-label">{{ thinkExpanded ? '收起思考过程' : '展开思考过程' }}</span>
            <span class="think-toggle-count">({{ parsed.thinkBlocks.length }})</span>
          </button>
          <div v-show="thinkExpanded" class="think-content">
            <div
              v-for="(block, i) in parsed.thinkBlocks"
              :key="'t-' + i"
              class="think-block"
            >{{ block }}</div>
          </div>
        </div>
        <span v-if="parsed.visible" class="text">
          <span
            v-for="(part, i) in partsForText(parsed.visible)"
            :key="'v-' + i"
            :class="{ mention: part.mention }"
          >{{ part.text }}</span>
        </span>
      </template>
      <span class="time">{{ formatTime(message.created_at) }}</span>
    </div>
    <div class="avatar-wrap self-avatar" v-if="isSelf">
      <img v-if="avatarUrl" :src="avatarUrl" alt="" class="avatar-img" @error="avatarError = true" />
      <span v-else class="avatar-initial">{{ displayInitial }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';

const props = defineProps({
  message: { type: Object, required: true },
  isSelf: { type: Boolean, default: false },
  avatarUrl: { type: String, default: null },
  initial: { type: String, default: '?' },
});

const avatarError = ref(false);
const imageError = ref(false);
const thinkExpanded = ref(false);
const displayInitial = computed(() => {
  const s = (props.initial || '?').trim();
  return s ? s.charAt(0).toUpperCase() : '?';
});

const MENTION_EVERYONE = '@所有人';
const MENTION_REG = /(@所有人|@[^\s@]+)/g;
const THINK_REG = /<think>([\s\S]*?)<\/think>/gi;

function isMentionPart(text) {
  return text === MENTION_EVERYONE || (text.startsWith('@') && /^@[^\s@]+$/.test(text));
}

/** 解析 content：抽出 <think> 块，得到可见文本 + think 块列表 */
const parsed = computed(() => {
  const content = props.message?.content;
  if (typeof content !== 'string') return { visible: '', thinkBlocks: [] };
  const thinkBlocks = [];
  const visible = content.replace(THINK_REG, (_, inner) => {
    thinkBlocks.push(inner.trim());
    return '';
  }).trim();
  return { visible, thinkBlocks };
});

function partsForText(text) {
  if (!text) return [];
  const parts = text.split(MENTION_REG).filter((p) => p.length > 0);
  return parts.map((t) => ({ text: t, mention: isMentionPart(t) }));
}

function formatTime(val) {
  if (!val) return '';
  return new Date(val).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
</script>

<style scoped>
.im-message { display: flex; align-items: flex-end; justify-content: flex-start; margin-bottom: 0.5rem; gap: 0.5rem; }
.im-message.self { justify-content: flex-end; }
.avatar-wrap {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, var(--jt-primary) 0%, color-mix(in srgb, var(--jt-primary) 75%, #555) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.avatar-wrap.self-avatar { order: 1; }
.im-message.self .bubble { order: 0; }
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-initial { font-size: 0.9rem; font-weight: 600; color: #fff; line-height: 1; }
.bubble {
  max-width: 72%;
  padding: 0.6rem 1rem;
  border-radius: 16px;
  font-size: 0.9375rem;
  line-height: 1.45;
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  position: relative;
}
.im-message.self .bubble {
  background: var(--jt-primary);
  color: #fff;
  border-color: var(--jt-primary);
  box-shadow: 0 2px 8px color-mix(in srgb, var(--jt-primary) 35%, transparent);
  border-bottom-right-radius: 4px;
}
.im-message:not(.self) .bubble { border-bottom-left-radius: 4px; }
.text { white-space: pre-wrap; word-break: break-word; }
.text :deep(.mention) { color: var(--jt-primary); font-weight: 600; }
.im-message.self .bubble .text :deep(.mention) { color: rgba(255,255,255,0.95); }
.time {
  display: block;
  font-size: 0.7rem;
  opacity: 0.82;
  margin-top: 0.35rem;
  letter-spacing: 0.02em;
}
.bubble-image-wrap {
  display: block;
  margin-bottom: 0.25rem;
  border-radius: 8px;
  overflow: hidden;
  max-width: 100%;
}
.bubble-image {
  max-width: 240px;
  max-height: 240px;
  width: auto;
  height: auto;
  display: block;
}
.bubble-image-fail {
  font-size: 0.875rem;
  opacity: 0.8;
}
.think-section {
  margin-bottom: 0.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  padding-bottom: 0.4rem;
}
.im-message.self .bubble .think-section {
  border-bottom-color: rgba(255, 255, 255, 0.25);
}
.think-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  color: var(--jt-text-muted);
  background: rgba(0, 0, 0, 0.05);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.im-message.self .bubble .think-toggle {
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.15);
}
.think-toggle:hover {
  background: rgba(0, 0, 0, 0.1);
  color: var(--jt-text);
}
.im-message.self .bubble .think-toggle:hover {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}
.think-toggle-icon {
  font-size: 0.65rem;
  opacity: 0.9;
}
.think-toggle-label {
  font-weight: 500;
}
.think-toggle-count {
  opacity: 0.8;
}
.think-content {
  margin-top: 0.4rem;
  margin-bottom: 0.25rem;
  padding: 0.5rem 0.6rem;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 8px;
  font-size: 0.8125rem;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 12rem;
  overflow-y: auto;
}
.im-message.self .bubble .think-content {
  background: rgba(255, 255, 255, 0.15);
}
.think-block {
  margin-bottom: 0.35rem;
}
.think-block:last-child {
  margin-bottom: 0;
}
</style>

<template>
  <div class="im-page">
    <aside class="conversation-list">
      <h2 class="panel-title">{{ t('official.im.title') }}</h2>
      <div v-if="loading" class="muted">{{ t('common.loading') }}</div>
      <ul v-else-if="conversations.length" class="list">
        <li
          v-for="c in conversations"
          :key="c.id"
          class="item"
          :class="{ active: currentId === c.id }"
          @click="currentId = c.id"
        >
          <span class="item-name">{{ c.title || c.id }}</span>
        </li>
      </ul>
      <div v-else class="muted">{{ t('official.im.noConversations') }}</div>
    </aside>
    <section class="chat-area">
      <template v-if="currentId">
        <div class="messages" ref="messagesRef">
          <div
            v-for="m in messages"
            :key="m.id"
            class="message"
            :class="m.role"
          >
            <span class="message-text">{{ m.content || m.text }}</span>
          </div>
        </div>
        <form @submit.prevent="sendMessage" class="input-row">
          <input
            v-model="inputText"
            type="text"
            class="input"
            :placeholder="t('official.im.inputPlaceholder')"
          />
          <button type="submit" class="btn primary">{{ t('official.im.send') }}</button>
        </form>
      </template>
      <div v-else class="empty">
        {{ t('official.im.noConversations') }}
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../api'

const { t } = useI18n()
const conversations = ref([])
const messages = ref([])
const currentId = ref(null)
const loading = ref(true)
const inputText = ref('')
const messagesRef = ref(null)

async function loadConversations() {
  try {
    conversations.value = await api.im.conversations()
    if (conversations.value.length && !currentId.value) currentId.value = conversations.value[0].id
  } catch {
    conversations.value = []
  } finally {
    loading.value = false
  }
}

async function loadMessages() {
  if (!currentId.value) { messages.value = []; return }
  try {
    const data = await api.im.messages(currentId.value)
    messages.value = Array.isArray(data) ? data : (data.items || data.messages || [])
  } catch {
    messages.value = []
  }
  nextTick(() => {
    if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  })
}

watch(currentId, () => { loadMessages() }, { immediate: true })

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || !currentId.value) return
  try {
    await api.im.send(currentId.value, { content: text })
    messages.value.push({ id: Date.now(), role: 'user', content: text })
    inputText.value = ''
    nextTick(() => {
      if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    })
  } catch (e) {
    console.error(e)
  }
}

loadConversations()
</script>

<style scoped>
.im-page { display: flex; height: 100%; min-height: 60vh; font-family: 'Segoe UI', system-ui, sans-serif; }
.conversation-list {
  width: 240px;
  min-width: 240px;
  border-right: 1px solid var(--jt-border);
  padding: 1rem;
  background: var(--jt-bg);
}
.panel-title { margin: 0 0 1rem; font-size: 1rem; font-weight: 600; color: var(--jt-text); }
.list { list-style: none; padding: 0; margin: 0; }
.item { padding: 0.6rem 0.75rem; border-radius: 8px; cursor: pointer; font-size: 0.9375rem; }
.item:hover { background: var(--jt-card-bg); }
.item.active { background: rgba(15, 118, 110, 0.12); color: var(--jt-primary); font-weight: 500; }
.item-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block; }
.muted { font-size: 0.875rem; color: var(--jt-text-muted); }
.chat-area { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.messages { flex: 1; overflow: auto; padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem; }
.message { max-width: 80%; padding: 0.5rem 0.75rem; border-radius: 10px; font-size: 0.9375rem; }
.message.user { align-self: flex-end; background: var(--jt-primary); color: #fff; }
.message.assistant { align-self: flex-start; background: var(--jt-card-bg); border: 1px solid var(--jt-border); }
.message-text { white-space: pre-wrap; word-break: break-word; }
.input-row { display: flex; gap: 0.5rem; padding: 1rem; border-top: 1px solid var(--jt-border); }
.input { flex: 1; padding: 0.5rem 0.75rem; border: 1px solid var(--jt-border); border-radius: 8px; font-size: 0.9375rem; }
.btn.primary { padding: 0.5rem 1rem; border-radius: 8px; background: var(--jt-primary); color: #fff; border: none; cursor: pointer; font-size: 0.9375rem; }
.empty { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--jt-text-muted); font-size: 0.9375rem; }
</style>

<template>
  <div class="im-page" :class="{ 'im-page-mobile': isMobile }">
    <template v-if="!isMobile">
      <ImConversationList
        :conversations="displayConversations"
        :current-id="currentId"
        :loading="loading"
        @select="currentId = $event"
        @new-conversation="showCreate = true"
      />
      <ImChatPane
        ref="chatPaneRef"
        :conversation-id="currentId"
        :current-user-id="currentUserId"
        :conversation="currentConversation"
        :mock-messages="currentMockMessages"
        :me="me"
        :sender-map="imSenderMap"
        @read="loadConversations"
        @open-group-info="showGroupInfo = true"
      />
    </template>
    <template v-else>
      <Transition :name="currentId ? 'slide-from-right' : 'slide-from-left'" mode="out-in">
        <div :key="currentId ? 'detail' : 'list'" class="im-mobile-view">
          <template v-if="!currentId">
            <MobileTitleBar :title="t('nav.imChat')">
              <template #left>
                <button type="button" class="mobile-btn-plus" :aria-label="t('official.im.newConversation')" @click="showCreate = true">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"/></svg>
                </button>
              </template>
            </MobileTitleBar>
            <div class="im-mobile-search">
              <input
                v-model="searchQuery"
                type="search"
                class="im-mobile-search-input"
                :placeholder="t('common.searchPlaceholder')"
                autocomplete="off"
              />
            </div>
            <ImConversationList
              :conversations="filteredConversations"
              :current-id="currentId"
              :loading="loading"
              :show-new-button="false"
              :hide-panel-head="true"
              @select="currentId = $event"
              @new-conversation="showCreate = true"
            />
          </template>
          <ImChatPane
            v-else
            ref="chatPaneRef"
            :conversation-id="currentId"
            :current-user-id="currentUserId"
            :conversation="currentConversation"
            :mock-messages="currentMockMessages"
            :me="me"
            :sender-map="imSenderMap"
            :show-back="true"
            @read="loadConversations"
            @open-group-info="showGroupInfo = true"
            @back="currentId = null"
          />
        </div>
      </Transition>
    </template>
    <ImCreateConversation
      :show="showCreate"
      @close="showCreate = false"
      @created="onConversationCreated"
    />
    <ImGroupInfo
      :show="showGroupInfo"
      :conversation-id="currentId"
      :conversation="currentConversation"
      :current-user-id="currentUserId"
      @close="showGroupInfo = false"
      @leave="onLeaveOrDismiss"
      @dismiss="onLeaveOrDismiss"
      @updated="loadConversations"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject } from 'vue';
import { useI18n } from 'vue-i18n';
import { api, getToken, getBase } from '../api';
import MobileTitleBar from '../components/MobileTitleBar.vue';
import ImConversationList from '../components/im/ImConversationList.vue';
import ImChatPane from '../components/im/ImChatPane.vue';
import ImCreateConversation from '../components/im/ImCreateConversation.vue';
import ImGroupInfo from '../components/im/ImGroupInfo.vue';

const { t } = useI18n();
const isMobile = inject('isMobile', ref(false));
const searchQuery = ref('');
const chatPaneRef = ref(null);
let imWs = null;

/** 左侧 mock 会话列表（类微信，无后端会话时展示） */
const MOCK_CONVERSATIONS = [
  {
    id: 'mock-1',
    type: 'direct',
    title: 'JoyTrunk 助手',
    last_message: { content: '你好，有什么可以帮到你？' },
    updated_at: new Date().toISOString(),
    unread_count: 0,
  },
  {
    id: 'mock-2',
    type: 'direct',
    title: '课程小助手',
    last_message: { content: '本周作业已发布，记得按时提交哦～' },
    updated_at: new Date(Date.now() - 3600000).toISOString(),
    unread_count: 1,
  },
  {
    id: 'mock-3',
    type: 'direct',
    title: '学习群',
    last_message: { content: '张三：有人一起刷题吗？' },
    updated_at: new Date(Date.now() - 86400000).toISOString(),
    unread_count: 0,
  },
];

/** 各 mock 会话的 mock 消息（mooc 场景） */
const MOCK_MESSAGES = {
  'mock-1': [
    { id: 101, sender_id: 0, content: '你好，我是 JoyTrunk 助手。', created_at: new Date(Date.now() - 300000).toISOString() },
    { id: 102, sender_id: 1, content: '你好，想了解一下怎么用。', created_at: new Date(Date.now() - 280000).toISOString() },
    { id: 103, sender_id: 0, content: '你可以先下载客户端，登录后就能和智能体聊天、安排任务啦。', created_at: new Date(Date.now() - 260000).toISOString() },
    { id: 104, sender_id: 1, content: '好的谢谢！', created_at: new Date(Date.now() - 240000).toISOString() },
  ],
  'mock-2': [
    { id: 201, sender_id: 0, content: '【课程通知】本周作业：完成第 3 章习题。', created_at: new Date(Date.now() - 7200000).toISOString() },
    { id: 202, sender_id: 1, content: '收到，截止日期是？', created_at: new Date(Date.now() - 7000000).toISOString() },
    { id: 203, sender_id: 0, content: '本周日 23:59 前提交即可。', created_at: new Date(Date.now() - 6980000).toISOString() },
  ],
  'mock-3': [
    { id: 301, sender_id: 2, content: '有人一起刷题吗？', created_at: new Date(Date.now() - 90000000).toISOString() },
    { id: 302, sender_id: 0, content: '我可以～ 约几点？', created_at: new Date(Date.now() - 89800000).toISOString() },
    { id: 303, sender_id: 2, content: '晚上 8 点图书馆见。', created_at: new Date(Date.now() - 89600000).toISOString() },
    { id: 304, sender_id: 1, content: '+1', created_at: new Date(Date.now() - 89400000).toISOString() },
  ],
};

/** mock 会话中 sender_id 对应的昵称（用于头像首字） */
const mockSenderMap = {
  0: { name: 'JoyTrunk 助手' },
  2: { name: '张三' },
};

/** 实际会话也需能显示 JoyTrunk 回复（sender_id=0），与 mock 共用 0 的展示名 */
const imSenderMap = computed(() => ({ 0: { name: 'JoyTrunk 助手' }, ...mockSenderMap }));

const conversations = ref([]);
const currentId = ref(null);
const loading = ref(true);
const showCreate = ref(false);
const showGroupInfo = ref(false);
const currentUserId = ref(null);
const me = ref(null);

/** 左侧展示的会话：有后端数据用后端，否则用 mock */
const displayConversations = computed(() => {
  if (conversations.value.length > 0) return conversations.value;
  return MOCK_CONVERSATIONS;
});

/** 移动端搜索过滤后的会话列表 */
const filteredConversations = computed(() => {
  const list = displayConversations.value;
  const q = (searchQuery.value || '').trim().toLowerCase();
  if (!q) return list;
  return list.filter((c) => (c.title || '').toLowerCase().includes(q) || String(c.id).toLowerCase().includes(q));
});

const currentConversation = computed(() => {
  if (currentId.value == null) return null;
  const list = conversations.value.length > 0 ? conversations.value : MOCK_CONVERSATIONS;
  return list.find((c) => String(c.id) === String(currentId.value)) || null;
});

/** 当前会话若为 mock，则传入对应 mock 消息 */
const currentMockMessages = computed(() => {
  if (currentId.value == null || typeof currentId.value !== 'string') return null;
  const list = MOCK_MESSAGES[currentId.value];
  return Array.isArray(list) ? list : null;
});

async function loadConversations() {
  try {
    conversations.value = await api.im.conversations();
    const mobile = isMobile?.value ?? false;
    if (conversations.value.length > 0) {
      if (!currentId.value && !mobile) currentId.value = conversations.value[0].id;
    } else {
      if (!currentId.value && !mobile) currentId.value = MOCK_CONVERSATIONS[0].id;
    }
  } catch {
    conversations.value = [];
    const mobile = isMobile?.value ?? false;
    if (!currentId.value && !mobile) currentId.value = MOCK_CONVERSATIONS[0].id;
  } finally {
    loading.value = false;
  }
}

async function loadCurrentUser() {
  try {
    const user = await api.users.me();
    me.value = user;
    if (user && user.id != null) currentUserId.value = user.id;
  } catch {
    me.value = null;
    const id = api.getOwnerId && api.getOwnerId();
    if (id) currentUserId.value = Number(id) || id;
  }
}

function onConversationCreated(id) {
  showCreate.value = false;
  loadConversations().then(() => {
    currentId.value = id;
  });
}

function onLeaveOrDismiss() {
  showGroupInfo.value = false;
  const prevId = currentId.value;
  loadConversations().then(() => {
    if (currentId.value === prevId) {
      const list = conversations.value.length > 0 ? conversations.value : MOCK_CONVERSATIONS;
      currentId.value = list.length ? list[0].id : null;
    }
  });
}

function connectImWs() {
  // 优先 localStorage token；无 token 时用当前用户 id 作 fallback（后端 ALLOW_X_OWNER_ID_FALLBACK 时接受数字）
  const token = getToken() || (currentUserId.value != null ? String(currentUserId.value) : null);
  if (!token) return;
  const base = getBase();
  let wsUrl;
  if (!base) {
    const proto = typeof location !== 'undefined' && location.protocol === 'https:' ? 'wss:' : 'ws:';
    wsUrl = `${proto}//${typeof location !== 'undefined' ? location.host : ''}/ws/im`;
  } else {
    const isSecure = base.startsWith('https');
    const host = base.replace(/^https?:\/\//, '').replace(/\/.*$/, '');
    wsUrl = (isSecure ? 'wss:' : 'ws:') + '//' + host + '/ws/im';
  }
  try {
    imWs = new WebSocket(wsUrl);
    imWs.onopen = () => {
      imWs.send(JSON.stringify({ type: 'auth', token }));
    };
    imWs.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'auth_ok') return;
        if (msg.type === 'joytrunk_reply') {
          const convMatch = currentId.value != null && String(msg.conversation_id) === String(currentId.value);
          if (typeof console !== 'undefined' && console.log) {
            console.log('[IM] joytrunk_reply', 'conv_id=', msg.conversation_id, 'currentId=', currentId.value, 'match=', convMatch, 'len=', (msg.content || '').length);
          }
          if (convMatch) {
            const raw = chatPaneRef.value;
            const pane = Array.isArray(raw) ? raw.find((p) => p && typeof p.appendJoytrunkReply === 'function') : raw;
            if (pane && typeof pane.appendJoytrunkReply === 'function') {
              pane.appendJoytrunkReply(msg.content || '', msg.status, msg.error);
            }
          }
        }
      } catch (_) {}
    };
    imWs.onclose = () => {
      imWs = null;
    };
    imWs.onerror = () => {}
  } catch (_) {}
}

onMounted(() => {
  loadCurrentUser().then(() => {
    connectImWs();
  });
  loadConversations();
});

onUnmounted(() => {
  if (imWs) {
    imWs.close();
    imWs = null;
  }
});
</script>

<style scoped>
.im-page {
  display: flex;
  flex: 1;
  min-height: 0;
  height: 100%;
  font-family: 'Segoe UI', system-ui, sans-serif;
  background: var(--jt-bg);
  overflow: hidden;
  border-radius: 0;
}
.im-page :deep(.im-chat-pane) {
  min-height: 0;
}
.im-page :deep(.im-conversation-list) {
  flex-shrink: 0;
  min-height: 0;
}
.im-page-mobile {
  display: block;
  min-height: 100%;
  height: 100%;
}
.im-mobile-view {
  height: 100%;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.im-mobile-view :deep(.im-conversation-list) {
  flex: 1;
  width: 100%;
  max-width: none;
  min-width: 0;
}
.im-mobile-view :deep(.im-chat-pane) {
  flex: 1;
  min-height: 0;
}
.im-mobile-search {
  flex-shrink: 0;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid var(--jt-border);
  background: var(--jt-card-bg);
}
.im-mobile-search-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  font-size: 0.9375rem;
  border: 1px solid var(--jt-border);
  border-radius: 10px;
  background: var(--jt-bg);
  color: var(--jt-text);
}
.im-mobile-search-input::placeholder {
  color: var(--jt-text-muted);
}
.im-mobile-search-input:focus {
  outline: none;
  border-color: var(--jt-primary);
}
.mobile-btn-plus {
  width: 44px;
  height: 44px;
  margin: -4px 0 -4px -8px;
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
.mobile-btn-plus:hover {
  background: color-mix(in srgb, var(--jt-primary) 12%, transparent);
  color: var(--jt-primary);
}
.mobile-btn-plus svg {
  width: 24px;
  height: 24px;
}
/* 进入聊天详情：从右侧滑入 */
.slide-from-right-enter-active,
.slide-from-right-leave-active,
.slide-from-left-enter-active,
.slide-from-left-leave-active {
  transition: transform 0.25s ease;
}
.slide-from-right-enter-from {
  transform: translateX(100%);
}
.slide-from-right-enter-to {
  transform: translateX(0);
}
.slide-from-right-leave-from {
  transform: translateX(0);
}
.slide-from-right-leave-to {
  transform: translateX(-100%);
}
.slide-from-left-enter-from {
  transform: translateX(-100%);
}
.slide-from-left-enter-to {
  transform: translateX(0);
}
.slide-from-left-leave-from {
  transform: translateX(0);
}
.slide-from-left-leave-to {
  transform: translateX(100%);
}
</style>

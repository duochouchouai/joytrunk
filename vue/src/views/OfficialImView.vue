<template>
  <div class="im-page">
    <ImConversationList
      :conversations="conversations"
      :current-id="currentId"
      :loading="loading"
      @select="currentId = $event"
      @new-conversation="showCreate = true"
    />
    <ImChatPane
      :conversation-id="currentId"
      :current-user-id="currentUserId"
      :conversation="currentConversation"
      @read="loadConversations"
      @open-group-info="showGroupInfo = true"
    />
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
import { ref, computed, onMounted } from 'vue';
import { api } from '../api';
import ImConversationList from '../components/im/ImConversationList.vue';
import ImChatPane from '../components/im/ImChatPane.vue';
import ImCreateConversation from '../components/im/ImCreateConversation.vue';
import ImGroupInfo from '../components/im/ImGroupInfo.vue';

const conversations = ref([]);
const currentId = ref(null);
const loading = ref(true);
const showCreate = ref(false);
const showGroupInfo = ref(false);
const currentUserId = ref(null);

const currentConversation = computed(() =>
  currentId.value != null ? conversations.value.find((c) => c.id === currentId.value) || null : null
);

async function loadConversations() {
  try {
    conversations.value = await api.im.conversations();
    if (conversations.value.length && !currentId.value) currentId.value = conversations.value[0].id;
  } catch {
    conversations.value = [];
  } finally {
    loading.value = false;
  }
}

async function loadCurrentUser() {
  try {
    const me = await api.users.me();
    if (me && me.id != null) currentUserId.value = me.id;
  } catch {
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
      currentId.value = conversations.value.length ? conversations.value[0].id : null;
    }
  });
}

onMounted(() => {
  loadCurrentUser();
  loadConversations();
});
</script>

<style scoped>
.im-page {
  display: flex;
  height: 100%;
  min-height: 60vh;
  font-family: 'Segoe UI', system-ui, sans-serif;
}
</style>

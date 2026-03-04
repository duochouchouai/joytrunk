<template>
  <header class="mobile-title-bar">
    <div class="mobile-title-bar-inner">
      <div v-if="$slots.left" class="mobile-title-bar-left">
        <slot name="left" />
      </div>
      <h1 class="mobile-title-bar-title">{{ title }}</h1>
      <div v-if="$slots.right" class="mobile-title-bar-right">
        <slot name="right" />
      </div>
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
});
</script>

<style scoped>
.mobile-title-bar {
  flex-shrink: 0;
  padding-top: env(safe-area-inset-top, 0);
  background: var(--jt-card-bg);
  border-bottom: 1px solid var(--jt-border);
}
.mobile-title-bar-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  min-height: 48px;
  padding: 0 0.5rem 0 0.25rem;
}
.mobile-title-bar-left,
.mobile-title-bar-right {
  flex-shrink: 0;
  min-width: 44px;
  display: flex;
  align-items: center;
}
.mobile-title-bar-right {
  justify-content: flex-end;
}
.mobile-title-bar-title {
  flex: 1;
  margin: 0;
  font-size: 1.0625rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--jt-text);
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>

<template>
  <div class="app">
    <router-view />
  </div>
</template>

<script setup>
import { useTheme } from './composables/useTheme'
useTheme()
</script>

<style>
.app { min-height: 100vh; }
</style>

<template>
  <v-app>
    <v-main>
      <v-container fluid>
        <!-- 本地预览壳：联邦模式下由宿主直接加载 components 下的组件 -->
        <div class="text-h6 mb-3">爱快时光机 · 本地预览</div>
        <Config :initial-config="{}" :api="mockApi" />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
const mockApi = {
  get: async () => ({}),
  post: async () => ({}),
}
</script>

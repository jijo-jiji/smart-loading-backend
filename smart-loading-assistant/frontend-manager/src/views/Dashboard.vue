<script setup>
import Sidebar from '../components/ui/Sidebar.vue'
import ManifestDetails from '../components/ui/ManifestDetails.vue'
import SceneManager from '../components/scene/SceneManager.vue'
</script>

<template>
  <div class="flex h-screen w-full bg-white text-gray-900">
    <Sidebar />
    <ManifestDetails />
    <SceneManager />
  </div>
</template>

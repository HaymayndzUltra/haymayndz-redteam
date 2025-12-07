<template>
  <div class="app">
    <header class="header">
      <h1>Panel Dashboard</h1>
      <nav>
        <a href="#home">Home</a>
        <a href="#logs">Logs</a>
        <a href="#traffic">Traffic</a>
        <a href="#phishlets">Phishlets</a>
        <a href="#config">Config</a>
      </nav>
    </header>
    <main class="main">
      <p>Dashboard loading...</p>
    </main>
  </div>
</template>

<script setup>
// Vue 3 Composition API
</script>

<style>
.app {
  font-family: system-ui, -apple-system, sans-serif;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}
.header nav a {
  margin-left: 20px;
  text-decoration: none;
  color: #333;
}
</style>


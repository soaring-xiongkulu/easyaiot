<template>
  <div id="app">
    <nav class="navbar">
      <div class="nav-brand">
        <h2>AI平台</h2>
      </div>
      <ul class="nav-links">
        <li><router-link to="/">首页</router-link></li>
        <li><router-link to="/ai-models">AI模型</router-link></li>
        <li><router-link to="/tasks">任务</router-link></li>
        <li><router-link to="/train">模型训练</router-link></li>
      </ul>
    </nav>
    <main class="main-content">
      <router-view/>
    </main>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #2c3e50;
  color: white;
  padding: 1rem 2rem;
}

.nav-brand h2 {
  margin: 0;
}

.nav-links {
  display: flex;
  list-style-type: none;
}

.nav-links li {
  margin-left: 2rem;
}

.nav-links a {
  color: white;
  text-decoration: none;
  font-weight: bold;
}

.nav-links a.router-link-exact-active {
  color: #42b983;
}

.main-content {
  padding: 2rem;
  min-height: calc(100vh - 4rem);
}
</style>
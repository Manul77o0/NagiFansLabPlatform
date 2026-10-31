<script setup>
import { ref, onMounted } from 'vue'
import { api } from './api'


// リアクティブな状態（データ）の定義
const isLoggedIn = ref(false)
const user = ref(null)
const items = ref([])
const username = ref('')
const password = ref('')
const message = ref('')

const loadCurrentUser = async () => {
  try {
    const response = await api.get('/api/users/me')
    user.value = response.data
    isLoggedIn.value = true
    await loadItems()
  } catch (error) {
    if (error.response?.status === 401) {
      isLoggedIn.value = false
      user.value = null
    } else {
      message.value = 'ユーザー情報を取得できませんでした'
    }
  }
}

const loadItems = async () => {
  try {
    const response = await api.get('/api/users/me/items/')
    items.value = response.data
  } catch (error) {
    message.value = 'アイテムを取得できませんでした'
  }
}

const handleLogin = async () => {
  message.value = ''
  try {
    await api.post('/api/session/login', {
      username: username.value,
      password: password.value,
    })
    username.value = ''
    password.value = ''
    await loadCurrentUser()
  } catch (error) {
    if (error.response?.status === 401) {
      message.value = 'ユーザー名またはパスワードが正しくありません'
    } else {
      message.value = 'ログインに失敗しました'
    }
  }
}

const handleLogout = async () => {
  message.value = ''
  try {
    await api.post('/api/session/logout')
    isLoggedIn.value = false
    user.value = null
    items.value = []
  } catch (error) {
    message.value = 'ログアウトに失敗しました'
  }
}

onMounted(() => {
  loadCurrentUser()
})
</script>

<template>
  <div>
    <h1>NagiFans Lab</h1>
    <p>NagiFans Lab へようこそ</p>

    <section v-if="!isLoggedIn">
      <p>ゲスト さん</p>
      <form @submit.prevent="handleLogin">
        <label for="username">ユーザー名:</label>
        <input type="text" id="username" v-model="username" autocomplete="username" required>
        
        <label for="password">パスワード:</label>
        <input type="password" id="password" v-model="password" autocomplete="current-password" required>
        
        <button type="submit">ログイン</button>
      </form>
    </section>

    <section v-else>
      <p>こんにちは、{{ user?.username }} さん</p>
      <button type="button" @click="handleLogout">ログアウト</button>
      
      <h2>APIから取得したアイテム</h2>
      <ul>
        <li v-for="item in items" :key="item.item_id">
          {{ item.item_id }} (owner: {{ item.owner }})
        </li>
      </ul>
    </section>

    <p role="status" aria-live="polite">{{ message }}</p>
  </div>
</template>
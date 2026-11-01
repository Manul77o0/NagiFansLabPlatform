<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../components/api'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const isLoggedIn = ref(false)
const user = ref(null)
const items = ref([])
const username = ref('')
const password = ref('')
const formdisplayMsg = ref('')
const cmdisplayMsg = ref('')
const isForbidden = ref(false)
const isAPIError = ref(false)

const loadCurrentUser = async () => {
  try {
    const response = await api.get('/api/users/me')
    user.value = response.data
    isLoggedIn.value = true
    if (user.value.level >= 3) {
      isUserAdmin.value = true
      return 'Admin'
    }
    return 'User'
  } catch (error) {
    if (error.response?.status === 401) {
      isLoggedIn.value = false
      user.value = null
      return 'Guest'
    } else if (error.response?.status === 400) {
      isLoggedIn.value = false
      user.value = null
      return 'Inactive'
    } else {
      isAPIError.value = true
      return 'APIError'
    }
  }
}

const loadItems = async () => {
  try {
    const response = await api.get('/api/users/me/tools/')
    items.value = response.data
  } catch (error) {
    cmdisplayMsg.value = '通信エラーが発生しました、再度お試しください'
  }
}

const handleLogin = async () => {
  cmdisplayMsg.value = ''
  formdisplayMsg.value = ''
  try {
    await api.post('/api/session/login', {
      username: username.value,
      password: password.value,
    })
    username.value = ''
    password.value = ''
    const state = await loadCurrentUser()
    if (state === 'APIError'){
        formdisplayMsg.value = '通信エラーが発生しました、再度お試しください'
    }
    const redirectPath = route.query.redirect
    if (redirectPath && redirectPath.startsWith('/') && !redirectPath.startsWith('//')) {
      router.push(redirectPath)
    } else {
       await loadItems()
    }

  } catch (error) {
    if (error.response?.status === 401) {
      formdisplayMsg.value = 'ユーザー名またはパスワードが正しくありません'
    } else {
      formdisplayMsg.value = '通信エラーが発生しました、再度お試しください'
    }
  }
}

const handleLogout = async () => {
  cmdisplayMsg.value = ''
  formdisplayMsg.value = ''
  try {
    await api.post('/api/session/logout')
    isLoggedIn.value = false
    user.value = null
    items.value = []
  } catch (error) {
    console.log('failed logout')
  }
}

onMounted(async () => {
  const state = await loadCurrentUser()
  if ('redirect' in route.query && 'requiredlogin' in route.query){
      if (state === 'InActive') {
        await handleLogout()
      } 
      formdisplayMsg.value = 'ログインが必要です'
  } else if (state === 'User' && 'requiredadmin' in route.query) {
    isForbidden.value = true
  } else if (isLoggedIn.value) {
    loadItems()
  }
})
</script>

<template>
  <div>
    <h1>NagiFans Lab</h1>
    <p>NagiFans Lab へようこそ</p>

    <section v-if="isAPIError">
      <p>通信エラーが発生しました。</p>
      <p>なお、処理中に遷移した場合、該当処理が完了していない可能性が高いです。</p>
      <p v-if="route.query?.redirect">
        <a :href="route.query.redirect">元のページに戻る</a>
      </p>
      <p v-else><a href="/">TOPへ</a></p>
    </section>

    <section v-else-if="!isLoggedIn">
      <p>ゲスト さん</p>
      <form @submit.prevent="handleLogin">
        <p role="status" aria-live="polite" v-if="formdisplayMsg">{{ formdisplayMsg }}</p>
        <label for="username">ユーザー名:</label>
        <input type="text" id="username" v-model="username" autocomplete="username" required>
        
        <label for="password">パスワード:</label>
        <input type="password" id="password" v-model="password" autocomplete="current-password" required>
        
        <button type="submit">ログイン</button>
      </form>
    </section>

    <section v-else-if="isForbidden">
      <p>こんにちは、{{ user?.displayname }} さん</p>
      <p>申し訳ありませんが、該当のページにアクセスする権限はありません。</p>
      <p><a href="/">TOPへ</a></p>
    </section>

    <section v-else>
      <p>こんにちは、{{ user?.displayname }} さん</p>
      <button type="button" @click="handleLogout">ログアウト</button>
        <ul>
          <li v-for="(toolObj, index) in items.tools" :key="index">
            <span v-for="(path, key) in toolObj" :key="key">
                <strong>{{ key }}</strong>: {{ path }}
            </span>
          </li>
        </ul>
    </section>
    <p role="status" aria-live="polite" v-if="cmdisplayMsg">{{ cmdisplayMsg }}</p>
  </div>
</template>
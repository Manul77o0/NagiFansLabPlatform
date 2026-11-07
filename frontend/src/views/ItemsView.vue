<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../components/api'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const cmdisplayMsg = ref('')
const isLoggedIn = ref(false)
const isUserAdmin = ref(false)
const user = ref(null)
const items = ref([])

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
    const response = await api.get('/api/wg_tools')
    items.value = response.data
  } catch (error) {
    cmdisplayMsg.value = '通信エラーが発生しました、再度お試しください'
  }
}

const handleLogout = async () => {
  try {
    await api.post('/api/session/logout')
    isLoggedIn.value = false
    user.value = null
    items.value = []
    router.push('/')
  } catch (error) {
    console.log('failed logout')
  }
}

onMounted(async () => {
  await loadCurrentUser()
  if (isLoggedIn){
    await loadItems()
  }
})
</script>

<template>
  <div>
    <h1>NagiFans Lab</h1>
    <p>NagiFans Lab へようこそ</p>

    <p role="status" aria-live="polite" v-if="cmdisplayMsg">{{ cmdisplayMsg }}</p>
    <section v-if="!isLoggedIn">
      <p>ゲスト さん</p>
      <p><a href="/?redirect=/admin/users&requiredlogin=true">ログインが必要です</a></p>
    </section>

    <section v-else>
      <p>こんにちは、{{ user?.displayname }} さん</p>
      <button type="button" @click="handleLogout">ログアウト</button>

      <div id="admin_contents" v-if="isLoggedIn">
        TLD..... {{ items }}
      </div>
    </section>

  </div>
</template>
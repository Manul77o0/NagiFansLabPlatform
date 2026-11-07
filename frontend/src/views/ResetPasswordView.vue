<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../components/api'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const isLoggedIn = ref(false)
const isUserAdmin = ref(false)
const user = ref(null)
const items = ref([])
const username = ref('')
const password = ref('')
const formdisplayMsg = ref('')
const cmdisplayMsg = ref('')
const isForbidden = ref(false)
const isAPIError = ref(false)


const handleReset = async () => {
  cmdisplayMsg.value = ''
  formdisplayMsg.value = ''
  try {
    await api.post('/api/reset', {
      new_password: password.value,
      token: route.query.token,
    })
    await handleLogout()
    router.push('/')

  } catch (error) {
    if (error.response?.status === 400) {
      console.log(error.response)
      formdisplayMsg.value = 'リセットに失敗しました：' + error.response?.data?.detail
    } else {
      formdisplayMsg.value = '通信エラーが発生しました、再度お試しください'
    }
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


</script>

<template>
  <div>
    <h1>NagiFans Lab</h1>
    <p>NagiFans Lab へようこそ</p>


    <section >
      <form @submit.prevent="handleReset">
        <p role="status" aria-live="polite" v-if="formdisplayMsg">{{ formdisplayMsg }}</p>
        <label for="password">新規パスワード:</label>
        <input type="password" id="password" v-model="password" autocomplete="current-password" required>
        
        <button type="submit">送信</button>
      </form>
    </section>

    <p role="status" aria-live="polite" v-if="cmdisplayMsg">{{ cmdisplayMsg }}</p>
  </div>
</template>
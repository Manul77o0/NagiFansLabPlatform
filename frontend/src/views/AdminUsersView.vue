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

const cmdisplayMsg = ref('')
const formdisplayMsg = ref('')
const registerusername = ref('')
const registerpassword = ref('')

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
    const response = await api.get('/api/admin/users')
    items.value = response.data
  } catch (error) {
    cmdisplayMsg.value = '通信エラーが発生しました、再度お試しください'
  }
}

const handleRegister = async () => {
  cmdisplayMsg.value = ''
  formdisplayMsg.value = ''
  try {
    await api.post('/api/admin/user/register', {
      username: registerusername.value,
      password: registerusername.value,
    })
    registerusername.value = ''
    registerpassword.value = ''
    await loadItems()

  } catch (error) {
    if (error.response?.status === 400) {
      formdisplayMsg.value = '不正なユーザ名・パスワードです'
    } else if (error.response?.status === 401) {
      formdisplayMsg.value = 'ページを再読み込みしてください'
    } else {
      formdisplayMsg.value = '通信エラーが発生しました、再度お試しください'
    }
  }
}
const enableUser = async (userId) => {
  try {
    await api.post(`/api/admin/user/${userId}/enable`, {})
    await loadItems()

  } catch (error) {
    if (error.response?.status === 400) {
      cmdisplayMsg.value = '不正なユーザIDです'
    } else if (error.response?.status === 401) {
      cmdisplayMsg.value = 'ページを再読み込みしてください'
    } else {
      cmdisplayMsg.value = '通信エラーが発生しました、再度お試しください'
    }
  }
}

const disableUser = async (userId) => {
  try {
    await api.post(`/api/admin/user/${userId}/disable`, {})
    await loadItems()

  } catch (error) {
    if (error.response?.status === 400) {
      cmdisplayMsg.value = '不正なユーザIDです'
    } else if (error.response?.status === 401) {
      cmdisplayMsg.value = 'ページを再読み込みしてください'
    } else {
      cmdisplayMsg.value = '通信エラーが発生しました、再度お試しください'
    }
  }
}

const resetPassword = async (userId) => {
  alert(`TLD.....${userId}`)
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
  if (isUserAdmin){
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
    <section v-else-if="!isUserAdmin">
      <p>こんにちは、{{ user?.displayname }} さん</p>
      <p>申し訳ありませんが、該当のページにアクセスする権限はありません。</p>
      <p><a href="/">TOPへ</a></p>
    </section>

    <section v-else>
      <p>こんにちは、{{ user?.displayname }} さん</p>
      <button type="button" @click="handleLogout">ログアウト</button>

      <div id="admin_contents" v-if="isUserAdmin">
        <h2>ユーザ一覧</h2>
        <ul>
          <li v-for="item_user in items" :key="item_user.id">
            {{ item_user.displayname }} ({{ item_user.email }}) (<a href="#" @click.prevent="resetPassword(item_user.id)">表示名変更</a> | <a href="#" @click.prevent="resetPassword(item_user.id)">パスワード初期化</a> | <a href="#" @click.prevent="disableUser(item_user.id)" v-if="!item_user.disabled">無効化</a><a href="#" @click.prevent="enableUser(item_user.id)" v-if="item_user.disabled">有効化</a>)
          </li>
        </ul>
        <h2>ユーザ追加</h2>
        <form @submit.prevent="handleRegister">
        <p role="status" aria-live="polite" v-if="formdisplayMsg">{{ formdisplayMsg }}</p>
        <label for="username">ユーザー名:</label>
        <input type="text" id="registerusername" v-model="registerusername" required>
        
        <label for="password">パスワード:</label>
        <input type="password" id="registerpassword" v-model="registerpassword" required>
        
        <button type="submit">登録</button>
      </form>
      </div>
    </section>

  </div>
</template>
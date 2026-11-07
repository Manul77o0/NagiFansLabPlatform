<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../components/api'
import { useRoute, useRouter } from 'vue-router'
import AuthLayout from '../components/AuthLayout.vue'

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
const isSubmitting = ref(false)

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
  isSubmitting.value = true
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
  } finally {
    isSubmitting.value = false
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
  <AuthLayout
    v-if="isAPIError"
    form-label="接続エラー"
    :show-intro="false"
  >
    <div class="auth-form">
      <h2 class="form-title">通信エラーが発生しました</h2>
      <p class="form-description">処理中に画面を移動した場合、操作が完了していない可能性があります。</p>
      <a
        v-if="route.query?.redirect"
        class="auth-submit auth-link-button"
        :href="route.query.redirect"
      >元のページに戻る</a>
      <a v-else class="auth-submit auth-link-button" href="/">TOPへ戻る</a>
    </div>
  </AuthLayout>

  <AuthLayout
    v-else-if="!isLoggedIn"
    form-label="MEMBER SIGN IN"
    :show-intro="false"
  >
    <form class="auth-form" @submit.prevent="handleLogin">
      <h2 class="form-title">おかえりなさい</h2>
      <p class="form-description">アカウントにログインしてください。</p>

      <p v-if="formdisplayMsg" class="form-message" role="alert" aria-live="polite">
        <span class="message-icon" aria-hidden="true">!</span>{{ formdisplayMsg }}
      </p>

      <div class="form-field">
        <label for="username">ユーザー名</label>
        <input
          id="username"
          v-model="username"
          type="text"
          autocomplete="username"
          placeholder="ユーザー名を入力"
          required
          :disabled="isSubmitting"
        >
      </div>

      <div class="form-field">
        <div class="field-label-row">
          <label for="password">パスワード</label>
        </div>
        <input
          id="password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          placeholder="パスワードを入力"
          required
          :disabled="isSubmitting"
        >
      </div>

      <button class="auth-submit" type="submit" :disabled="isSubmitting">
        <span>{{ isSubmitting ? 'ログイン中...' : 'ログイン' }}</span>
        <span v-if="!isSubmitting" class="submit-arrow" aria-hidden="true">→</span>
        <span v-else class="submit-spinner" aria-hidden="true"></span>
      </button>
    </form>

  </AuthLayout>

  <main v-else class="signed-in-page">
    <header class="signed-in-header">
      <a href="/" class="signed-in-brand">NagiFans <strong>Lab</strong></a>
      <button class="logout-button" type="button" @click="handleLogout">ログアウト</button>
    </header>
    <section v-if="isForbidden" class="signed-in-card">
      <span class="signed-in-icon" aria-hidden="true">!</span>
      <h1>アクセス権限がありません</h1>
      <p>申し訳ありませんが、該当のページにアクセスする権限はありません。</p>
      <a href="/">TOPへ戻る</a>
    </section>
    <section v-else class="signed-in-card">
      <p class="signed-in-eyebrow">YOUR WORKSPACE</p>
      <h1>こんにちは、{{ user?.displayname }} さん</h1>
      <p>使用可能なツール</p>
      <ul class="tool-list">
        <li v-for="(toolObj, index) in items.tools" :key="index">
          <a v-for="(path, key) in toolObj" :key="key" :href="path">{{ key }} <span aria-hidden="true">→</span></a>
        </li>
      </ul>
    </section>
    <p v-if="cmdisplayMsg" class="signed-in-message" role="status" aria-live="polite">{{ cmdisplayMsg }}</p>
  </main>
</template>

<style scoped>
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 19px;
}

.form-title {
  margin: 0;
  color: #243d52;
  font-size: 25px;
  font-weight: 720;
  letter-spacing: -0.045em;
}

.form-description {
  margin: -11px 0 2px;
  color: #8494a2;
  font-size: 12px;
  line-height: 1.7;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-field label {
  color: #42596c;
  font-size: 12px;
  font-weight: 650;
}

.form-field input {
  box-sizing: border-box;
  width: 100%;
  height: 47px;
  padding: 0 13px;
  border: 1px solid #dfe7ed;
  border-radius: 8px;
  outline: none;
  color: #30485d;
  background: #fbfcfd;
  font: inherit;
  font-size: 13px;
  transition: border-color 150ms ease, box-shadow 150ms ease, background 150ms ease;
}

.form-field input::placeholder { color: #b0bbc4; }
.form-field input:focus {
  border-color: #78a9d2;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(40, 116, 200, 0.1);
}
.form-field input:disabled { opacity: 0.65; }

.auth-submit {
  min-height: 48px;
  box-sizing: border-box;
  margin-top: 3px;
  padding: 0 17px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 0;
  border-radius: 8px;
  color: #fff;
  background: linear-gradient(100deg, #2874c8, #3186c9);
  box-shadow: 0 7px 15px rgba(40, 116, 200, 0.19);
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  transition: filter 140ms ease, transform 140ms ease, box-shadow 140ms ease;
}

.auth-submit:hover:not(:disabled) {
  filter: brightness(1.04);
  box-shadow: 0 9px 18px rgba(40, 116, 200, 0.25);
  transform: translateY(-1px);
}

.auth-submit:focus-visible,
.reset-prompt a:focus-visible {
  outline: 3px solid rgba(40, 116, 200, 0.3);
  outline-offset: 3px;
}

.auth-submit:disabled { opacity: 0.72; cursor: wait; }
.auth-link-button { width: fit-content; padding: 0 24px; }
.submit-arrow { margin-left: auto; font-size: 17px; font-weight: 400; }
.submit-spinner {
  width: 15px;
  height: 15px;
  border: 2px solid rgba(255, 255, 255, 0.45);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.form-message {
  margin: -2px 0 0;
  padding: 11px 12px;
  display: flex;
  align-items: flex-start;
  gap: 9px;
  border: 1px solid #f1d9d4;
  border-radius: 8px;
  color: #a24f44;
  background: #fff8f6;
  font-size: 11px;
  line-height: 1.65;
}

.message-icon {
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  background: #d77a69;
  font-size: 10px;
  font-weight: 700;
}

.signed-in-page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 0 6%;
  color: #243d52;
  background: #f5f8fb;
  font-family: "Mona Sans VF", -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
}

.signed-in-header {
  max-width: 1120px;
  height: 78px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.signed-in-brand {
  color: #1d3448;
  font-size: 15px;
  font-weight: 650;
  text-decoration: none;
}

.signed-in-brand strong { color: #2874c8; }
.logout-button {
  padding: 8px 13px;
  border: 1px solid #dfe7ed;
  border-radius: 7px;
  color: #607487;
  background: #fff;
  font: inherit;
  font-size: 11px;
  cursor: pointer;
}

.signed-in-card {
  max-width: 700px;
  box-sizing: border-box;
  margin: 8vh auto 0;
  padding: 38px;
  border: 1px solid #e8eef3;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 18px 45px rgba(36, 68, 93, 0.07);
}

.signed-in-eyebrow { color: #6c9ab7 !important; font-size: 10px !important; font-weight: 700; letter-spacing: 0.13em; }
.signed-in-card h1 { margin: 10px 0 12px; font-size: 24px; letter-spacing: -0.03em; }
.signed-in-card p { color: #7b8d9c; font-size: 13px; }
.signed-in-card > a { color: #2874c8; font-size: 12px; text-decoration: none; }
.signed-in-icon {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  color: #ae6a55;
  background: #fff2ec;
  font-weight: 700;
}

.tool-list { margin: 22px 0 0; padding: 0; list-style: none; }
.tool-list li + li { margin-top: 9px; }
.tool-list a {
  padding: 14px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid #e8eef3;
  border-radius: 8px;
  color: #38536a;
  background: #fbfcfd;
  font-size: 13px;
  text-decoration: none;
}

.tool-list a:hover { border-color: #b7d2e7; background: #f6fbfe; }
.tool-list a span { color: #6296bc; font-size: 17px; }
.signed-in-message { max-width: 700px; margin: 15px auto; color: #a24f44; font-size: 12px; }

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 540px) {
  .signed-in-page { padding: 0 20px; }
  .signed-in-card { margin-top: 36px; padding: 25px 22px; }
}
</style>
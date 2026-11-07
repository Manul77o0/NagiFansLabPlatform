<script setup>
import { ref } from 'vue'
import { api } from '../components/api'
import AuthLayout from '../components/AuthLayout.vue'

const username = ref('')
const password = ref('')
const passwordConfirmation = ref('')
const setupToken = ref('')
const message = ref('')
const completed = ref(false)
const submitting = ref(false)

const submit = async () => {
  message.value = ''
  if (password.value !== passwordConfirmation.value) {
    message.value = 'パスワードが一致しません。'
    return
  }
  submitting.value = true
  try {
    await api.post('/api/setup/initial-admin', {
      username: username.value,
      password: password.value,
      setup_token: setupToken.value,
    })
    password.value = ''
    passwordConfirmation.value = ''
    setupToken.value = ''
    completed.value = true
  } catch (error) {
    const code = error.response?.status
    message.value = code === 403
      ? 'セットアップトークンが正しくありません。'
      : code === 409
        ? '初期登録は完了済みです。'
        : code === 503
          ? '初期登録が設定されていません。サーバーの設定を確認してください。'
          : code === 422
            ? 'ユーザー名、パスワード、トークンの入力内容を確認してください。'
            : '登録できませんでした。サーバーの状態を確認してください。'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AuthLayout form-label="INITIAL SETUP" :show-intro="false">
    <div v-if="completed" class="setup-form">
      <h2>初期管理者を登録しました</h2>
      <p>サーバーのセットアップトークンを削除し、サービスを再起動してください。</p>
      <router-link to="/">ログイン画面へ</router-link>
    </div>
    <form v-else class="setup-form" @submit.prevent="submit">
      <h2>初期管理者の登録</h2>
      <p>ユーザーがまだ存在しない場合に、一度だけ登録できます。</p>
      <p v-if="message" class="error" role="alert">{{ message }}</p>
      <label for="setup-username">ユーザー名</label>
      <input id="setup-username" v-model="username" required maxlength="64"
        pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,63}" autocomplete="username"
        :disabled="submitting">
      <small>半角英数字で始め、半角英数字・ドット・ハイフン・アンダースコアを使用できます。</small>
      <label for="setup-password">パスワード</label>
      <input id="setup-password" v-model="password" type="password" required
        minlength="12" maxlength="256" autocomplete="new-password" :disabled="submitting">
      <small>12文字以上で入力してください。</small>
      <label for="setup-password-confirmation">パスワード（確認）</label>
      <input id="setup-password-confirmation" v-model="passwordConfirmation"
        type="password" required minlength="12" maxlength="256"
        autocomplete="new-password" :disabled="submitting">
      <label for="setup-token">セットアップトークン</label>
      <input id="setup-token" v-model="setupToken" type="password" required
        minlength="32" maxlength="256" autocomplete="off" :disabled="submitting">
      <button type="submit" :disabled="submitting">
        {{ submitting ? '登録中...' : '管理者を登録' }}
      </button>
      <router-link to="/">ログイン画面へ戻る</router-link>
    </form>
  </AuthLayout>
</template>

<style scoped>
.setup-form { display: flex; flex-direction: column; gap: 10px; color: #30485d; }
.setup-form h2 { margin: 0; font-size: 24px; }
.setup-form p, .setup-form small { font-size: 12px; line-height: 1.6; }
.setup-form label { font-size: 12px; font-weight: 650; }
.setup-form input { box-sizing: border-box; width: 100%; padding: 12px; border: 1px solid #dfe7ed; border-radius: 8px; font: inherit; }
.setup-form button { padding: 14px; border: 0; border-radius: 8px; color: white; background: #2874c8; font: inherit; cursor: pointer; }
.setup-form button:disabled { opacity: 0.7; cursor: wait; }
.setup-form .error { color: #a24f44; }
</style>

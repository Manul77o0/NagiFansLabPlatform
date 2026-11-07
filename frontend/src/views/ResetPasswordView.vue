<script setup>
import { ref } from 'vue'
import { api } from '../components/api'
import { useRoute, useRouter } from 'vue-router'
import AuthLayout from '../components/AuthLayout.vue'

const route = useRoute()
const router = useRouter()

const password = ref('')
const formdisplayMsg = ref('')
const isSubmitting = ref(false)


const handleReset = async () => {
  formdisplayMsg.value = ''
  isSubmitting.value = true
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
  } finally {
    isSubmitting.value = false
  }
}

const handleLogout = async () => {
  try {
    await api.post('/api/session/logout')
    router.push('/')
  } catch (error) {
    console.log('failed logout')
  }
}


</script>

<template>
  <AuthLayout
    form-label="PASSWORD RESET"
    :show-intro="false"
  >
    <form class="reset-form" @submit.prevent="handleReset">
      <h2 class="form-title">新しいパスワード</h2>
      <p class="form-description">今後のログインに使うパスワードを入力してください。</p>

      <p v-if="formdisplayMsg" class="form-message" role="alert" aria-live="polite">
        <span class="message-icon" aria-hidden="true">!</span>{{ formdisplayMsg }}
      </p>

      <div class="form-field">
        <label for="new-password">新規パスワード</label>
        <input
          id="new-password"
          v-model="password"
          type="password"
          autocomplete="new-password"
          placeholder="新しいパスワードを入力"
          required
          :disabled="isSubmitting"
        >
        <span class="field-hint">安全のため、他のサービスと異なるパスワードを設定してください。</span>
      </div>

      <button class="auth-submit" type="submit" :disabled="isSubmitting">
        <span>{{ isSubmitting ? '更新中...' : 'パスワードを更新' }}</span>
        <span v-if="!isSubmitting" class="submit-arrow" aria-hidden="true">→</span>
        <span v-else class="submit-spinner" aria-hidden="true"></span>
      </button>
    </form>

  </AuthLayout>
</template>

<style scoped>
.reset-form {
  display: flex;
  flex-direction: column;
  gap: 19px;
}

.form-title {
  margin: 0;
  color: #243d52;
  font-size: 24px;
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

.field-hint {
  color: #93a1ad;
  font-size: 10px;
  line-height: 1.65;
}

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
  cursor: pointer;
  transition: filter 140ms ease, transform 140ms ease, box-shadow 140ms ease;
}

.auth-submit:hover:not(:disabled) {
  filter: brightness(1.04);
  box-shadow: 0 9px 18px rgba(40, 116, 200, 0.25);
  transform: translateY(-1px);
}

.auth-submit:focus-visible {
  outline: 3px solid rgba(40, 116, 200, 0.3);
  outline-offset: 3px;
}

.auth-submit:disabled { opacity: 0.72; cursor: wait; }
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

@keyframes spin { to { transform: rotate(360deg); } }
</style>
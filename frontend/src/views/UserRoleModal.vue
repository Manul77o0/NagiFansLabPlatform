<script setup>
import { ref } from 'vue'
import { api } from '../components/api'

const props = defineProps({
  user: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'success'])

const level = ref(props.user.level)
const isLoading = ref(false)
const errorMessage = ref('')

const roleName = (value) => ({
  1: '読み取りユーザー',
  2: '書き込みユーザー',
  3: '管理ユーザー'
}[value] || '未設定')

const handleSubmit = async () => {
  if (![1, 2, 3].includes(level.value)) {
    errorMessage.value = '権限を選択してください。'
    return
  }

  if (level.value === props.user.level) {
    emit('close')
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await api.post(`/api/admin/user/${props.user.id}/level`, {
      level: level.value
    })
    emit('success', response.data)
  } catch (error) {
    if (error.response?.status === 400) {
      errorMessage.value = '自分自身または存在しないユーザーの権限は変更できません。'
    } else if (error.response?.status === 401) {
      errorMessage.value = 'ページを再読み込みしてください。'
    } else if (error.response?.status === 403) {
      errorMessage.value = '権限を変更するには管理者権限が必要です。'
    } else if (error.response?.status === 409) {
      errorMessage.value = '有効な管理者が1人以上必要なため、変更できません。'
    } else if (error.response?.status === 422) {
      errorMessage.value = '権限の指定が不正です。'
    } else {
      errorMessage.value = '通信エラーが発生しました。再度お試しください。'
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="role-modal-overlay" @click.self="!isLoading && emit('close')">
    <section
      class="role-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="role-modal-title"
    >
      <header class="role-modal-heading">
        <span class="role-modal-icon" aria-hidden="true">権</span>
        <div>
          <h2 id="role-modal-title">権限変更</h2>
          <p>{{ user.displayname }} <span>・</span> {{ user.email }}</p>
        </div>
        <button
          class="role-modal-close"
          type="button"
          aria-label="閉じる"
          :disabled="isLoading"
          @click="emit('close')"
        >×</button>
      </header>

      <form @submit.prevent="handleSubmit">
        <label class="role-modal-label" for="user-role">新しい権限</label>
        <select id="user-role" v-model.number="level" :disabled="isLoading">
          <option :value="1">読み取りユーザー</option>
          <option :value="2">書き込みユーザー</option>
          <option :value="3">管理ユーザー</option>
        </select>
        <p class="role-modal-current">現在の権限：{{ roleName(user.level) }}</p>

        <p v-if="errorMessage" class="role-modal-error" role="alert" aria-live="polite">
          {{ errorMessage }}
        </p>

        <div class="role-modal-actions">
          <button type="button" :disabled="isLoading" @click="emit('close')">キャンセル</button>
          <button type="submit" :disabled="isLoading">
            {{ isLoading ? '変更中…' : '変更を保存' }}
          </button>
        </div>
      </form>
    </section>
  </div>
</template>

<style scoped>
.role-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(20, 36, 52, 0.42);
  backdrop-filter: blur(3px);
}

.role-modal {
  box-sizing: border-box;
  width: min(100%, 430px);
  padding: 25px;
  border: 1px solid rgba(226, 235, 243, 0.9);
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 24px 70px rgba(20, 42, 63, 0.22);
}

.role-modal-heading {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.role-modal-icon {
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  border-radius: 11px;
  color: #3479b7;
  background: #edf5fc;
  font-size: 15px;
  font-weight: 700;
}

.role-modal-heading h2 {
  margin: 0;
  color: #263a4d;
  font-size: 17px;
  font-weight: 700;
}

.role-modal-heading p {
  margin: 5px 0 0;
  color: #8997a4;
  font-size: 11px;
}

.role-modal-heading p span {
  margin: 0 3px;
  color: #bdc7cf;
}

.role-modal-close {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  margin-left: auto;
  border: 0;
  border-radius: 7px;
  color: #82909d;
  background: transparent;
  font-size: 22px;
  cursor: pointer;
}

.role-modal-close:hover:not(:disabled) {
  color: #34495c;
  background: #f2f5f8;
}

.role-modal-label {
  display: block;
  margin-bottom: 7px;
  color: #526579;
  font-size: 12px;
  font-weight: 650;
}

.role-modal select {
  box-sizing: border-box;
  width: 100%;
  height: 42px;
  padding: 0 11px;
  border: 1px solid #e3eaf0;
  border-radius: 7px;
  outline: 0;
  color: #34495c;
  background: #fcfdfe;
  font: inherit;
  font-size: 13px;
}

.role-modal select:focus {
  border-color: #92bce0;
  box-shadow: 0 0 0 3px rgba(40, 116, 200, 0.08);
}

.role-modal-current {
  margin: 9px 0 0;
  color: #8997a4;
  font-size: 11px;
}

.role-modal-error {
  margin: 17px 0 0;
  padding: 9px 10px;
  border: 1px solid #f2d9d4;
  border-radius: 6px;
  color: #a74f43;
  background: #fff7f5;
  font-size: 11px;
  line-height: 1.6;
}

.role-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 9px;
  margin-top: 23px;
}

.role-modal-actions button {
  min-height: 38px;
  padding: 0 14px;
  border: 1px solid #e3eaf0;
  border-radius: 7px;
  color: #5c6e7e;
  background: white;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.role-modal-actions button[type="submit"] {
  border-color: #2874c8;
  color: white;
  background: #2874c8;
  font-weight: 650;
}

.role-modal-actions button:hover:not(:disabled) {
  filter: brightness(0.97);
}

.role-modal-actions button:disabled,
.role-modal-close:disabled {
  opacity: 0.6;
  cursor: wait;
}
</style>

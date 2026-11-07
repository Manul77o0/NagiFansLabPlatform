<script setup>
import { ref } from 'vue'
import axios from 'axios'

const props = defineProps({
  userId: {
    type: [String, Number],
    required: true
  }
})

const emit = defineEmits(['close', 'success'])

const displayName = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

const handleSubmit = async () => {
  if (!displayName.value.trim()) {
    errorMessage.value = '表示名を入力してください。'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await axios.post(`/api/admin/user/${props.userId}/update`, {
      displayName: displayName.value
    })

    emit('success', response.data)
    emit('close')
  } catch (error) {
    console.error(error)
    errorMessage.value = '送信に失敗しました。もう一度お試しください。'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div class="modal-heading">
        <span class="modal-icon" aria-hidden="true">Aa</span>
        <div>
          <h3 id="modal-title">表示名の変更</h3>
          <p class="user-id">ユーザー ID: {{ userId }}</p>
        </div>
        <button class="close-button" type="button" aria-label="閉じる" @click="emit('close')">×</button>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="display-name">新しい表示名</label>
          <input 
            id="display-name"
            v-model="displayName" 
            type="text" 
            placeholder="表示名を入力してください"
            autocomplete="name"
            required
            :disabled="isLoading"
          />
        </div>

        <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>

        <div class="buttons">
          <button type="button" @click="emit('close')" :disabled="isLoading">
            キャンセル
          </button>
          <button type="submit" :disabled="isLoading">
            {{ isLoading ? '送信中...' : '保存する' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(20, 36, 52, 0.42);
  backdrop-filter: blur(3px);
  z-index: 1000;
}

.modal-content {
  width: min(100%, 430px);
  padding: 25px;
  border: 1px solid rgba(226, 235, 243, 0.9);
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 24px 70px rgba(20, 42, 63, 0.22);
}

.modal-heading {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.modal-icon {
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

.modal-heading h3 {
  margin: 0;
  color: #263a4d;
  font-size: 17px;
  font-weight: 700;
}

.user-id {
  margin: 5px 0 0;
  color: #8997a4;
  font-size: 11px;
}

.close-button {
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

.close-button:hover {
  color: #34495c;
  background: #f2f5f8;
}

.form-group {
  margin-bottom: 22px;
}

.form-group label {
  display: block;
  margin-bottom: 7px;
  color: #526579;
  font-size: 12px;
  font-weight: 650;
}

.form-group input {
  width: 100%;
  box-sizing: border-box;
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

.form-group input:focus {
  border-color: #92bce0;
  box-shadow: 0 0 0 3px rgba(40, 116, 200, 0.08);
}

.error-msg {
  margin: 0 0 15px;
  padding: 9px 10px;
  border: 1px solid #f2d9d4;
  border-radius: 6px;
  color: #a74f43;
  background: #fff7f5;
  font-size: 11px;
}

.buttons {
  display: flex;
  justify-content: flex-end;
  gap: 9px;
}

.buttons button {
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

.buttons button[type="submit"] {
  border-color: #2874c8;
  color: white;
  background: #2874c8;
  font-weight: 650;
}

.buttons button:hover:not(:disabled) {
  filter: brightness(0.97);
}

.buttons button:disabled {
  opacity: 0.6;
  cursor: wait;
}
</style>

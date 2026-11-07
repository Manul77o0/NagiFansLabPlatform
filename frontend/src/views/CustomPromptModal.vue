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
    <div class="modal-content">
      <h3>表示名の変更</h3>
      
      <!-- 渡されたユーザーIDの表示（確認用） -->
      <p class="user-id">対象ユーザーID: {{ userId }}</p>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="display-name">新しい表示名</label>
          <input 
            id="display-name"
            v-model="displayName" 
            type="text" 
            placeholder="名前を入力してください"
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
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-content {
  background: white;
  padding: 24px;
  border-radius: 8px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.user-id {
  font-size: 0.9em;
  color: #666;
  margin-bottom: 16px;
}
.form-group {
  margin-bottom: 16px;
}
.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: bold;
}
.form-group input {
  width: 100%;
  padding: 8px;
  box-sizing: border-box;
}
.error-msg {
  color: red;
  font-size: 0.9em;
  margin-bottom: 12px;
}
.buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>

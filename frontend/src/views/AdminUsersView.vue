<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../components/api'
import CustomPromptModal from './CustomPromptModal.vue'
import UserRoleModal from './UserRoleModal.vue'

const router = useRouter()

const isLoggedIn = ref(false)
const isUserAdmin = ref(false)
const isLoading = ref(true)
const isRegistering = ref(false)
const isAPIError = ref(false)
const user = ref(null)
const items = ref([])
const searchQuery = ref('')
const cmdisplayMsg = ref('')
const isCommandError = ref(false)
const formdisplayMsg = ref('')
const registerusername = ref('')
const registerpassword = ref('')
const isModalOpen = ref(false)
const selectedUserId = ref(null)
const isRoleModalOpen = ref(false)
const selectedRoleUser = ref(null)

const filteredUsers = computed(() => {
  const query = searchQuery.value.trim().toLocaleLowerCase()
  if (!query) return items.value

  return items.value.filter((item) =>
    [item.displayname, item.email]
      .filter(Boolean)
      .some((value) => value.toLocaleLowerCase().includes(query)),
  )
})

const activeUserCount = computed(() => items.value.filter((item) => !item.disabled).length)
const disabledUserCount = computed(() => items.value.length - activeUserCount.value)
const userInitial = computed(() => user.value?.displayname?.trim()?.slice(0, 1) || 'A')

const roleName = (level) => ({
  1: '読み取りユーザー',
  2: '書き込みユーザー',
  3: '管理ユーザー',
}[level] || '未設定')

const setCommandMessage = (message, isError = false) => {
  cmdisplayMsg.value = message
  isCommandError.value = isError
}

const openEditModal = (id) => {
  selectedUserId.value = id
  isModalOpen.value = true
}

const openRoleModal = (itemUser) => {
  selectedRoleUser.value = itemUser
  isRoleModalOpen.value = true
}

const handleSuccess = async () => {
  setCommandMessage('表示名を変更しました')
  await loadItems()
}

const handleRoleSuccess = (updatedUser) => {
  const itemUser = items.value.find((item) => item.id === updatedUser.id)
  if (itemUser) itemUser.level = updatedUser.level
  setCommandMessage(`${updatedUser.displayname}さんの権限を「${roleName(updatedUser.level)}」に変更しました`)
  isRoleModalOpen.value = false
}

const loadCurrentUser = async () => {
  try {
    const response = await api.get('/api/users/me')
    user.value = response.data
    isLoggedIn.value = true
    isUserAdmin.value = response.data.level >= 3
    return isUserAdmin.value ? 'Admin' : 'User'
  } catch (error) {
    if (error.response?.status === 401 || error.response?.status === 400) {
      isLoggedIn.value = false
      user.value = null
      return error.response.status === 401 ? 'Guest' : 'Inactive'
    }

    isAPIError.value = true
    return 'APIError'
  }
}

const loadItems = async () => {
  try {
    const response = await api.get('/api/admin/users')
    items.value = response.data
  } catch {
    setCommandMessage('通信エラーが発生しました。再度お試しください。', true)
  } finally {
    isLoading.value = false
  }
}

const handleRegister = async () => {
  setCommandMessage('')
  formdisplayMsg.value = ''
  isRegistering.value = true

  try {
    await api.post('/api/admin/user/register', {
      username: registerusername.value,
      password: registerpassword.value,
    })
    registerusername.value = ''
    registerpassword.value = ''
    setCommandMessage('ユーザーを登録しました')
    await loadItems()
  } catch (error) {
    if (error.response?.status === 400) {
      formdisplayMsg.value = 'ユーザー名またはパスワードを確認してください'
    } else if (error.response?.status === 401) {
      formdisplayMsg.value = 'ページを再読み込みしてください'
    } else {
      formdisplayMsg.value = '通信エラーが発生しました。再度お試しください。'
    }
  } finally {
    isRegistering.value = false
  }
}

const updateUserStatus = async (userId, shouldEnable) => {
  try {
    await api.post(`/api/admin/user/${userId}/${shouldEnable ? 'enable' : 'disable'}`, {})
    setCommandMessage(shouldEnable ? 'ユーザーを有効化しました' : 'ユーザーを無効化しました')
    await loadItems()
  } catch (error) {
    if (error.response?.status === 400) {
      setCommandMessage('不正なユーザーIDです', true)
    } else if (error.response?.status === 401) {
      setCommandMessage('ページを再読み込みしてください', true)
    } else {
      setCommandMessage('通信エラーが発生しました。再度お試しください。', true)
    }
  }
}

const resetPassword = async (userId) => {
  try {
    await api.post(`/api/admin/user/${userId}/reset`, {})
    setCommandMessage('パスワード初期化メールを送信しました')
  } catch (error) {
    if (error.response?.status === 400) {
      setCommandMessage('不正なユーザーIDです', true)
    } else if (error.response?.status === 401) {
      setCommandMessage('ページを再読み込みしてください', true)
    } else {
      setCommandMessage('通信エラーが発生しました。再度お試しください。', true)
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
  } catch {
    setCommandMessage('ログアウトに失敗しました。再度お試しください。', true)
  }
}

onMounted(async () => {
  const state = await loadCurrentUser()
  if (state === 'Admin') {
    await loadItems()
  } else {
    isLoading.value = false
  }
})
</script>

<template>
  <div class="admin-page">
    <header class="topbar">
      <a class="brand" href="/" aria-label="NagiFans Lab ホーム">
        <span class="brand-mark">N</span>
        <span class="brand-name">NagiFans <strong>Lab</strong></span>
      </a>
      <div class="topbar-divider"></div>
      <span class="topbar-section">管理コンソール</span>
      <div class="topbar-user" v-if="isLoggedIn">
        <span class="avatar">{{ userInitial }}</span>
        <span class="topbar-username">{{ user?.displayname }}</span>
        <button class="logout-button" type="button" @click="handleLogout">ログアウト</button>
      </div>
    </header>

    <main class="dashboard">
      <div class="page-heading">
        <div>
          <p class="eyebrow">ADMINISTRATION</p>
          <h1>ユーザー管理</h1>
          <p class="page-description">アカウントの確認や登録、アクセス権の管理ができます。</p>
        </div>
        <div class="heading-badge">
          <span class="heading-badge-dot"></span>
          管理者
        </div>
      </div>

      <p v-if="cmdisplayMsg" class="notice" :class="{ 'notice-error': isCommandError }" role="status" aria-live="polite">
        <span class="notice-icon" aria-hidden="true">{{ isCommandError ? '!' : '✓' }}</span>
        {{ cmdisplayMsg }}
      </p>

      <section v-if="isAPIError" class="access-card">
        <div class="access-icon">!</div>
        <h2>情報を読み込めませんでした</h2>
        <p>通信エラーが発生しました。時間をおいて再度お試しください。</p>
        <a class="text-link" href="/">トップページへ戻る</a>
      </section>

      <section v-else-if="!isLoggedIn" class="access-card">
        <div class="access-icon">↗</div>
        <h2>ログインが必要です</h2>
        <p>ユーザー管理を利用するにはログインしてください。</p>
        <a class="primary-button link-button" href="/?redirect=/admin/users&requiredlogin=true">
          ログイン画面へ
        </a>
      </section>

      <section v-else-if="!isUserAdmin" class="access-card">
        <div class="access-icon">!</div>
        <h2>アクセス権限がありません</h2>
        <p>このページは管理者のみ利用できます。</p>
        <a class="text-link" href="/">トップページへ戻る</a>
      </section>

      <template v-else>
        <section class="summary-grid" aria-label="ユーザー概要">
          <article class="summary-card">
            <div class="summary-icon total-icon" aria-hidden="true">U</div>
            <div>
              <p class="summary-label">登録ユーザー</p>
              <p class="summary-value">{{ items.length }}<span>人</span></p>
            </div>
            <span class="summary-decoration" aria-hidden="true">01</span>
          </article>
          <article class="summary-card">
            <div class="summary-icon active-icon" aria-hidden="true">✓</div>
            <div>
              <p class="summary-label">有効</p>
              <p class="summary-value">{{ activeUserCount }}<span>人</span></p>
            </div>
            <span class="summary-decoration" aria-hidden="true">02</span>
          </article>
          <article class="summary-card">
            <div class="summary-icon disabled-icon" aria-hidden="true">Ⅱ</div>
            <div>
              <p class="summary-label">無効</p>
              <p class="summary-value">{{ disabledUserCount }}<span>人</span></p>
            </div>
            <span class="summary-decoration" aria-hidden="true">03</span>
          </article>
        </section>

        <div class="content-grid">
          <section class="panel users-panel">
            <div class="panel-heading">
              <div>
                <h2>ユーザー一覧</h2>
                <p>登録済みアカウントを管理します</p>
              </div>
              <span class="count-pill">{{ items.length }} 件</span>
            </div>

            <label class="search-box">
              <span class="search-icon" aria-hidden="true"></span>
              <input
                v-model="searchQuery"
                type="search"
                placeholder="名前・メールアドレスで検索"
                aria-label="ユーザーを検索"
              />
              <kbd>/</kbd>
            </label>

            <div class="user-table-wrap">
              <table class="user-table">
                <thead>
                  <tr>
                    <th scope="col">ユーザー</th>
                    <th scope="col">ステータス</th>
                    <th scope="col">権限</th>
                    <th scope="col">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="isLoading">
                    <td class="table-message" colspan="4">ユーザー情報を読み込んでいます…</td>
                  </tr>
                  <tr v-else-if="filteredUsers.length === 0">
                    <td class="table-message" colspan="4">
                      {{ searchQuery ? '検索条件に一致するユーザーはいません。' : 'ユーザーはまだ登録されていません。' }}
                    </td>
                  </tr>
                  <tr v-for="item_user in filteredUsers" :key="item_user.id">
                    <td>
                      <div class="user-cell">
                        <span class="user-avatar">{{ item_user.displayname?.trim()?.slice(0, 1) || '?' }}</span>
                        <span class="user-details">
                          <strong>{{ item_user.displayname }}</strong>
                          <span>{{ item_user.email }}</span>
                        </span>
                      </div>
                    </td>
                    <td>
                      <span class="status-badge" :class="item_user.disabled ? 'status-disabled' : 'status-active'">
                        <span class="status-dot"></span>
                        {{ item_user.disabled ? '無効' : '有効' }}
                      </span>
                    </td>
                    <td>
                      <span class="role-badge" :class="`role-level-${item_user.level}`">
                        {{ roleName(item_user.level) }}
                      </span>
                    </td>
                    <td>
                      <div class="row-actions">
                        <button
                          class="action-button"
                          type="button"
                          title="表示名を編集"
                          :aria-label="`${item_user.displayname}の表示名を変更`"
                          @click="openEditModal(item_user.id)"
                        >
                          表示名編集
                        </button>
                        <button
                          class="action-button"
                          type="button"
                          :title="item_user.id === user?.id ? '自分自身の権限は変更できません' : '権限を変更'"
                          :aria-label="`${item_user.displayname}の権限を変更`"
                          :disabled="item_user.id === user?.id"
                          @click="openRoleModal(item_user)"
                        >
                          権限変更
                        </button>
                        <button
                          class="action-button"
                          type="button"
                          title="パスワード初期化メールを送信"
                          :aria-label="`${item_user.displayname}のパスワードを初期化`"
                          @click="resetPassword(item_user.id)"
                        >
                          初期化
                        </button>
                        <button
                          v-if="item_user.disabled"
                          class="action-button action-enable"
                          type="button"
                          @click="updateUserStatus(item_user.id, true)"
                        >
                          有効化
                        </button>
                        <button
                          v-else
                          class="action-button action-disable"
                          type="button"
                          :title="item_user.id === user?.id ? '自分自身は無効化できません' : 'ユーザーを無効化'"
                          :disabled="item_user.id === user?.id"
                          @click="updateUserStatus(item_user.id, false)"
                        >
                          無効化
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="table-footer">
              <span>全 {{ items.length }} 件のユーザー</span>
              <span>表示名またはメールアドレスで検索できます</span>
            </div>
          </section>

          <aside class="panel register-panel">
            <div class="register-heading">
              <span class="register-icon" aria-hidden="true">＋</span>
              <div>
                <h2>新しいユーザー</h2>
                <p>アカウントを追加します</p>
              </div>
            </div>
            <div class="form-divider"></div>
            <form class="register-form" @submit.prevent="handleRegister">
              <p v-if="formdisplayMsg" class="form-error" role="alert">{{ formdisplayMsg }}</p>
              <label for="registerusername">ユーザー名</label>
              <input
                id="registerusername"
                v-model="registerusername"
                type="text"
                placeholder="例: nagi_user"
                autocomplete="username"
                required
                :disabled="isRegistering"
              />
              <span class="field-hint">メールアドレスの一部として使用されます</span>

              <label for="registerpassword">初期パスワード</label>
              <input
                id="registerpassword"
                v-model="registerpassword"
                type="password"
                placeholder="初期パスワードを入力"
                autocomplete="new-password"
                required
                :disabled="isRegistering"
              />
              <span class="field-hint">登録後、パスワード初期化メールを送信できます</span>

              <button class="primary-button submit-button" type="submit" :disabled="isRegistering">
                <span aria-hidden="true">{{ isRegistering ? '…' : '+' }}</span>
                {{ isRegistering ? '登録中…' : 'ユーザーを登録' }}
              </button>
            </form>
            <p class="form-footnote">
              <span aria-hidden="true">i</span>
              登録したアカウントは、初期状態では無効です。
            </p>
          </aside>
        </div>
      </template>

      <footer class="page-footer">
        <span>NagiFans Lab</span>
        <span>ユーザー管理</span>
      </footer>

      <CustomPromptModal
        v-if="isModalOpen"
        :user-id="selectedUserId"
        @close="isModalOpen = false"
        @success="handleSuccess"
      />
      <UserRoleModal
        v-if="isRoleModalOpen && selectedRoleUser"
        :user="selectedRoleUser"
        @close="isRoleModalOpen = false"
        @success="handleRoleSuccess"
      />
    </main>
  </div>
</template>

<style scoped>
.admin-page {
  --ink: #192b3d;
  --muted: #78889a;
  --line: #e7edf2;
  --paper: #ffffff;
  --canvas: #f4f7fa;
  --blue: #2874c8;
  --blue-dark: #1d5fa9;
  min-height: 100vh;
  color: var(--ink);
  background:
    radial-gradient(ellipse at 87% 2%, rgba(201, 225, 247, 0.27), transparent 28rem),
    var(--canvas);
  font-family: "Mona Sans VF", -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
}

.admin-page *,
.admin-page *::before,
.admin-page *::after {
  box-sizing: border-box;
}

.topbar {
  height: 72px;
  padding: 0 clamp(20px, 5vw, 72px);
  display: flex;
  align-items: center;
  gap: 20px;
  background: rgba(255, 255, 255, 0.92);
  border-bottom: 1px solid #e8eef3;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  color: var(--ink);
  text-decoration: none;
}

.brand-mark {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  color: #fff;
  background: linear-gradient(145deg, #4195df, #2467b3);
  box-shadow: 0 5px 12px rgba(40, 116, 200, 0.2);
  font-size: 17px;
  font-weight: 800;
}

.brand-name {
  font-size: 15px;
  letter-spacing: -0.035em;
}

.brand-name strong {
  font-weight: 750;
}

.topbar-divider {
  width: 1px;
  height: 23px;
  background: var(--line);
}

.topbar-section {
  color: #8190a0;
  font-size: 13px;
}

.topbar-user {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}

.avatar,
.user-avatar {
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: #316fae;
  background: #e7f1fb;
  font-size: 13px;
  font-weight: 700;
}

.topbar-username {
  max-width: 180px;
  overflow: hidden;
  color: #435568;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logout-button {
  margin-left: 8px;
  padding: 8px 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  color: #56687a;
  background: white;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
  transition: border-color 0.18s, color 0.18s;
}

.logout-button:hover {
  border-color: #b8cadb;
  color: var(--ink);
}

.dashboard {
  width: min(1320px, 100%);
  margin: 0 auto;
  padding: 42px clamp(20px, 5vw, 72px) 28px;
}

.page-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 27px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #6b95bd;
  font-size: 10px;
  font-weight: 750;
  letter-spacing: 0.16em;
}

.page-heading h1 {
  margin: 0;
  color: #172a3d;
  font-size: clamp(26px, 3vw, 34px);
  font-weight: 720;
  letter-spacing: -0.045em;
  text-decoration: none;
}

.page-description {
  margin: 9px 0 0;
  color: var(--muted);
  font-size: 13px;
}

.heading-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #dceaf6;
  border-radius: 20px;
  color: #4a7296;
  background: rgba(255, 255, 255, 0.7);
  font-size: 11px;
  font-weight: 650;
  white-space: nowrap;
}

.heading-badge-dot,
.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #55b88a;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.summary-card {
  position: relative;
  min-height: 112px;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--paper);
  box-shadow: 0 3px 12px rgba(36, 61, 82, 0.025);
}

.summary-icon {
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
}

.total-icon {
  color: #427cb5;
  background: #edf5fc;
}

.active-icon {
  color: #388d6a;
  background: #eaf7f0;
}

.disabled-icon {
  color: #9a7a4b;
  background: #f8f2e8;
}

.summary-label {
  margin: 0 0 5px;
  color: #8290a0;
  font-size: 12px;
}

.summary-value {
  margin: 0;
  color: #24384b;
  font-size: 27px;
  font-weight: 720;
  letter-spacing: -0.04em;
  line-height: 1;
}

.summary-value span {
  margin-left: 4px;
  color: #8695a3;
  font-size: 12px;
  font-weight: 500;
}

.summary-decoration {
  position: absolute;
  top: 17px;
  right: 18px;
  color: #eef2f6;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 310px;
  align-items: start;
  gap: 20px;
}

.panel {
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--paper);
  box-shadow: 0 3px 12px rgba(36, 61, 82, 0.025);
}

.users-panel {
  overflow: hidden;
}

.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 22px 22px 17px;
}

.panel-heading h2,
.register-heading h2 {
  margin: 0;
  color: #263a4d;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.panel-heading p,
.register-heading p {
  margin: 5px 0 0;
  color: #8a98a6;
  font-size: 11px;
}

.count-pill {
  padding: 5px 9px;
  border-radius: 20px;
  color: #67839d;
  background: #f0f5f9;
  font-size: 11px;
  font-weight: 600;
}

.search-box {
  height: 40px;
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 22px 16px;
  padding: 0 11px;
  border: 1px solid #e7edf2;
  border-radius: 8px;
  background: #fbfcfd;
  transition: border-color 0.18s, box-shadow 0.18s;
}

.search-box:focus-within {
  border-color: #9dc3e5;
  box-shadow: 0 0 0 3px rgba(40, 116, 200, 0.08);
}

.search-icon {
  position: relative;
  width: 13px;
  height: 13px;
  flex: 0 0 auto;
  border: 1.5px solid #93a2af;
  border-radius: 50%;
}

.search-icon::after {
  position: absolute;
  right: -4px;
  bottom: -3px;
  width: 5px;
  height: 1.5px;
  background: #93a2af;
  content: "";
  transform: rotate(45deg);
  transform-origin: left center;
}

.search-box input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: 0;
  color: #31485b;
  background: transparent;
  font: inherit;
  font-size: 12px;
}

.search-box input::placeholder {
  color: #a0acb7;
}

.search-box kbd {
  min-width: 21px;
  padding: 2px 5px;
  border: 1px solid #e6ebf0;
  border-radius: 4px;
  color: #9ba8b4;
  background: white;
  font-family: inherit;
  font-size: 10px;
  text-align: center;
}

.user-table-wrap {
  width: 100%;
  overflow-x: auto;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.user-table th {
  padding: 11px 16px;
  border-top: 1px solid #edf1f4;
  border-bottom: 1px solid #edf1f4;
  color: #8b98a5;
  background: #fafbfd;
  font-size: 10px;
  font-weight: 650;
  letter-spacing: 0.035em;
  white-space: nowrap;
}

.user-table th:first-child,
.user-table td:first-child {
  padding-left: 22px;
}

.user-table th:last-child,
.user-table td:last-child {
  padding-right: 22px;
}

.user-table td {
  padding: 13px 16px;
  border-bottom: 1px solid #eff2f5;
  color: #536576;
  font-size: 12px;
  vertical-align: middle;
}

.user-table tbody tr:last-child td {
  border-bottom: 0;
}

.user-cell {
  min-width: 180px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  width: 33px;
  height: 33px;
  color: #647d94;
  background: #eef2f5;
  font-size: 12px;
}

.user-details {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-details strong {
  overflow: hidden;
  color: #314558;
  font-size: 12px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-details > span {
  overflow: hidden;
  color: #8c99a6;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-radius: 20px;
  font-size: 10px;
  font-weight: 600;
  white-space: nowrap;
}

.status-active {
  color: #43856c;
  background: #edf7f1;
}

.status-active .status-dot {
  background: #54b287;
}

.status-disabled {
  color: #957b55;
  background: #f8f3e9;
}

.status-disabled .status-dot {
  background: #c8a86d;
}

.role-badge {
  display: inline-flex;
  padding: 5px 8px;
  border-radius: 20px;
  font-size: 10px;
  font-weight: 650;
  white-space: nowrap;
}

.role-level-1 {
  color: #64798d;
  background: #eff3f6;
}

.role-level-2 {
  color: #3977a5;
  background: #edf5fb;
}

.role-level-3 {
  color: #7d68a5;
  background: #f3effa;
}

.row-actions {
  display: flex;
  justify-content: flex-end;
  gap: 5px;
  white-space: nowrap;
}

.action-button {
  padding: 6px 7px;
  border: 1px solid transparent;
  border-radius: 6px;
  color: #65798b;
  background: transparent;
  font: inherit;
  font-size: 10px;
  cursor: pointer;
  transition: background 0.16s, color 0.16s, border-color 0.16s;
}

.action-button:hover {
  border-color: #dce8f2;
  color: #286da9;
  background: #f3f8fc;
}

.action-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-button.action-disable:hover {
  border-color: #f0ded7;
  color: #a55f4d;
  background: #fff7f4;
}

.action-button.action-enable:hover {
  border-color: #d8ebdf;
  color: #3e8b68;
  background: #f2faf5;
}

.table-message {
  height: 110px;
  color: #8997a4 !important;
  text-align: center;
}

.table-footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 22px;
  border-top: 1px solid #edf1f4;
  color: #98a4af;
  font-size: 10px;
}

.register-panel {
  padding: 21px;
}

.register-heading {
  display: flex;
  align-items: center;
  gap: 11px;
}

.register-icon {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  color: #3479b7;
  background: #edf5fc;
  font-size: 20px;
  font-weight: 400;
}

.form-divider {
  height: 1px;
  margin: 18px 0;
  background: #edf1f4;
}

.register-form {
  display: flex;
  flex-direction: column;
}

.register-form label {
  margin: 0 0 7px;
  color: #526579;
  font-size: 11px;
  font-weight: 650;
}

.register-form input {
  width: 100%;
  height: 40px;
  padding: 0 11px;
  border: 1px solid #e3eaf0;
  border-radius: 7px;
  outline: 0;
  color: #34495c;
  background: #fcfdfe;
  font: inherit;
  font-size: 12px;
  transition: border-color 0.18s, box-shadow 0.18s;
}

.register-form input:focus {
  border-color: #92bce0;
  box-shadow: 0 0 0 3px rgba(40, 116, 200, 0.08);
}

.register-form input::placeholder {
  color: #a7b2bc;
}

.field-hint {
  margin: 6px 0 18px;
  color: #98a4af;
  font-size: 10px;
  line-height: 1.5;
}

.primary-button {
  min-height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 15px;
  border: 0;
  border-radius: 7px;
  color: white;
  background: var(--blue);
  box-shadow: 0 4px 9px rgba(40, 116, 200, 0.18);
  font: inherit;
  font-size: 12px;
  font-weight: 650;
  text-decoration: none;
  cursor: pointer;
  transition: background 0.18s, transform 0.18s;
}

.primary-button:hover:not(:disabled) {
  background: var(--blue-dark);
  transform: translateY(-1px);
}

.primary-button:disabled {
  opacity: 0.65;
  cursor: wait;
}

.submit-button {
  width: 100%;
  margin-top: 1px;
}

.submit-button > span {
  font-size: 17px;
  font-weight: 400;
}

.form-footnote {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 14px 0 0;
  color: #919eaa;
  font-size: 10px;
  line-height: 1.6;
}

.form-footnote > span {
  width: 15px;
  height: 15px;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: #7d93a7;
  background: #f0f4f7;
  font-size: 9px;
  font-weight: 700;
}

.form-error {
  margin: 0 0 14px;
  padding: 9px 10px;
  border: 1px solid #f2d9d4;
  border-radius: 6px;
  color: #a74f43;
  background: #fff7f5;
  font-size: 11px;
  line-height: 1.5;
}

.notice {
  display: flex;
  align-items: center;
  gap: 9px;
  margin: -8px 0 19px;
  padding: 11px 13px;
  border: 1px solid #d8ecdf;
  border-radius: 8px;
  color: #478268;
  background: #f1faf4;
  font-size: 12px;
}

.notice-error {
  border-color: #f2d9d4;
  color: #a74f43;
  background: #fff7f5;
}

.notice-icon {
  width: 18px;
  height: 18px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: white;
  background: #62ae83;
  font-size: 11px;
}

.notice-error .notice-icon {
  background: #c77668;
}

.access-card {
  padding: 48px 24px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--paper);
  text-align: center;
}

.access-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  margin: 0 auto 15px;
  border-radius: 50%;
  color: #5685af;
  background: #edf5fc;
  font-size: 18px;
  font-weight: 700;
}

.access-card h2 {
  margin: 0;
  color: #2d4357;
  font-size: 17px;
}

.access-card p {
  margin: 9px 0 18px;
  color: #82909d;
  font-size: 12px;
}

.link-button {
  margin-top: 3px;
}

.text-link {
  color: #3478b6;
  font-size: 12px;
  text-decoration: none;
}

.text-link:hover {
  text-decoration: underline;
}

.page-footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 25px;
  color: #a3aeb8;
  font-size: 10px;
}

button:focus-visible,
a:focus-visible,
input:focus-visible {
  outline: 3px solid rgba(40, 116, 200, 0.24);
  outline-offset: 2px;
}

@media (max-width: 980px) {
  .content-grid {
    grid-template-columns: minmax(0, 1fr) 285px;
    gap: 14px;
  }

  .dashboard {
    padding-right: 28px;
    padding-left: 28px;
  }

  .row-actions {
    gap: 1px;
  }

  .action-button {
    padding-right: 5px;
    padding-left: 5px;
  }
}

@media (max-width: 760px) {
  .topbar {
    height: 64px;
    gap: 13px;
    padding: 0 20px;
  }

  .topbar-section {
    font-size: 11px;
  }

  .topbar-username {
    display: none;
  }

  .logout-button {
    margin-left: 0;
  }

  .dashboard {
    padding: 32px 20px 24px;
  }

  .content-grid {
    grid-template-columns: 1fr;
  }

  .register-panel {
    order: -1;
  }
}

@media (max-width: 540px) {
  .brand-name {
    font-size: 13px;
  }

  .topbar {
    gap: 10px;
    padding: 0 14px;
  }

  .topbar-section {
    font-size: 10px;
  }

  .logout-button {
    padding: 7px 9px;
    font-size: 11px;
  }

  .dashboard {
    padding: 27px 14px 20px;
  }

  .page-heading {
    align-items: flex-start;
    margin-bottom: 21px;
  }

  .page-description {
    max-width: 290px;
    font-size: 12px;
    line-height: 1.6;
  }

  .heading-badge {
    padding: 7px 9px;
    font-size: 10px;
  }

  .summary-grid {
    gap: 8px;
    margin-bottom: 13px;
  }

  .summary-card {
    min-height: 94px;
    align-items: flex-start;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
  }

  .summary-icon {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    font-size: 12px;
  }

  .summary-label {
    margin-bottom: 4px;
    font-size: 10px;
    white-space: nowrap;
  }

  .summary-value {
    font-size: 20px;
  }

  .summary-decoration {
    top: 14px;
    right: 12px;
    font-size: 9px;
  }

  .panel-heading {
    padding: 18px 15px 14px;
  }

  .search-box {
    margin-right: 15px;
    margin-left: 15px;
  }

  .user-table {
    min-width: 530px;
  }

  .user-table th:first-child,
  .user-table td:first-child {
    padding-left: 15px;
  }

  .user-table th:last-child,
  .user-table td:last-child {
    padding-right: 15px;
  }

  .table-footer {
    padding-right: 15px;
    padding-left: 15px;
  }

  .table-footer > span:last-child {
    display: none;
  }

  .page-footer {
    margin-top: 19px;
  }
}
</style>

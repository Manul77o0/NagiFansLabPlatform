<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { api, getCurrentUser } from '../components/api'

const route = useRoute()
const router = useRouter()
const user = ref(null)
const peers = ref([])
const isLoading = ref(true)
const message = ref('')
const isError = ref(false)
const lastUpdated = ref(null)
let refreshTimer

const userInitial = computed(() => user.value?.displayname?.trim()?.slice(0, 1) || 'A')

const setMessage = (text, error = false) => {
  message.value = text
  isError.value = error
}

const loadPeers = async () => {
  try {
    const response = await api.get('/api/wg_tools/connected_peers')
    peers.value = response.data
    lastUpdated.value = new Date()
    setMessage('')
  } catch (error) {
    if (error.response?.status === 401 || error.response?.status === 403) {
      await router.replace({
        path: '/',
        query: { redirect: route.fullPath, requiredlogin: 'true' },
      })
    } else {
      setMessage(
        error.response?.data?.detail || '接続状態を読み込めませんでした。WireGuardの状態を確認してください。',
        true,
      )
    }
  } finally {
    isLoading.value = false
  }
}

const formatBytes = (value) => {
  if (!value) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const unitIndex = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1)
  return `${(value / (1024 ** unitIndex)).toFixed(unitIndex ? 2 : 0)} ${units[unitIndex]}`
}

const formatHandshake = (timestamp) => {
  if (!timestamp) return '未接続'
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'medium',
  }).format(new Date(timestamp * 1000))
}

const handleLogout = async () => {
  try {
    await api.post('/api/session/logout')
    await router.push('/')
  } catch {
    setMessage('ログアウトに失敗しました。再度お試しください。', true)
  }
}

onMounted(async () => {
  try {
    user.value = await getCurrentUser()
    await loadPeers()
    refreshTimer = window.setInterval(loadPeers, 15000)
  } catch (error) {
    if (error.response?.status === 401 || error.response?.status === 403) {
      await router.replace({
        path: '/',
        query: { redirect: route.fullPath, requiredlogin: 'true' },
      })
    } else {
      setMessage('アカウント情報を確認できませんでした。再読み込みしてください。', true)
      isLoading.value = false
    }
  }
})

onUnmounted(() => {
  window.clearInterval(refreshTimer)
})
</script>

<template>
  <div class="peers-page">
    <header class="peers-topbar">
      <a class="peers-brand" href="/" aria-label="NagiFans Lab ホーム">
        <span class="peers-brand-mark">N</span>
        <span>NagiFans <strong>Lab</strong></span>
      </a>
      <span class="peers-topbar-section">管理コンソール</span>
      <div v-if="user" class="peers-user">
        <span class="peers-avatar">{{ userInitial }}</span>
        <span>{{ user.displayname }}</span>
        <button type="button" @click="handleLogout">ログアウト</button>
      </div>
    </header>

    <main class="peers-content">
      <div class="peers-heading">
        <div>
          <p class="peers-eyebrow">WIREGUARD MANAGEMENT</p>
          <h1>接続中のクライアント</h1>
          <p>最新のハンドシェイクから接続状況を推定します。15秒ごとに自動更新します。</p>
        </div>
        <button type="button" :disabled="isLoading" @click="loadPeers">
          {{ isLoading ? '読み込み中…' : '更新' }}
        </button>
      </div>

      <nav class="peers-nav" aria-label="WireGuard設定">
        <RouterLink to="/wg_tools">クライアント設定</RouterLink>
        <RouterLink to="/wg_tools/connected_peers" class="peers-nav-active">接続状態</RouterLink>
        <RouterLink to="/wg_tools/server_settings">サーバー設定</RouterLink>
        <RouterLink to="/wg_tools/global_settings">グローバル設定</RouterLink>
      </nav>

      <p v-if="message" class="peers-message" :class="{ 'peers-message-error': isError }" role="status">
        {{ message }}
      </p>

      <section class="peers-panel" aria-label="WireGuard接続中のクライアント一覧">
        <div class="peers-panel-heading">
          <div>
            <h2>Connected Peers</h2>
            <p>{{ peers.length }} 件の登録クライアント</p>
          </div>
          <span v-if="lastUpdated">更新: {{ lastUpdated.toLocaleTimeString() }}</span>
        </div>
        <div class="peers-table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">#</th>
                <th scope="col">名前</th>
                <th scope="col">メール</th>
                <th scope="col">割り当てIP</th>
                <th scope="col">Endpoint</th>
                <th scope="col">Public Key</th>
                <th scope="col">受信</th>
                <th scope="col">送信</th>
                <th scope="col">接続</th>
                <th scope="col">最終Handshake</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="isLoading">
                <td colspan="10" class="peers-table-message">接続状態を読み込んでいます…</td>
              </tr>
              <tr v-else-if="peers.length === 0">
                <td colspan="10" class="peers-table-message">登録済みクライアントはいません。</td>
              </tr>
              <tr v-for="(peer, index) in peers" :key="peer.ID" :class="{ 'peer-connected': peer.Connected }">
                <td>{{ index }}</td>
                <td>{{ peer.Name }}</td>
                <td>{{ peer.Email }}</td>
                <td class="peer-mono">{{ peer.IPAllocation || '-' }}</td>
                <td class="peer-mono">{{ peer.Endpoint || '-' }}</td>
                <td class="peer-key">{{ peer.PublicKey || '-' }}</td>
                <td>{{ formatBytes(peer.ReceivedBytes) }}</td>
                <td>{{ formatBytes(peer.TransmittedBytes) }}</td>
                <td>{{ peer.Connected ? '✓' : '-' }}</td>
                <td>{{ formatHandshake(peer.LastHandshake) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <footer>最終Handshakeが3分以内の場合を「接続中」として表示します（接続状態は概算です）。</footer>
      </section>
    </main>
  </div>
</template>

<style scoped>
.peers-page {
  min-height: 100vh;
  color: #233447;
  background: #f3f6fa;
  font-family: Inter, "Noto Sans JP", sans-serif;
}

.peers-topbar {
  display: flex;
  min-height: 66px;
  align-items: center;
  gap: 24px;
  padding: 0 5vw;
  border-bottom: 1px solid #e1e8f0;
  background: #fff;
}

.peers-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #233447;
  font-size: 15px;
  font-weight: 650;
  text-decoration: none;
}

.peers-brand strong {
  color: #2874c8;
}

.peers-brand-mark,
.peers-avatar {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border-radius: 9px;
  color: #fff;
  background: #2874c8;
  font-weight: 700;
}

.peers-topbar-section {
  color: #8290a0;
  font-size: 12px;
}

.peers-user {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
  font-size: 12px;
}

.peers-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
}

.peers-user button,
.peers-heading button {
  padding: 8px 12px;
  border: 1px solid #dce5ef;
  border-radius: 7px;
  color: #526579;
  background: #fff;
  cursor: pointer;
  font: inherit;
  font-size: 12px;
}

.peers-heading button:disabled {
  cursor: wait;
  opacity: 0.6;
}

.peers-content {
  max-width: 1540px;
  margin: 0 auto;
  padding: 38px 5vw 60px;
}

.peers-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 25px;
}

.peers-eyebrow {
  margin: 0 0 7px;
  color: #5290c9;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.13em;
}

.peers-heading h1 {
  margin: 0;
  color: #263b51;
  font-size: 26px;
}

.peers-heading p:last-child {
  margin: 8px 0 0;
  color: #8290a0;
  font-size: 12px;
}

.peers-nav {
  display: flex;
  gap: 5px;
  overflow-x: auto;
  margin-bottom: 20px;
  border-bottom: 1px solid #dce4ec;
}

.peers-nav a {
  padding: 11px 14px 12px;
  color: #768698;
  font-size: 12px;
  text-decoration: none;
  white-space: nowrap;
}

.peers-nav a:hover,
.peers-nav a.peers-nav-active {
  color: #286da9;
}

.peers-nav a.peers-nav-active {
  border-bottom: 2px solid #2874c8;
  font-weight: 650;
}

.peers-message {
  margin: 0 0 16px;
  padding: 12px 14px;
  border: 1px solid #d8ecdf;
  border-radius: 8px;
  color: #478268;
  background: #f1faf4;
  font-size: 12px;
}

.peers-message-error {
  border-color: #f0d7d4;
  color: #a24f49;
  background: #fff5f4;
}

.peers-panel {
  overflow: hidden;
  border: 1px solid #e1e8f0;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 7px 24px rgb(34 62 89 / 4%);
}

.peers-panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px;
  border-bottom: 1px solid #e7edf3;
}

.peers-panel-heading h2 {
  margin: 0;
  color: #2b3f53;
  font-size: 17px;
}

.peers-panel-heading p,
.peers-panel-heading > span {
  margin: 5px 0 0;
  color: #8795a4;
  font-size: 11px;
}

.peers-table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  white-space: nowrap;
}

th,
td {
  padding: 11px 12px;
  border-bottom: 1px solid #e8edf2;
  text-align: left;
}

th {
  color: #506174;
  background: #f8fafc;
  font-weight: 650;
}

tbody tr:last-child td {
  border-bottom: 0;
}

tbody tr.peer-connected {
  background: #c9ead2;
}

.peer-mono,
.peer-key {
  font-family: "SFMono-Regular", Consolas, monospace;
}

.peer-key {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.peers-table-message {
  padding: 32px;
  color: #8290a0;
  text-align: center;
}

.peers-panel footer {
  padding: 12px 20px;
  border-top: 1px solid #e7edf3;
  color: #8290a0;
  font-size: 11px;
}

@media (max-width: 640px) {
  .peers-topbar {
    gap: 12px;
    padding: 0 16px;
  }

  .peers-topbar-section,
  .peers-topbar-user > span:not(.peers-avatar) {
    display: none;
  }

  .peers-content {
    padding: 28px 16px 40px;
  }

  .peers-heading {
    align-items: flex-start;
  }

  .peers-heading h1 {
    font-size: 21px;
  }

  .peers-panel-heading {
    padding: 16px;
  }
}
</style>

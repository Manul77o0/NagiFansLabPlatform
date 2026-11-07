<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { api, getCurrentUser } from '../components/api'

const route = useRoute()
const router = useRouter()
const user = ref(null)
const clients = ref([])
const searchQuery = ref('')
const isLoading = ref(true)
const isSaving = ref(false)
const isLoadingClientKeys = ref(false)
const isLoadingServerKeys = ref(false)
const showPrivateKey = ref(false)
const showPresharedKey = ref(false)
const showServerPrivateKey = ref(false)
const isModalOpen = ref(false)
const editingId = ref(null)
const message = ref('')
const isMessageError = ref(false)
const globalSettingsExist = ref(false)
const serverSettingsExist = ref(false)

const clientForm = reactive({
  Name: '',
  Email: '',
  IPAllocation: '',
  AllowedIPs: '',
  UseDNS: false,
  PublicKey: '',
  PrivateKey: '',
  PresharedKey: '',
})

const globalForm = reactive({
  Endpoint: '',
  DNSServer: '',
  MTU: '',
  PersistentKeepalive: '',
  FirewallMark: '0xca6c',
  Table: 'auto',
})

const serverForm = reactive({
  ServerInterface: '',
  ListenPort: '',
  Address: '',
  PostUpScript: '',
  PreDownScript: '',
  PostDownScript: '',
  PrivateKey: '',
  PublicKey: '',
})

const section = computed(() => {
  if (route.path.endsWith('/server_settings')) return 'server'
  if (route.path.endsWith('/global_settings')) return 'global'
  return 'clients'
})
const canManage = computed(() => (user.value?.level || 0) >= 2)
const canAdmin = computed(() => (user.value?.level || 0) >= 3)
const userInitial = computed(() => user.value?.displayname?.trim()?.slice(0, 1) || 'A')
const activeClientCount = computed(() => clients.value.filter((client) => !client.disabled).length)
const disabledClientCount = computed(() => clients.value.length - activeClientCount.value)
const filteredClients = computed(() => {
  const query = searchQuery.value.trim().toLocaleLowerCase()
  if (!query) return clients.value

  return clients.value.filter((client) =>
    [client.Name, client.Email, client.IPAllocation, client.AllowedIPs]
      .filter(Boolean)
      .some((value) => value.toLocaleLowerCase().includes(query)),
  )
})

const setMessage = (text, isError = false) => {
  message.value = text
  isMessageError.value = isError
}

const loadClients = async () => {
  isLoading.value = true
  try {
    const response = await api.get('/api/wg_tools/clients')
    clients.value = response.data
  } catch (error) {
    if (error.response?.status === 401) {
      await router.replace({
        path: '/',
        query: { redirect: route.fullPath, requiredlogin: 'true' },
      })
    } else {
      setMessage('クライアント一覧を読み込めませんでした。時間をおいて再度お試しください。', true)
    }
  } finally {
    isLoading.value = false
  }
}

const loadGlobalSettings = async () => {
  isLoading.value = true
  try {
    const response = await api.get('/api/wg_tools/global_settings')
    const settings = response.data
    globalSettingsExist.value = settings !== null
    Object.assign(globalForm, {
      Endpoint: settings?.Endpoint || '',
      DNSServer: settings?.DNSServer || '',
      MTU: settings?.MTU ?? '',
      PersistentKeepalive: settings?.PersistentKeepalive ?? '',
      FirewallMark: settings?.FirewallMark ?? '0xca6c',
      Table: settings?.Table ?? 'auto',
    })
  } catch (error) {
    if (error.response?.status === 401) {
      await router.replace({
        path: '/',
        query: { redirect: route.fullPath, requiredlogin: 'true' },
      })
    } else {
      setMessage('グローバル設定を読み込めませんでした。時間をおいて再度お試しください。', true)
    }
  } finally {
    isLoading.value = false
  }
}

const loadServerKeys = async () => {
  isLoadingServerKeys.value = true
  showServerPrivateKey.value = false
  try {
    const response = await api.get('/api/wg_tools/server_settings/keys')
    serverForm.PrivateKey = response.data.PrivateKey || ''
    serverForm.PublicKey = response.data.PublicKey || ''
  } catch (error) {
    if (error.response?.status !== 404) {
      setMessage(
        error.response?.status === 403
          ? 'サーバー秘密鍵の表示には管理者権限が必要です。'
          : 'サーバー鍵を読み込めませんでした。',
        true,
      )
    }
  } finally {
    isLoadingServerKeys.value = false
  }
}

const loadServerSettings = async () => {
  isLoading.value = true
  try {
    const response = await api.get('/api/wg_tools/server_settings')
    const settings = response.data
    serverSettingsExist.value = settings !== null
    Object.assign(serverForm, {
      ServerInterface: settings?.ServerInterface || '',
      ListenPort: settings?.ListenPort ?? '',
      Address: settings?.Address || '',
      PostUpScript: settings?.PostUpScript || '',
      PreDownScript: settings?.PreDownScript || '',
      PostDownScript: settings?.PostDownScript || '',
      PrivateKey: '',
      PublicKey: settings?.PublicKey || '',
    })
    if (settings && canAdmin.value) await loadServerKeys()
  } catch (error) {
    if (error.response?.status === 401) {
      await router.replace({
        path: '/',
        query: { redirect: route.fullPath, requiredlogin: 'true' },
      })
    } else {
      setMessage('サーバー設定を読み込めませんでした。時間をおいて再度お試しください。', true)
    }
  } finally {
    isLoading.value = false
  }
}

const loadSection = () => {
  setMessage('')
  if (section.value === 'server') return loadServerSettings()
  if (section.value === 'global') return loadGlobalSettings()
  return loadClients()
}

const resetClientForm = () => {
  Object.assign(clientForm, {
    Name: '',
    Email: '',
    IPAllocation: '',
    AllowedIPs: '',
    UseDNS: false,
    PublicKey: '',
    PrivateKey: '',
    PresharedKey: '',
  })
  showPrivateKey.value = false
  showPresharedKey.value = false
}

const openCreateForm = () => {
  editingId.value = null
  resetClientForm()
  isModalOpen.value = true
}

const generateClientKeys = async () => {
  try {
    const response = await api.post('/api/wg_tools/client/generate-keys', {})
    Object.assign(clientForm, response.data)
    showPrivateKey.value = false
    showPresharedKey.value = false
    setMessage('WireGuard形式のクライアント鍵を生成しました。保存すると反映されます。')
  } catch {
    setMessage('クライアント鍵を生成できませんでした。', true)
  }
}

const openEditForm = (client) => {
  editingId.value = client.ID
  Object.assign(clientForm, {
    Name: client.Name,
    Email: client.Email,
    IPAllocation: client.IPAllocation || '',
    AllowedIPs: client.AllowedIPs || '',
    UseDNS: Boolean(client.UseDNS),
    PublicKey: '',
    PrivateKey: '',
    PresharedKey: '',
  })
  showPrivateKey.value = false
  showPresharedKey.value = false
  isModalOpen.value = true
}

const closeClientForm = () => {
  isModalOpen.value = false
  clientForm.PrivateKey = ''
  clientForm.PresharedKey = ''
  showPrivateKey.value = false
  showPresharedKey.value = false
}

const loadClientKeys = async () => {
  if (!editingId.value) return

  isLoadingClientKeys.value = true
  showPrivateKey.value = false
  showPresharedKey.value = false
  try {
    const response = await api.get(
      `/api/wg_tools/clients/${encodeURIComponent(editingId.value)}/keys`,
    )
    Object.assign(clientForm, {
      PublicKey: response.data.PublicKey || '',
      PrivateKey: response.data.PrivateKey || '',
      PresharedKey: response.data.PresharedKey || '',
    })
    setMessage('保存済みのクライアント鍵を読み込みました。')
  } catch (error) {
    setMessage(
      error.response?.status === 403
        ? '鍵の読み出しには管理者権限が必要です。'
        : 'クライアント鍵を読み込めませんでした。',
      true,
    )
  } finally {
    isLoadingClientKeys.value = false
  }
}

const saveClient = async () => {
  isSaving.value = true
  setMessage('')
  const isCreating = !editingId.value
  const payload = {
    Name: clientForm.Name.trim(),
    Email: clientForm.Email.trim(),
    IPAllocation: clientForm.IPAllocation.trim() || null,
    AllowedIPs: clientForm.AllowedIPs.trim() || null,
    UseDNS: clientForm.UseDNS,
  }
  const keys = Object.fromEntries(
    ['PublicKey', 'PrivateKey', 'PresharedKey']
      .filter((key) => clientForm[key].trim())
      .map((key) => [key, clientForm[key].trim()]),
  )

  try {
    if (editingId.value) {
      await api.post(`/api/wg_tools/${encodeURIComponent(editingId.value)}/update`, payload)
      if (Object.keys(keys).length) {
        await api.put(
          `/api/wg_tools/clients/${encodeURIComponent(editingId.value)}/keys`,
          keys,
        )
      }
      setMessage('クライアント情報を更新しました。')
    } else {
      if (canAdmin.value && !keys.PrivateKey && !keys.PublicKey) {
        Object.assign(keys, (await api.post('/api/wg_tools/client/generate-keys', {})).data)
      }
      await api.post('/api/wg_tools/client/register', { ...payload, ...keys })
      setMessage('クライアントを追加しました。')
      await loadClients()
      closeClientForm()
    }
    if (!isCreating) {
      closeClientForm()
      await loadClients()
    }
  } catch (error) {
    setMessage(
      error.response?.status === 403
        ? 'この操作を行う権限がありません。'
        : '保存に失敗しました。入力内容と接続状態を確認してください。',
      true,
    )
  } finally {
    isSaving.value = false
  }
}

const toggleClient = async (client) => {
  const action = client.disabled ? 'enable' : 'disable'
  try {
    await api.post(`/api/wg_tools/${encodeURIComponent(client.ID)}/${action}`, {})
    setMessage(client.disabled ? 'クライアントを有効化しました。' : 'クライアントを無効化しました。')
    await loadClients()
  } catch (error) {
    setMessage(
      error.response?.status === 403
        ? 'この操作を行う権限がありません。'
        : '状態を更新できませんでした。再度お試しください。',
      true,
    )
  }
}

const downloadClientConfig = async (client) => {
  try {
    const response = await api.get(
      `/api/wg_tools/clients/${encodeURIComponent(client.ID)}/config`,
      { responseType: 'blob' },
    )
    const url = URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    link.download = `wireguard-client-${client.ID}.conf`
    document.body.append(link)
    link.click()
    link.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    setMessage(`${client.Name}の設定ファイルをダウンロードしました。`)
  } catch {
    setMessage('設定ファイルをダウンロードできませんでした。設定と鍵を確認してください。', true)
  }
}

const emailClientConfig = async (client) => {
  if (!window.confirm(`${client.Email}へ秘密鍵を含む設定ファイルとQRコードを送信します。続行しますか？`)) {
    return
  }

  try {
    await api.post(
      `/api/wg_tools/clients/${encodeURIComponent(client.ID)}/send-config`,
      {},
    )
    setMessage(`${client.Email}へ設定ファイルとQRコードを送信しました。`)
  } catch {
    setMessage('設定ファイルを送信できませんでした。設定・鍵・メールサーバーを確認してください。', true)
  }
}

const applyServerConfig = async () => {
  if (!window.confirm('WireGuardサーバー設定を適用します。通常はサーバーのサービスが再起動され、通信が一時的に切断される場合があります。続行しますか？')) {
    return
  }

  isSaving.value = true
  try {
    const response = await api.post('/api/wg_tools/server/apply', {})
    setMessage(response.data.mode === 'test-container'
      ? `WireGuardテストコンテナへ適用しました（interface: ${response.data.interface}, peer: ${response.data.peer_count}）。クライアントの起動を待って疎通を確認してください。`
      : `WireGuardサーバーへ適用しました（interface: ${response.data.interface}, peer: ${response.data.peer_count}）。`)
  } catch (error) {
    setMessage(
      error.response?.data?.detail
        || 'サーバー設定を適用できませんでした。サービスと設定を確認してください。',
      true,
    )
  } finally {
    isSaving.value = false
  }
}

const saveGlobalSettings = async () => {
  isSaving.value = true
  setMessage('')
  try {
    await api.post('/api/wg_tools/global_settings', {
      Endpoint: globalForm.Endpoint.trim(),
      DNSServer: globalForm.DNSServer.trim(),
      MTU: Number(globalForm.MTU),
      PersistentKeepalive: Number(globalForm.PersistentKeepalive),
      FirewallMark: globalForm.FirewallMark.trim() || null,
      Table: globalForm.Table.trim() || null,
    })
    globalSettingsExist.value = true
    setMessage('グローバル設定を保存しました。')
  } catch (error) {
    setMessage(
      error.response?.status === 403
        ? 'この操作を行う権限がありません。'
        : '設定を保存できませんでした。入力内容を確認してください。',
      true,
    )
  } finally {
    isSaving.value = false
  }
}

const saveServerSettings = async () => {
  isSaving.value = true
  setMessage('')
  const payload = {
    ServerInterface: serverForm.ServerInterface.trim(),
    ListenPort: Number(serverForm.ListenPort),
    Address: serverForm.Address.trim(),
    PostUpScript: serverForm.PostUpScript.trim() || null,
    PreDownScript: serverForm.PreDownScript.trim() || null,
    PostDownScript: serverForm.PostDownScript.trim() || null,
  }
  if (serverForm.PrivateKey.trim()) payload.PrivateKey = serverForm.PrivateKey.trim()

  try {
    await api.post('/api/wg_tools/server_settings', payload)
    serverSettingsExist.value = true
    if (canAdmin.value) await loadServerKeys()
    setMessage('サーバー設定を保存しました。')
  } catch (error) {
    setMessage(
      error.response?.status === 403
        ? 'この操作を行う権限がありません。'
        : '設定を保存できませんでした。入力内容を確認してください。',
      true,
    )
  } finally {
    isSaving.value = false
  }
}

const generateServerKeys = async () => {
  if (!window.confirm('サーバー鍵を再生成しますか？新しい鍵の保存後はクライアント設定の再配布とサーバー再適用が必要です。')) {
    return
  }

  try {
    const response = await api.post('/api/wg_tools/server_settings/keys/generate', {})
    serverForm.PrivateKey = response.data.PrivateKey
    serverForm.PublicKey = response.data.PublicKey
    showServerPrivateKey.value = false
    setMessage('新しいサーバー鍵を生成しました。設定を保存してからサーバーへ適用してください。')
  } catch {
    setMessage('サーバー鍵を生成できませんでした。', true)
  }
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
    await loadSection()
  } catch (error) {
    if (error.response?.status === 401) {
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

watch(() => route.path, () => {
  if (user.value) loadSection()
})
</script>

<template>
  <div class="wg-page">
    <header class="wg-topbar">
      <a class="wg-brand" href="/" aria-label="NagiFans Lab ホーム">
        <span class="wg-brand-mark">N</span>
        <span class="wg-brand-name">NagiFans <strong>Lab</strong></span>
      </a>
      <span class="wg-topbar-divider"></span>
      <span class="wg-topbar-section">管理コンソール</span>
      <div v-if="user" class="wg-topbar-user">
        <span class="wg-avatar">{{ userInitial }}</span>
        <span class="wg-topbar-username">{{ user.displayname }}</span>
        <button class="wg-logout-button" type="button" @click="handleLogout">ログアウト</button>
      </div>
    </header>

    <main class="wg-dashboard">
      <div class="wg-page-heading">
        <div>
          <p class="wg-eyebrow">WIREGUARD MANAGEMENT</p>
          <h1>WireGuard管理</h1>
          <p class="wg-page-description">クライアントとネットワーク設定を管理できます。</p>
        </div>
        <div class="wg-heading-badge">
          <span></span>{{ canManage ? '書き込み可能' : '読み取り専用' }}
        </div>
      </div>

      <nav class="wg-section-nav" aria-label="WireGuard設定">
        <RouterLink to="/wg_tools" :class="{ 'wg-section-active': section === 'clients' }">クライアント設定</RouterLink>
        <RouterLink to="/wg_tools/server_settings" :class="{ 'wg-section-active': section === 'server' }">サーバー設定</RouterLink>
        <RouterLink to="/wg_tools/global_settings" :class="{ 'wg-section-active': section === 'global' }">グローバル設定</RouterLink>
      </nav>

      <p v-if="message" class="wg-notice" :class="{ 'wg-notice-error': isMessageError }" role="status" aria-live="polite">
        <span>{{ isMessageError ? '!' : '✓' }}</span>{{ message }}
      </p>

      <template v-if="section === 'clients'">
        <section class="wg-summary-grid" aria-label="クライアント概要">
          <article class="wg-summary-card">
            <div class="wg-summary-icon wg-total-icon" aria-hidden="true">WG</div>
            <div><p>登録クライアント</p><strong>{{ clients.length }}<span>件</span></strong></div>
            <span class="wg-summary-decoration">01</span>
          </article>
          <article class="wg-summary-card">
            <div class="wg-summary-icon wg-active-icon" aria-hidden="true">✓</div>
            <div><p>有効</p><strong>{{ activeClientCount }}<span>件</span></strong></div>
            <span class="wg-summary-decoration">02</span>
          </article>
          <article class="wg-summary-card">
            <div class="wg-summary-icon wg-disabled-icon" aria-hidden="true">Ⅱ</div>
            <div><p>無効</p><strong>{{ disabledClientCount }}<span>件</span></strong></div>
            <span class="wg-summary-decoration">03</span>
          </article>
        </section>

        <section class="wg-panel wg-client-panel">
          <div class="wg-panel-heading">
            <div><h2>クライアント一覧</h2><p>登録済みクライアントを管理します</p></div>
            <button class="wg-count-pill" type="button" disabled>{{ clients.length }} 件</button>
            <button class="wg-primary-button" type="button" :disabled="!canManage" @click="openCreateForm">
              <span aria-hidden="true">＋</span> クライアント追加
            </button>
          </div>
          <label class="wg-search-box">
            <span class="wg-search-icon" aria-hidden="true"></span>
            <input v-model="searchQuery" type="search" placeholder="名前・メールアドレス・IPで検索" aria-label="クライアントを検索">
            <kbd>/</kbd>
          </label>

          <div class="wg-table-wrap">
            <table class="wg-client-table">
              <thead>
                <tr>
                  <th scope="col">クライアント</th>
                  <th scope="col">ステータス</th>
                  <th scope="col">割り当てIP</th>
                  <th scope="col">Allowed IPs</th>
                  <th scope="col">DNS</th>
                  <th scope="col">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="isLoading"><td class="wg-table-message" colspan="6">クライアント情報を読み込んでいます…</td></tr>
                <tr v-else-if="filteredClients.length === 0">
                  <td class="wg-table-message" colspan="6">
                    {{ searchQuery ? '検索条件に一致するクライアントはいません。' : 'クライアントはまだ登録されていません。' }}
                  </td>
                </tr>
                <tr v-for="client in filteredClients" :key="client.ID">
                  <td>
                    <div class="wg-client-cell">
                      <span class="wg-client-avatar">{{ client.Name?.trim()?.slice(0, 1) || '?' }}</span>
                      <span class="wg-client-details"><strong>{{ client.Name }}</strong><span>{{ client.Email }}</span></span>
                    </div>
                  </td>
                  <td>
                    <span class="wg-status-badge" :class="client.disabled ? 'wg-status-disabled' : 'wg-status-active'">
                      <span></span>{{ client.disabled ? '無効' : '有効' }}
                    </span>
                  </td>
                  <td class="wg-mono">{{ client.IPAllocation || '-' }}</td>
                  <td class="wg-mono">{{ client.AllowedIPs || '-' }}</td>
                  <td>{{ client.UseDNS ? '使用' : '不使用' }}</td>
                  <td>
                    <div class="wg-row-actions">
                      <button class="wg-action-button" type="button" :disabled="!canManage" @click="openEditForm(client)">編集</button>
                      <button
                        class="wg-action-button wg-action-config"
                        type="button"
                        :disabled="!canAdmin"
                        title="設定ファイルをダウンロード"
                        @click="downloadClientConfig(client)"
                      >DL</button>
                      <button
                        class="wg-action-button wg-action-config"
                        type="button"
                        :disabled="!canAdmin || !client.Email"
                        title="登録メールアドレスへ設定ファイルを送信"
                        @click="emailClientConfig(client)"
                      >メール</button>
                      <button
                        class="wg-action-button"
                        :class="client.disabled ? 'wg-action-enable' : 'wg-action-disable'"
                        type="button"
                        :disabled="!canManage"
                        @click="toggleClient(client)"
                      >{{ client.disabled ? '有効化' : '無効化' }}</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <footer class="wg-table-footer">
            <span>全 {{ clients.length }} 件のクライアント</span>
            <span>名前・メールアドレス・IPで検索できます</span>
          </footer>
        </section>
      </template>

      <template v-else-if="section === 'global'">
        <section class="wg-panel wg-settings-panel">
          <div class="wg-panel-heading">
            <div><h2>グローバル設定</h2><p>クライアント共通の接続オプションを設定します</p></div>
            <span class="wg-count-pill">{{ globalSettingsExist ? '設定済み' : '未設定' }}</span>
          </div>
          <div v-if="isLoading" class="wg-settings-loading">設定を読み込んでいます…</div>
          <form v-else class="wg-settings-form" @submit.prevent="saveGlobalSettings">
            <div class="wg-form-grid">
              <label class="wg-form-field">
                <span>Endpoint <b>*</b></span>
                <input v-model="globalForm.Endpoint" type="text" required :disabled="!canManage">
                <small>クライアントが接続するサーバーのアドレス</small>
              </label>
              <label class="wg-form-field">
                <span>DNS Server <b>*</b></span>
                <input v-model="globalForm.DNSServer" type="text" placeholder="1.1.1.1" required :disabled="!canManage">
                <small>クライアントに設定するDNSサーバー</small>
              </label>
              <label class="wg-form-field">
                <span>MTU <b>*</b></span>
                <input v-model="globalForm.MTU" type="number" min="1" max="65535" required :disabled="!canManage">
              </label>
              <label class="wg-form-field">
                <span>Persistent Keepalive <b>*</b></span>
                <input v-model="globalForm.PersistentKeepalive" type="number" min="0" max="65535" required :disabled="!canManage">
                <small>秒単位。無効にする場合は 0</small>
              </label>
              <label class="wg-form-field">
                <span>Firewall Mark</span>
                <input v-model="globalForm.FirewallMark" type="text" placeholder="0xca6c" :disabled="!canManage">
              </label>
              <label class="wg-form-field">
                <span>Routing Table</span>
                <input v-model="globalForm.Table" type="text" placeholder="auto" :disabled="!canManage">
              </label>
            </div>
            <div class="wg-settings-footer">
              <span>設定の変更は、今後生成するクライアント設定に適用されます。</span>
              <button class="wg-primary-button" type="submit" :disabled="!canManage || isSaving">
                {{ isSaving ? '保存中…' : 'グローバル設定を保存' }}
              </button>
            </div>
          </form>
        </section>
      </template>

      <template v-else>
        <section class="wg-panel wg-settings-panel">
          <div class="wg-panel-heading">
            <div><h2>サーバー設定</h2><p>WireGuardサーバーインターフェースを設定します</p></div>
            <span class="wg-count-pill">{{ serverSettingsExist ? '設定済み' : '未設定' }}</span>
          </div>
          <div v-if="isLoading" class="wg-settings-loading">設定を読み込んでいます…</div>
          <form v-else class="wg-settings-form" @submit.prevent="saveServerSettings">
            <div class="wg-form-grid">
              <label class="wg-form-field">
                <span>Server Interface <b>*</b></span>
                <input v-model="serverForm.ServerInterface" type="text" required :disabled="!canManage">
              </label>
              <label class="wg-form-field">
                <span>Listen Port <b>*</b></span>
                <input v-model="serverForm.ListenPort" type="number" min="1" max="65535" required :disabled="!canManage">
              </label>
              <label class="wg-form-field">
                <span>Server Address <b>*</b></span>
                <input v-model="serverForm.Address" type="text" placeholder="例: 10.77.0.1/24" required :disabled="!canManage">
              </label>
              <label class="wg-form-field">
                <span>Public Key</span>
                <input v-model="serverForm.PublicKey" type="text" autocomplete="off" readonly>
              </label>
              <label class="wg-form-field">
                <span>Private Key</span>
                <div class="wg-key-input">
                  <input
                    v-model="serverForm.PrivateKey"
                    :type="showServerPrivateKey ? 'text' : 'password'"
                    autocomplete="new-password"
                    :placeholder="canAdmin ? '鍵を読み込むか、新しい鍵を生成' : '管理者のみ表示・変更できます'"
                    :disabled="!canAdmin"
                  >
                  <button
                    type="button"
                    :disabled="!canAdmin || !serverForm.PrivateKey"
                    :aria-label="showServerPrivateKey ? 'Private Keyを隠す' : 'Private Keyを表示'"
                    @click="showServerPrivateKey = !showServerPrivateKey"
                  >{{ showServerPrivateKey ? '隠す' : '表示' }}</button>
                </div>
                <small>WireGuard Curve25519鍵。秘密鍵を変更した場合は設定保存後にサーバーへ適用してください。</small>
              </label>
              <label class="wg-form-field wg-form-field-wide">
                <span>Post Up Script</span>
                <textarea v-model="serverForm.PostUpScript" rows="3" placeholder="インターフェース起動後に実行するコマンド" :disabled="!canManage"></textarea>
              </label>
              <label class="wg-form-field wg-form-field-wide">
                <span>Pre Down Script</span>
                <textarea v-model="serverForm.PreDownScript" rows="3" placeholder="インターフェース停止前に実行するコマンド" :disabled="!canManage"></textarea>
              </label>
              <label class="wg-form-field wg-form-field-wide">
                <span>Post Down Script</span>
                <textarea v-model="serverForm.PostDownScript" rows="3" placeholder="インターフェース停止後に実行するコマンド" :disabled="!canManage"></textarea>
              </label>
            </div>
            <div class="wg-settings-footer">
              <span>初回保存時に鍵が自動生成されます。鍵を再生成した場合はクライアント設定の再配布が必要です。</span>
              <div class="wg-server-actions">
                <button
                  class="wg-secondary-button"
                  type="button"
                  :disabled="!canAdmin || isSaving"
                  @click="generateServerKeys"
                >サーバー鍵を再生成</button>
                <button
                  class="wg-secondary-button"
                  type="button"
                  :disabled="!canAdmin || isSaving"
                  @click="applyServerConfig"
                >サーバー設定を適用</button>
                <button class="wg-primary-button" type="submit" :disabled="!canManage || isSaving">
                  {{ isSaving ? '保存中…' : 'サーバー設定を保存' }}
                </button>
              </div>
            </div>
          </form>
        </section>
      </template>

      <footer class="wg-page-footer"><span>NagiFans Lab</span><span>WireGuard管理</span></footer>
    </main>

    <div v-if="isModalOpen" class="wg-modal-backdrop" @click.self="closeClientForm">
      <section class="wg-modal" role="dialog" aria-modal="true" aria-labelledby="wg-modal-title">
        <div class="wg-modal-heading">
          <div><p class="wg-eyebrow">{{ editingId ? 'CLIENT SETTINGS' : 'NEW CLIENT' }}</p>
            <h2 id="wg-modal-title">{{ editingId ? 'クライアントを編集' : 'クライアントを追加' }}</h2>
          </div>
          <button class="wg-modal-close" type="button" aria-label="閉じる" @click="closeClientForm">×</button>
        </div>
        <form class="wg-client-form" @submit.prevent="saveClient">
          <label class="wg-form-field"><span>表示名 <b>*</b></span><input v-model="clientForm.Name" type="text" maxlength="120" required></label>
          <label class="wg-form-field"><span>メールアドレス <b>*</b></span><input v-model="clientForm.Email" type="email" maxlength="254" required></label>
          <label class="wg-form-field"><span>割り当てIP</span><input v-model="clientForm.IPAllocation" type="text" placeholder="例: 10.0.0.2/32"></label>
          <label class="wg-form-field"><span>Allowed IPs</span><input v-model="clientForm.AllowedIPs" type="text" placeholder="例: 0.0.0.0/0, ::/0"></label>
          <label class="wg-checkbox-field"><input v-model="clientForm.UseDNS" type="checkbox"><span>クライアントでDNSを使用する</span></label>
          <div class="wg-key-fields">
            <div class="wg-key-heading">
              <div><strong>クライアント鍵</strong><span>空欄の鍵は変更せず、そのまま保持します。</span></div>
              <div class="wg-key-actions">
                <button
                  v-if="canAdmin"
                  class="wg-load-keys-button"
                  type="button"
                  :disabled="isSaving || isLoadingClientKeys"
                  @click="generateClientKeys"
                >鍵を自動生成</button>
                <button
                  v-if="editingId && canAdmin"
                  class="wg-load-keys-button"
                  type="button"
                  :disabled="isLoadingClientKeys || isSaving"
                  @click="loadClientKeys"
                >{{ isLoadingClientKeys ? '読込中…' : '保存済みの鍵を表示' }}</button>
              </div>
            </div>
            <label class="wg-form-field">
              <span>Public Key</span>
              <input v-model="clientForm.PublicKey" type="text" autocomplete="off">
            </label>
            <label class="wg-form-field">
              <span>Private Key</span>
              <div class="wg-key-input">
                <input v-model="clientForm.PrivateKey" :type="showPrivateKey ? 'text' : 'password'" autocomplete="new-password">
                <button
                  type="button"
                  :aria-label="showPrivateKey ? 'Private Keyを隠す' : 'Private Keyを表示'"
                  @click="showPrivateKey = !showPrivateKey"
                >{{ showPrivateKey ? '隠す' : '表示' }}</button>
              </div>
            </label>
            <label class="wg-form-field">
              <span>Preshared Key</span>
              <div class="wg-key-input">
                <input v-model="clientForm.PresharedKey" :type="showPresharedKey ? 'text' : 'password'" autocomplete="new-password">
                <button
                  type="button"
                  :aria-label="showPresharedKey ? 'Preshared Keyを隠す' : 'Preshared Keyを表示'"
                  @click="showPresharedKey = !showPresharedKey"
                >{{ showPresharedKey ? '隠す' : '表示' }}</button>
              </div>
            </label>
            <p class="wg-key-warning">Private KeyとPreshared Keyは機密情報です。読み込み後は画面上に表示されます。</p>
          </div>
          <div class="wg-modal-actions">
            <button class="wg-secondary-button" type="button" :disabled="isSaving" @click="closeClientForm">キャンセル</button>
            <button class="wg-primary-button" type="submit" :disabled="isSaving">{{ isSaving ? '保存中…' : '保存する' }}</button>
          </div>
        </form>
      </section>
    </div>
  </div>
</template>

<style scoped>
.wg-page {
  --wg-ink: #192b3d;
  --wg-muted: #78889a;
  --wg-line: #e7edf2;
  --wg-paper: #fff;
  --wg-blue: #2874c8;
  min-height: 100vh;
  color: var(--wg-ink);
  background:
    radial-gradient(ellipse at 87% 2%, rgb(201 225 247 / 27%), transparent 28rem),
    #f4f7fa;
  font-family: "Mona Sans VF", -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
}

.wg-page *,
.wg-page *::before,
.wg-page *::after {
  box-sizing: border-box;
}

.wg-topbar {
  display: flex;
  height: 72px;
  align-items: center;
  gap: 20px;
  padding: 0 clamp(20px, 5vw, 72px);
  border-bottom: 1px solid #e8eef3;
  background: rgb(255 255 255 / 92%);
}

.wg-brand {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  color: var(--wg-ink);
  text-decoration: none;
}

.wg-brand-mark {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border-radius: 11px;
  color: #fff;
  background: linear-gradient(145deg, #4195df, #2467b3);
  box-shadow: 0 5px 12px rgb(40 116 200 / 20%);
  font-size: 17px;
  font-weight: 800;
}

.wg-brand-name {
  font-size: 15px;
  letter-spacing: -0.035em;
}

.wg-brand-name strong {
  font-weight: 750;
}

.wg-topbar-divider {
  width: 1px;
  height: 23px;
  background: var(--wg-line);
}

.wg-topbar-section {
  color: #8190a0;
  font-size: 13px;
}

.wg-topbar-user {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}

.wg-avatar,
.wg-client-avatar {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
}

.wg-avatar {
  width: 34px;
  height: 34px;
  color: #316fae;
  background: #e7f1fb;
  font-size: 13px;
  font-weight: 700;
}

.wg-topbar-username {
  max-width: 180px;
  overflow: hidden;
  color: #435568;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wg-logout-button {
  margin-left: 8px;
  padding: 8px 12px;
  border: 1px solid var(--wg-line);
  border-radius: 8px;
  color: #56687a;
  background: #fff;
  cursor: pointer;
  font: inherit;
  font-size: 12px;
}

.wg-logout-button:hover {
  border-color: #b8cadb;
  color: var(--wg-ink);
}

.wg-dashboard {
  width: min(1320px, 100%);
  margin: 0 auto;
  padding: 42px clamp(20px, 5vw, 72px) 28px;
}

.wg-page-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 20px;
}

.wg-eyebrow {
  margin: 0 0 8px;
  color: #6b95bd;
  font-size: 10px;
  font-weight: 750;
  letter-spacing: 0.16em;
}

.wg-page-heading h1 {
  margin: 0;
  color: #172a3d;
  font-size: clamp(26px, 3vw, 34px);
  font-weight: 720;
  letter-spacing: -0.045em;
}

.wg-page-description {
  margin: 9px 0 0;
  color: var(--wg-muted);
  font-size: 13px;
}

.wg-heading-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #dceaf6;
  border-radius: 20px;
  color: #4a7296;
  background: rgb(255 255 255 / 70%);
  font-size: 11px;
  font-weight: 650;
  white-space: nowrap;
}

.wg-heading-badge span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #55b88a;
}

.wg-section-nav {
  display: flex;
  gap: 5px;
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--wg-line);
}

.wg-section-nav::-webkit-scrollbar {
  display: none;
}

.wg-section-nav a {
  position: relative;
  flex: 0 0 auto;
  padding: 11px 14px 12px;
  color: #768698;
  font-size: 12px;
  text-decoration: none;
  transition: color 0.18s;
}

.wg-section-nav a:hover,
.wg-section-nav a.wg-section-active {
  color: #286da9;
}

.wg-section-nav a.wg-section-active {
  font-weight: 650;
}

.wg-section-nav a.wg-section-active::after {
  position: absolute;
  right: 12px;
  bottom: -1px;
  left: 12px;
  height: 2px;
  border-radius: 2px 2px 0 0;
  background: #2874c8;
  content: "";
}

.wg-notice {
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 0 0 19px;
  padding: 11px 13px;
  border: 1px solid #d8ecdf;
  border-radius: 8px;
  color: #478268;
  background: #f1faf4;
  font-size: 12px;
}

.wg-notice > span {
  display: grid;
  width: 18px;
  height: 18px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  background: #62ae83;
  font-size: 11px;
}

.wg-notice-error {
  border-color: #f2d9d4;
  color: #a74f43;
  background: #fff7f5;
}

.wg-notice-error > span {
  background: #c77668;
}

.wg-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.wg-summary-card {
  position: relative;
  display: flex;
  min-height: 112px;
  align-items: center;
  gap: 15px;
  overflow: hidden;
  padding: 20px;
  border: 1px solid var(--wg-line);
  border-radius: 12px;
  background: var(--wg-paper);
  box-shadow: 0 3px 12px rgb(36 61 82 / 2.5%);
}

.wg-summary-icon {
  display: grid;
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 700;
}

.wg-total-icon {
  color: #427cb5;
  background: #edf5fc;
}

.wg-active-icon {
  color: #388d6a;
  background: #eaf7f0;
}

.wg-disabled-icon {
  color: #9a7a4b;
  background: #f8f2e8;
}

.wg-summary-card p {
  margin: 0 0 5px;
  color: #8290a0;
  font-size: 12px;
}

.wg-summary-card strong {
  color: #24384b;
  font-size: 27px;
  font-weight: 720;
  letter-spacing: -0.04em;
  line-height: 1;
}

.wg-summary-card strong span {
  margin-left: 4px;
  color: #8695a3;
  font-size: 12px;
  font-weight: 500;
}

.wg-summary-decoration {
  position: absolute;
  top: 17px;
  right: 18px;
  color: #eef2f6;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.wg-panel {
  min-width: 0;
  border: 1px solid var(--wg-line);
  border-radius: 12px;
  background: var(--wg-paper);
  box-shadow: 0 3px 12px rgb(36 61 82 / 2.5%);
}

.wg-client-panel {
  overflow: hidden;
}

.wg-panel-heading {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 22px 22px 17px;
}

.wg-panel-heading > div {
  margin-right: auto;
}

.wg-panel-heading h2 {
  margin: 0;
  color: #263a4d;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.wg-panel-heading p {
  margin: 5px 0 0;
  color: #8a98a6;
  font-size: 11px;
}

.wg-count-pill {
  padding: 5px 9px;
  border: 0;
  border-radius: 20px;
  color: #67839d;
  background: #f0f5f9;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.wg-primary-button,
.wg-secondary-button {
  display: inline-flex;
  min-height: 38px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 13px;
  border: 0;
  border-radius: 7px;
  cursor: pointer;
  font: inherit;
  font-size: 11px;
  font-weight: 650;
  text-decoration: none;
  transition: background 0.18s, transform 0.18s;
}

.wg-primary-button {
  color: #fff;
  background: var(--wg-blue);
  box-shadow: 0 4px 9px rgb(40 116 200 / 18%);
}

.wg-primary-button:hover:not(:disabled) {
  transform: translateY(-1px);
  background: #1d5fa9;
}

.wg-primary-button:disabled,
.wg-secondary-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.wg-search-box {
  display: flex;
  height: 40px;
  align-items: center;
  gap: 10px;
  margin: 0 22px 16px;
  padding: 0 11px;
  border: 1px solid #e7edf2;
  border-radius: 8px;
  background: #fbfcfd;
  transition: border-color 0.18s, box-shadow 0.18s;
}

.wg-search-box:focus-within {
  border-color: #9dc3e5;
  box-shadow: 0 0 0 3px rgb(40 116 200 / 8%);
}

.wg-search-icon {
  position: relative;
  width: 13px;
  height: 13px;
  flex: 0 0 auto;
  border: 1.5px solid #93a2af;
  border-radius: 50%;
}

.wg-search-icon::after {
  position: absolute;
  right: -4px;
  bottom: -3px;
  width: 5px;
  height: 1.5px;
  transform: rotate(45deg);
  transform-origin: left center;
  background: #93a2af;
  content: "";
}

.wg-search-box input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: 0;
  color: #31485b;
  background: transparent;
  font: inherit;
  font-size: 12px;
}

.wg-search-box input::placeholder {
  color: #a0acb7;
}

.wg-search-box kbd {
  min-width: 21px;
  padding: 2px 5px;
  border: 1px solid #e6ebf0;
  border-radius: 4px;
  color: #9ba8b4;
  background: #fff;
  font-family: inherit;
  font-size: 10px;
  text-align: center;
}

.wg-table-wrap {
  width: 100%;
  overflow-x: auto;
}

.wg-client-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.wg-client-table th {
  padding: 11px 14px;
  border-top: 1px solid #edf1f4;
  border-bottom: 1px solid #edf1f4;
  color: #8b98a5;
  background: #fafbfd;
  font-size: 10px;
  font-weight: 650;
  letter-spacing: 0.035em;
  white-space: nowrap;
}

.wg-client-table th:first-child,
.wg-client-table td:first-child {
  padding-left: 22px;
}

.wg-client-table th:last-child,
.wg-client-table td:last-child {
  padding-right: 22px;
}

.wg-client-table td {
  padding: 13px 14px;
  border-bottom: 1px solid #eff2f5;
  color: #536576;
  font-size: 11px;
  vertical-align: middle;
}

.wg-client-table tbody tr:last-child td {
  border-bottom: 0;
}

.wg-client-cell {
  display: flex;
  min-width: 170px;
  align-items: center;
  gap: 10px;
}

.wg-client-avatar {
  width: 33px;
  height: 33px;
  color: #647d94;
  background: #eef2f5;
  font-size: 12px;
  font-weight: 700;
}

.wg-client-details {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.wg-client-details strong,
.wg-client-details span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wg-client-details strong {
  color: #314558;
  font-size: 11px;
  font-weight: 650;
}

.wg-client-details span {
  color: #8c99a6;
  font-size: 10px;
}

.wg-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-radius: 20px;
  font-size: 10px;
  font-weight: 600;
  white-space: nowrap;
}

.wg-status-badge > span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.wg-status-active {
  color: #43856c;
  background: #edf7f1;
}

.wg-status-active > span {
  background: #54b287;
}

.wg-status-disabled {
  color: #957b55;
  background: #f8f3e9;
}

.wg-status-disabled > span {
  background: #c8a86d;
}

.wg-mono {
  font-family: "DM Mono", "SFMono-Regular", Consolas, monospace;
  font-size: 10px !important;
  white-space: nowrap;
}

.wg-row-actions {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  white-space: nowrap;
}

.wg-action-button {
  padding: 6px 7px;
  border: 1px solid transparent;
  border-radius: 6px;
  color: #65798b;
  background: transparent;
  cursor: pointer;
  font: inherit;
  font-size: 10px;
  transition: background 0.16s, color 0.16s, border-color 0.16s;
}

.wg-action-button:hover:not(:disabled) {
  border-color: #dce8f2;
  color: #286da9;
  background: #f3f8fc;
}

.wg-action-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.wg-action-button.wg-action-disable:hover:not(:disabled) {
  border-color: #f0ded7;
  color: #a55f4d;
  background: #fff7f4;
}

.wg-action-button.wg-action-enable:hover:not(:disabled) {
  border-color: #d8ebdf;
  color: #3e8b68;
  background: #f2faf5;
}

.wg-action-config {
  color: #3977a5;
}

.wg-server-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.wg-table-message {
  height: 110px;
  color: #8997a4 !important;
  text-align: center;
}

.wg-table-footer,
.wg-page-footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #98a4af;
  font-size: 10px;
}

.wg-table-footer {
  padding: 13px 22px;
  border-top: 1px solid #edf1f4;
}

.wg-page-footer {
  margin-top: 25px;
  color: #a3aeb8;
}

.wg-settings-panel {
  overflow: hidden;
}

.wg-settings-panel > .wg-panel-heading {
  padding-bottom: 18px;
}

.wg-settings-loading {
  padding: 35px 22px;
  border-top: 1px solid #edf1f4;
  color: #8997a4;
  font-size: 12px;
  text-align: center;
}

.wg-settings-form {
  padding: 22px;
  border-top: 1px solid #edf1f4;
}

.wg-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px 18px;
}

.wg-form-field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
}

.wg-form-field > span {
  color: #526579;
  font-size: 11px;
  font-weight: 650;
}

.wg-form-field b {
  color: #c56d5e;
}

.wg-form-field input,
.wg-form-field textarea {
  width: 100%;
  min-height: 40px;
  padding: 9px 11px;
  border: 1px solid #e3eaf0;
  border-radius: 7px;
  outline: 0;
  color: #34495c;
  background: #fcfdfe;
  font: inherit;
  font-size: 12px;
  transition: border-color 0.18s, box-shadow 0.18s;
}

.wg-form-field textarea {
  min-height: 86px;
  resize: vertical;
  font-family: "DM Mono", "SFMono-Regular", Consolas, monospace;
  font-size: 11px;
  line-height: 1.6;
}

.wg-form-field input:focus,
.wg-form-field textarea:focus {
  border-color: #92bce0;
  box-shadow: 0 0 0 3px rgb(40 116 200 / 8%);
}

.wg-form-field input:disabled,
.wg-form-field textarea:disabled {
  color: #8794a2;
  background: #f7f9fb;
  cursor: not-allowed;
}

.wg-form-field small {
  color: #98a4af;
  font-size: 10px;
  line-height: 1.5;
}

.wg-form-field-wide {
  grid-column: 1 / -1;
}

.wg-settings-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-top: 24px;
  padding-top: 18px;
  border-top: 1px solid #edf1f4;
}

.wg-settings-footer > span {
  color: #8997a4;
  font-size: 10px;
  line-height: 1.6;
}

.wg-secondary-button {
  border: 1px solid #e0e7ed;
  color: #56687a;
  background: #fff;
}

.wg-secondary-button:hover:not(:disabled) {
  border-color: #b8cadb;
  color: var(--wg-ink);
}

.wg-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 10;
  display: grid;
  overflow-y: auto;
  place-items: center;
  padding: 22px;
  background: rgb(20 37 54 / 48%);
}

.wg-modal {
  width: min(100%, 480px);
  padding: 23px;
  border: 1px solid #e7edf2;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 18px 60px rgb(20 37 54 / 20%);
}

.wg-modal-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 22px;
}

.wg-modal-heading .wg-eyebrow {
  margin-bottom: 6px;
}

.wg-modal-heading h2 {
  margin: 0;
  color: #263a4d;
  font-size: 18px;
}

.wg-modal-close {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border: 1px solid #e4eaf0;
  border-radius: 7px;
  color: #798897;
  background: #fff;
  cursor: pointer;
  font-size: 18px;
}

.wg-client-form {
  display: grid;
  gap: 15px;
}

.wg-key-fields {
  display: grid;
  gap: 14px;
  padding: 15px;
  border: 1px solid #e7edf2;
  border-radius: 9px;
  background: #fbfcfd;
}

.wg-key-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.wg-key-heading > div {
  display: grid;
  gap: 4px;
}

.wg-key-heading strong {
  color: #40546a;
  font-size: 11px;
}

.wg-key-heading span,
.wg-key-warning {
  color: #8997a4;
  font-size: 10px;
  line-height: 1.5;
}

.wg-key-warning {
  margin: -4px 0 0;
}

.wg-key-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.wg-load-keys-button {
  flex: 0 0 auto;
  padding: 6px 8px;
  border: 1px solid #dce8f2;
  border-radius: 6px;
  color: #286da9;
  background: #fff;
  cursor: pointer;
  font: inherit;
  font-size: 10px;
}

.wg-load-keys-button:hover:not(:disabled) {
  background: #f3f8fc;
}

.wg-load-keys-button:disabled {
  cursor: wait;
  opacity: 0.6;
}

.wg-key-input {
  position: relative;
}

.wg-key-input input {
  padding-right: 52px;
}

.wg-key-input button {
  position: absolute;
  top: 50%;
  right: 7px;
  transform: translateY(-50%);
  padding: 5px 7px;
  border: 0;
  border-radius: 5px;
  color: #64798b;
  background: transparent;
  cursor: pointer;
  font: inherit;
  font-size: 10px;
}

.wg-key-input button:hover {
  color: #286da9;
  background: #f0f5f9;
}

.wg-checkbox-field {
  display: flex;
  align-items: center;
  gap: 9px;
  color: #56647a;
  cursor: pointer;
  font-size: 11px;
}

.wg-checkbox-field input {
  width: 15px;
  height: 15px;
  accent-color: var(--wg-blue);
}

.wg-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 6px;
}

@media (max-width: 980px) {
  .wg-dashboard {
    padding-right: 28px;
    padding-left: 28px;
  }

  .wg-row-actions {
    gap: 1px;
  }

  .wg-action-button {
    padding-right: 5px;
    padding-left: 5px;
  }
}

@media (max-width: 760px) {
  .wg-topbar {
    height: 64px;
    gap: 13px;
    padding: 0 20px;
  }

  .wg-topbar-section {
    font-size: 11px;
  }

  .wg-topbar-username {
    display: none;
  }

  .wg-logout-button {
    margin-left: 0;
  }

  .wg-dashboard {
    padding: 32px 20px 24px;
  }

  .wg-summary-grid {
    gap: 9px;
  }

  .wg-summary-card {
    min-height: 100px;
    align-items: flex-start;
    flex-direction: column;
    gap: 7px;
    padding: 12px;
  }

  .wg-summary-icon {
    width: 29px;
    height: 29px;
    border-radius: 8px;
    font-size: 11px;
  }

  .wg-summary-card p {
    margin-bottom: 4px;
    font-size: 10px;
    white-space: nowrap;
  }

  .wg-summary-card strong {
    font-size: 20px;
  }

  .wg-summary-decoration {
    top: 13px;
    right: 12px;
    font-size: 9px;
  }

  .wg-settings-form {
    padding: 18px 15px;
  }

  .wg-client-table {
    min-width: 750px;
  }
}

@media (max-width: 540px) {
  .wg-brand-name {
    font-size: 13px;
  }

  .wg-topbar {
    gap: 10px;
    padding: 0 14px;
  }

  .wg-topbar-section {
    font-size: 10px;
  }

  .wg-logout-button {
    padding: 7px 9px;
    font-size: 11px;
  }

  .wg-dashboard {
    padding: 27px 14px 20px;
  }

  .wg-page-heading {
    align-items: flex-start;
    margin-bottom: 17px;
  }

  .wg-page-description {
    max-width: 290px;
    font-size: 12px;
    line-height: 1.6;
  }

  .wg-heading-badge {
    padding: 7px 9px;
    font-size: 10px;
  }

  .wg-section-nav {
    margin-right: -14px;
    margin-left: -14px;
    padding: 0 7px;
  }

  .wg-section-nav a {
    padding: 10px 9px 11px;
    font-size: 11px;
  }

  .wg-summary-grid {
    gap: 8px;
    margin-bottom: 13px;
  }

  .wg-summary-card {
    min-height: 94px;
    padding: 10px;
  }

  .wg-summary-decoration {
    display: none;
  }

  .wg-panel-heading {
    flex-wrap: wrap;
    padding: 18px 15px 14px;
  }

  .wg-panel-heading > div {
    width: 100%;
  }

  .wg-panel-heading h2 {
    font-size: 15px;
  }

  .wg-panel-heading .wg-count-pill {
    margin-right: auto;
  }

  .wg-search-box {
    margin-right: 15px;
    margin-left: 15px;
  }

  .wg-client-table th:first-child,
  .wg-client-table td:first-child {
    padding-left: 15px;
  }

  .wg-client-table th:last-child,
  .wg-client-table td:last-child {
    padding-right: 15px;
  }

  .wg-table-footer {
    padding: 13px 15px;
  }

  .wg-table-footer > span:last-child {
    display: none;
  }

  .wg-page-footer {
    margin-top: 19px;
  }

  .wg-form-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .wg-form-field-wide {
    grid-column: auto;
  }

  .wg-settings-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .wg-server-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .wg-server-actions .wg-primary-button,
  .wg-server-actions .wg-secondary-button {
    width: 100%;
  }

  .wg-settings-footer .wg-primary-button {
    width: 100%;
  }
}
</style>

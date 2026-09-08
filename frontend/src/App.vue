<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import { fetchStores } from './api'
import { connectionLabel, formatMoney } from './format'
import type { Store } from './types'

const stores = ref<Store[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const wsConnected = ref(false)
const lastRefresh = ref<Date | null>(null)
let socket: WebSocket | null = null
let reconnectTimer: number | null = null
let reconnectAttempt = 0
let refreshTimer: number | null = null
let pollingTimer: number | null = null
let stopped = false

const onlineCount = computed(() => stores.value.filter((store) => store.online).length)
const websocketUrl = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000/ws/dashboard'

async function refreshStores(): Promise<void> {
  try {
    stores.value = await fetchStores()
    error.value = null
    lastRefresh.value = new Date()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Unknown API error'
  } finally {
    loading.value = false
  }
}

function scheduleRefresh(): void {
  if (refreshTimer !== null) {
    window.clearTimeout(refreshTimer)
  }
  refreshTimer = window.setTimeout(() => void refreshStores(), 150)
}

function connectWebSocket(): void {
  if (stopped) return

  const currentSocket = new WebSocket(websocketUrl)
  socket = currentSocket

  currentSocket.onopen = () => {
    if (socket !== currentSocket) return
    wsConnected.value = true
    reconnectAttempt = 0
  }

  currentSocket.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data) as { type?: string }
      if (payload.type === 'stores.changed') {
        scheduleRefresh()
      }
    } catch {
      // Ignore malformed development messages; authoritative state still comes from REST.
    }
  }

  currentSocket.onclose = () => {
    if (socket !== currentSocket || stopped) return
    wsConnected.value = false
    const delay = Math.min(1000 * 2 ** reconnectAttempt, 10_000)
    reconnectAttempt += 1
    reconnectTimer = window.setTimeout(connectWebSocket, delay)
  }

  currentSocket.onerror = () => currentSocket.close()
}

onMounted(() => {
  void refreshStores()
  connectWebSocket()
  pollingTimer = window.setInterval(() => void refreshStores(), 10_000)
})

onBeforeUnmount(() => {
  stopped = true
  if (reconnectTimer !== null) window.clearTimeout(reconnectTimer)
  if (refreshTimer !== null) window.clearTimeout(refreshTimer)
  if (pollingTimer !== null) window.clearInterval(pollingTimer)
  if (socket) {
    socket.onclose = null
    socket.close()
  }
})
</script>

<template>
  <main class="shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">MAD DEVS TAKE-HOME · CASE 5</p>
        <h1>StorePulse</h1>
        <p class="subtitle">Realtime retail operations foundation</p>
      </div>
      <div class="connection" :class="{ connected: wsConnected }">
        <span class="dot" />
        {{ connectionLabel(wsConnected) }}
      </div>
    </header>

    <section class="notice">
      <strong>Foundation checkpoint.</strong>
      Heartbeats, PostgreSQL persistence and multi-client realtime invalidation are active. Sales ranking and analytics are intentionally the next phase.
    </section>

    <section class="summary-grid">
      <article class="metric">
        <span>Seeded stores</span>
        <strong>{{ stores.length }}</strong>
      </article>
      <article class="metric">
        <span>Online now</span>
        <strong>{{ onlineCount }}</strong>
      </article>
      <article class="metric">
        <span>Ranking window</span>
        <strong>Pending</strong>
      </article>
      <article class="metric">
        <span>Last refresh</span>
        <strong>{{ lastRefresh ? lastRefresh.toLocaleTimeString() : '—' }}</strong>
      </article>
    </section>

    <section class="panel">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">CONNECTIVITY</p>
          <h2>Store heartbeat status</h2>
        </div>
        <button type="button" @click="refreshStores">Refresh</button>
      </div>

      <p v-if="loading">Loading stores…</p>
      <p v-else-if="error" class="error">{{ error }}</p>

      <div v-else class="store-grid">
        <article v-for="store in stores" :key="store.id" class="store-card">
          <div class="store-title">
            <div>
              <h3>{{ store.name }}</h3>
              <code>{{ store.code }}</code>
            </div>
            <span class="status" :class="store.online ? 'online' : 'offline'">
              {{ store.online ? 'ONLINE' : 'OFFLINE' }}
            </span>
          </div>
          <dl>
            <div><dt>Timezone</dt><dd>{{ store.timezone }}</dd></div>
            <div><dt>Daily target</dt><dd>{{ formatMoney(store.daily_target_cents) }}</dd></div>
            <div><dt>Responsible</dt><dd>{{ store.responsible_name }}</dd></div>
            <div><dt>Last heartbeat</dt><dd>{{ store.last_seen_at ? new Date(store.last_seen_at).toLocaleTimeString() : 'Never' }}</dd></div>
          </dl>
        </article>
      </div>
    </section>
  </main>
</template>

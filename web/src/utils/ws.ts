/**
 * WebSocket 客户端 — 实时行情数据
 */

export type WSCallback = (data: any) => void

export class MarketWS {
  private ws: WebSocket | null = null
  private market: string
  private callbacks: WSCallback[] = []
  private reconnectTimer: number | null = null
  private heartbeatTimer: number | null = null

  constructor(market: string) {
    this.market = market
  }

  connect() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${location.host}/ws/market/${this.market}`
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      this._startHeartbeat()
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.callbacks.forEach(cb => cb(data))
      } catch { /* ignore parse errors */ }
    }

    this.ws.onclose = () => {
      this._stopHeartbeat()
      this._scheduleReconnect()
    }

    this.ws.onerror = () => {
      this.ws?.close()
    }
  }

  onMessage(callback: WSCallback) {
    this.callbacks.push(callback)
  }

  disconnect() {
    this._stopHeartbeat()
    this._stopReconnect()
    this.ws?.close()
    this.callbacks = []
  }

  private _startHeartbeat() {
    this.heartbeatTimer = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send('ping')
      }
    }, 30000)
  }

  private _stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private _scheduleReconnect() {
    this.reconnectTimer = window.setTimeout(() => this.connect(), 3000)
  }

  private _stopReconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }
}

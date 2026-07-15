/**
 * SSE (Server-Sent Events) 处理工具
 */

export interface SSEOptions {
  onMessage?: (data: any) => void
  onError?: (error: Event) => void
  onOpen?: () => void
  onClose?: () => void
}

/**
 * 创建 SSE 连接
 */
export const createSSEConnection = (
  url: string,
  options: SSEOptions = {}
): EventSource => {
  const eventSource = new EventSource(url)

  if (options.onOpen) {
    eventSource.addEventListener('open', options.onOpen)
  }

  if (options.onMessage) {
    eventSource.addEventListener('message', (event) => {
      if (event.data === '[DONE]') {
        eventSource.close()
        options.onClose?.()
        return
      }

      try {
        const data = JSON.parse(event.data)
        options.onMessage!(data)
      } catch (error) {
        console.error('Parse SSE data error:', error)
      }
    })
  }

  if (options.onError) {
    eventSource.addEventListener('error', (error) => {
      options.onError!(error)
      eventSource.close()
    })
  }

  return eventSource
}

/**
 * 流式消息聚合器
 */
export class StreamAggregator {
  private buffer: string = ''
  private callbacks: ((text: string) => void)[] = []

  /**
   * 添加数据块
   */
  add(chunk: string) {
    this.buffer += chunk
    this.callbacks.forEach(cb => cb(this.buffer))
  }

  /**
   * 监听变化
   */
  onChange(callback: (text: string) => void) {
    this.callbacks.push(callback)
  }

  /**
   * 获取完整内容
   */
  getContent(): string {
    return this.buffer
  }

  /**
   * 清空缓冲区
   */
  clear() {
    this.buffer = ''
  }
}

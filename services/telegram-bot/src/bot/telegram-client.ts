import type { Logger } from "../config/logger.js"

export type TelegramUpdate = {
  update_id: number
  message?: {
    chat: { id: number }
    text?: string
    from?: {
      username?: string
    }
  }
}

type GetUpdatesResponse = {
  ok: boolean
  result: TelegramUpdate[]
}

type TelegramClientOptions = {
  token: string
  timeoutSeconds: number
  logger: Logger
}

export class TelegramClient {
  private readonly baseUrl: string

  constructor(private readonly options: TelegramClientOptions) {
    this.baseUrl = `https://api.telegram.org/bot${options.token}`
  }

  async getUpdates(offset: number): Promise<TelegramUpdate[]> {
    this.options.logger.debug("[TelegramClient.getUpdates] Fetching updates", {
      offset,
      timeoutSeconds: this.options.timeoutSeconds
    })

    const response = await fetch(`${this.baseUrl}/getUpdates`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        timeout: this.options.timeoutSeconds,
        offset
      })
    })

    if (!response.ok) {
      this.options.logger.error("[TelegramClient.getUpdates] HTTP error", {
        status: response.status
      })
      throw new Error(`Telegram getUpdates failed with status ${response.status}`)
    }

    const body = (await response.json()) as GetUpdatesResponse
    this.options.logger.debug("[TelegramClient.getUpdates] Received updates", {
      count: body.result.length
    })
    return body.result
  }

  async sendMessage(chatId: number, text: string): Promise<void> {
    this.options.logger.debug("[TelegramClient.sendMessage] Sending message", {
      chatId,
      preview: text.slice(0, 80)
    })

    const response = await fetch(`${this.baseUrl}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: chatId,
        text
      })
    })

    if (!response.ok) {
      this.options.logger.error("[TelegramClient.sendMessage] HTTP error", {
        status: response.status,
        chatId
      })
      throw new Error(`Telegram sendMessage failed with status ${response.status}`)
    }

    this.options.logger.info("[TelegramClient.sendMessage] Message sent", { chatId })
  }
}

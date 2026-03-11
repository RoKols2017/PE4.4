import type { Logger } from "../config/logger.js"
import { TelegramClient, type TelegramUpdate } from "./telegram-client.js"

export type MessageProcessor = {
  processMessage(input: {
    chatId: number
    text: string
    username?: string
  }): Promise<string>
}

type RouterOptions = {
  telegramClient: TelegramClient
  messageProcessor: MessageProcessor
  logger: Logger
}

export class BotRouter {
  constructor(private readonly options: RouterOptions) {}

  async routeUpdate(update: TelegramUpdate): Promise<void> {
    const message = update.message
    if (!message?.text) {
      this.options.logger.debug("[BotRouter.routeUpdate] Skipping non-text update", {
        updateId: update.update_id
      })
      return
    }

    const chatId = message.chat.id
    const text = message.text.trim()
    this.options.logger.debug("[BotRouter.routeUpdate] Routing message", {
      chatId,
      updateId: update.update_id,
      textPreview: text.slice(0, 80)
    })

    try {
      const responseText = await this.options.messageProcessor.processMessage({
        chatId,
        text,
        username: message.from?.username
      })

      await this.options.telegramClient.sendMessage(chatId, responseText)
    } catch (error) {
      this.options.logger.error("[BotRouter.routeUpdate] Failed to process update", {
        chatId,
        error: error instanceof Error ? error.message : "unknown"
      })
      await this.options.telegramClient.sendMessage(
        chatId,
        "Не удалось обработать сообщение. Попробуйте еще раз через минуту."
      )
    }
  }
}

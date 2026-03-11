import { BotRouter } from "./bot/router.js"
import { ConversationHandler } from "./bot/handlers/conversation-handler.js"
import { SubmitHandler } from "./bot/handlers/submit.js"
import { InMemorySessionStore } from "./bot/session/in-memory-session-store.js"
import { TelegramClient } from "./bot/telegram-client.js"
import { CreateLeadUseCase } from "./application/use-cases/create-lead.js"
import { loadConfig, safeConfigSnapshot } from "./config/env.js"
import { Logger } from "./config/logger.js"
import { LeadValidator } from "./domain/lead-validator.js"
import { GoogleSheetsLeadRepository } from "./integrations/google-sheets/google-sheets-lead-repository.js"

async function start(): Promise<void> {
  const config = loadConfig()
  const logger = new Logger(config.logLevel)

  logger.info("[main] Starting telegram-bot service", {
    config: safeConfigSnapshot(config)
  })

  const telegramClient = new TelegramClient({
    token: config.telegramToken,
    timeoutSeconds: config.telegramPollTimeoutSeconds,
    logger
  })

  const validator = new LeadValidator(logger)
  const repository = new GoogleSheetsLeadRepository({
    sheetId: config.googleSheetsId,
    range: config.googleSheetsRange,
    serviceAccountJson: config.googleServiceAccountJson,
    logger
  })
  const useCase = new CreateLeadUseCase({ validator, repository, logger })
  const submitHandler = new SubmitHandler({ useCase, logger })
  const conversationHandler = new ConversationHandler({
    sessionStore: new InMemorySessionStore(),
    submitHandler,
    logger,
    maxOffscriptRetries: config.maxOffscriptRetries
  })

  const router = new BotRouter({
    telegramClient,
    logger,
    messageProcessor: conversationHandler
  })

  let offset = 0
  while (true) {
    try {
      logger.debug("[main] Polling telegram updates", { offset })
      const updates = await telegramClient.getUpdates(offset)
      for (const update of updates) {
        await router.routeUpdate(update)
        offset = Math.max(offset, update.update_id + 1)
      }
    } catch (error) {
      logger.error("[main] Polling iteration failed", {
        error: error instanceof Error ? error.message : "unknown"
      })
      await new Promise((resolve) => setTimeout(resolve, 1500))
    }
  }
}

start().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : "unknown"
  console.error(JSON.stringify({ ts: new Date().toISOString(), level: "error", message }))
  process.exit(1)
})

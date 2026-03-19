import { describe, expect, it } from "vitest"
import { ConversationHandler } from "../../src/bot/handlers/conversation-handler.js"
import { InMemorySessionStore } from "../../src/bot/session/in-memory-session-store.js"
import { Logger } from "../../src/config/logger.js"

describe("ConversationHandler", () => {
  it("walks through dialog steps and submits", async () => {
    const handler = new ConversationHandler({
      sessionStore: new InMemorySessionStore(),
      submitHandler: {
        async submit() {
          return { ok: true, message: "saved" }
        }
      } as never,
      logger: new Logger("error"),
      maxOffscriptRetries: 2
    })

    const start = await handler.processMessage({ chatId: 1, text: "/start" })
    const contact = await handler.processMessage({ chatId: 1, text: "Иван" })
    const req = await handler.processMessage({ chatId: 1, text: "+79990001122" })
    const confirm = await handler.processMessage({
      chatId: 1,
      text: "Нужна помощь с подбором тарифа"
    })
    const saved = await handler.processMessage({ chatId: 1, text: "да" })

    expect(start).toContain("Как вас зовут")
    expect(contact).toContain("Укажите контакт")
    expect(req).toContain("Опишите")
    expect(confirm).toContain("Подтвердите отправку")
    expect(saved).toContain("Спасибо")
  })
})

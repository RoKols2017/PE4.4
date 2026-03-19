import type { LeadInput } from "../../../../shared/domain/lead.js"

export type DialogStep = "name" | "contact" | "request" | "confirm"

export type ConversationSession = {
  chatId: number
  step: DialogStep
  draft: Partial<LeadInput>
  offScriptRetries: number
  updatedAt: number
}

export class InMemorySessionStore {
  private readonly sessions = new Map<number, ConversationSession>()

  get(chatId: number): ConversationSession {
    const existing = this.sessions.get(chatId)
    if (existing) {
      return existing
    }

    const created: ConversationSession = {
      chatId,
      step: "name",
      draft: { source: "telegram_bot" },
      offScriptRetries: 0,
      updatedAt: Date.now()
    }
    this.sessions.set(chatId, created)
    return created
  }

  save(session: ConversationSession): void {
    this.sessions.set(session.chatId, { ...session, updatedAt: Date.now() })
  }

  reset(chatId: number): ConversationSession {
    const fresh: ConversationSession = {
      chatId,
      step: "name",
      draft: { source: "telegram_bot" },
      offScriptRetries: 0,
      updatedAt: Date.now()
    }
    this.sessions.set(chatId, fresh)
    return fresh
  }
}

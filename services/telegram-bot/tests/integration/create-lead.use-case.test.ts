import { describe, expect, it } from "vitest"
import { CreateLeadUseCase } from "../../src/application/use-cases/create-lead.js"
import { Logger } from "../../src/config/logger.js"
import { LeadValidator } from "../../src/domain/lead-validator.js"

describe("CreateLeadUseCase integration", () => {
  it("returns leadId when repository succeeds", async () => {
    const useCase = new CreateLeadUseCase({
      validator: new LeadValidator(new Logger("error")),
      repository: {
        async appendLead() {
          return { leadId: "lead-123" }
        }
      },
      logger: new Logger("debug")
    })

    const result = await useCase.execute({
      name: "Ivan",
      telegram_username: "ivan_user",
      request: "Нужна консультация",
      source: "telegram_bot"
    })

    expect(result).toEqual({ ok: true, leadId: "lead-123" })
  })

  it("returns storage_error when repository throws", async () => {
    const useCase = new CreateLeadUseCase({
      validator: new LeadValidator(new Logger("error")),
      repository: {
        async appendLead() {
          throw new Error("google error")
        }
      },
      logger: new Logger("debug")
    })

    const result = await useCase.execute({
      name: "Ivan",
      phone: "+79991234567",
      request: "Нужна консультация",
      source: "telegram_bot"
    })

    expect(result).toEqual({ ok: false, reason: "storage_error" })
  })
})

import type { Logger } from "../../config/logger.js"
import type { LeadInput } from "../../../../shared/domain/lead.js"
import { LeadValidator } from "../../domain/lead-validator.js"
import type { LeadRepository } from "../ports/lead-repository.js"

export type CreateLeadResult =
  | { ok: true; leadId: string }
  | { ok: false; reason: string }

type CreateLeadUseCaseOptions = {
  validator: LeadValidator
  repository: LeadRepository
  logger: Logger
}

export class CreateLeadUseCase {
  constructor(private readonly options: CreateLeadUseCaseOptions) {}

  async execute(input: LeadInput): Promise<CreateLeadResult> {
    this.options.logger.debug("[CreateLeadUseCase.execute] Enter", {
      source: input.source,
      hasName: Boolean(input.name),
      hasRequest: Boolean(input.request)
    })

    const validated = this.options.validator.validate(input)
    if (!validated.ok) {
      this.options.logger.warn("[CreateLeadUseCase.execute] Validation failed", {
        issues: validated.issues.map((issue) => issue.code)
      })
      return {
        ok: false,
        reason: validated.issues.map((issue) => issue.message).join("; ")
      }
    }

    try {
      const persisted = await this.options.repository.appendLead(validated.value)
      this.options.logger.info("[CreateLeadUseCase.execute] Lead persisted", {
        leadId: persisted.leadId
      })
      return { ok: true, leadId: persisted.leadId }
    } catch (error) {
      this.options.logger.error("[CreateLeadUseCase.execute] Persistence failed", {
        error: error instanceof Error ? error.message : "unknown"
      })
      return { ok: false, reason: "storage_error" }
    }
  }
}

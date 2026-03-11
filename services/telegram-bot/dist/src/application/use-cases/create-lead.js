export class CreateLeadUseCase {
    options;
    constructor(options) {
        this.options = options;
    }
    async execute(input) {
        this.options.logger.debug("[CreateLeadUseCase.execute] Enter", {
            source: input.source,
            hasName: Boolean(input.name),
            hasRequest: Boolean(input.request)
        });
        const validated = this.options.validator.validate(input);
        if (!validated.ok) {
            this.options.logger.warn("[CreateLeadUseCase.execute] Validation failed", {
                issues: validated.issues.map((issue) => issue.code)
            });
            return {
                ok: false,
                reason: validated.issues.map((issue) => issue.message).join("; ")
            };
        }
        try {
            const persisted = await this.options.repository.appendLead(validated.value);
            this.options.logger.info("[CreateLeadUseCase.execute] Lead persisted", {
                leadId: persisted.leadId
            });
            return { ok: true, leadId: persisted.leadId };
        }
        catch (error) {
            this.options.logger.error("[CreateLeadUseCase.execute] Persistence failed", {
                error: error instanceof Error ? error.message : "unknown"
            });
            return { ok: false, reason: "storage_error" };
        }
    }
}

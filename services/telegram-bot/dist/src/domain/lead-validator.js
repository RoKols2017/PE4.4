import { validateLead } from "../../../shared/domain/lead.js";
export class LeadValidator {
    logger;
    constructor(logger) {
        this.logger = logger;
    }
    validate(input) {
        this.logger.debug("[LeadValidator.validate] Validating lead", {
            source: input.source,
            hasName: Boolean(input.name),
            hasPhone: Boolean(input.phone),
            hasTelegram: Boolean(input.telegram_username)
        });
        const result = validateLead(input);
        if (result.ok) {
            this.logger.info("[LeadValidator.validate] Lead accepted", {
                source: result.value.source,
                hasPhone: Boolean(result.value.phone),
                hasTelegram: Boolean(result.value.telegram_username)
            });
            return result;
        }
        this.logger.warn("[LeadValidator.validate] Lead rejected", {
            issueCodes: result.issues.map((issue) => issue.code)
        });
        return result;
    }
}

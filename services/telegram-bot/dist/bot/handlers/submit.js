export class SubmitHandler {
    options;
    constructor(options) {
        this.options = options;
    }
    async submit(leadDraft) {
        this.options.logger.debug("[SubmitHandler.submit] Enter", {
            hasName: Boolean(leadDraft.name),
            hasContact: Boolean(leadDraft.phone || leadDraft.telegram_username)
        });
        const input = {
            name: leadDraft.name ?? "",
            phone: leadDraft.phone,
            telegram_username: leadDraft.telegram_username,
            request: leadDraft.request ?? "",
            source: "telegram_bot"
        };
        const result = await this.options.useCase.execute(input);
        if (!result.ok) {
            this.options.logger.warn("[SubmitHandler.submit] Submission rejected", {
                reason: result.reason
            });
            return {
                ok: false,
                message: "Не удалось сохранить заявку. Проверьте данные и попробуйте снова."
            };
        }
        this.options.logger.info("[SubmitHandler.submit] Submission completed", {
            leadId: result.leadId
        });
        return {
            ok: true,
            message: `Спасибо! Ваша заявка принята. Номер: ${result.leadId}`
        };
    }
}

export class TelegramClient {
    options;
    baseUrl;
    constructor(options) {
        this.options = options;
        this.baseUrl = `https://api.telegram.org/bot${options.token}`;
    }
    async getUpdates(offset) {
        this.options.logger.debug("[TelegramClient.getUpdates] Fetching updates", {
            offset,
            timeoutSeconds: this.options.timeoutSeconds
        });
        const response = await fetch(`${this.baseUrl}/getUpdates`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                timeout: this.options.timeoutSeconds,
                offset
            })
        });
        if (!response.ok) {
            this.options.logger.error("[TelegramClient.getUpdates] HTTP error", {
                status: response.status
            });
            throw new Error(`Telegram getUpdates failed with status ${response.status}`);
        }
        const body = (await response.json());
        this.options.logger.debug("[TelegramClient.getUpdates] Received updates", {
            count: body.result.length
        });
        return body.result;
    }
    async sendMessage(chatId, text) {
        this.options.logger.debug("[TelegramClient.sendMessage] Sending message", {
            chatId,
            preview: text.slice(0, 80)
        });
        const response = await fetch(`${this.baseUrl}/sendMessage`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                chat_id: chatId,
                text
            })
        });
        if (!response.ok) {
            this.options.logger.error("[TelegramClient.sendMessage] HTTP error", {
                status: response.status,
                chatId
            });
            throw new Error(`Telegram sendMessage failed with status ${response.status}`);
        }
        this.options.logger.info("[TelegramClient.sendMessage] Message sent", { chatId });
    }
}

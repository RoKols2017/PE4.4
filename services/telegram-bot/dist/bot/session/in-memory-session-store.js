export class InMemorySessionStore {
    sessions = new Map();
    get(chatId) {
        const existing = this.sessions.get(chatId);
        if (existing) {
            return existing;
        }
        const created = {
            chatId,
            step: "name",
            draft: { source: "telegram_bot" },
            offScriptRetries: 0,
            updatedAt: Date.now()
        };
        this.sessions.set(chatId, created);
        return created;
    }
    save(session) {
        this.sessions.set(session.chatId, { ...session, updatedAt: Date.now() });
    }
    reset(chatId) {
        const fresh = {
            chatId,
            step: "name",
            draft: { source: "telegram_bot" },
            offScriptRetries: 0,
            updatedAt: Date.now()
        };
        this.sessions.set(chatId, fresh);
        return fresh;
    }
}

import { isOffScriptMessage, sanitizeUserText } from "../../application/policies/assistant-policy.js";
import { DialogMessages } from "../messages/dialog-messages.js";
const STEP_ORDER = ["name", "contact", "request", "confirm"];
export class ConversationHandler {
    options;
    constructor(options) {
        this.options = options;
    }
    async processMessage(input) {
        const text = sanitizeUserText(input.text);
        const session = this.options.sessionStore.get(input.chatId);
        this.options.logger.debug("[ConversationHandler.processMessage] Enter", {
            chatId: input.chatId,
            step: session.step,
            textPreview: text.slice(0, 80)
        });
        if (text === "/start") {
            this.options.logger.info("[ConversationHandler.processMessage] Restart requested", {
                chatId: input.chatId
            });
            const reset = this.options.sessionStore.reset(input.chatId);
            this.bumpStep(reset, "name");
            return `${DialogMessages.greeting}\n\n${DialogMessages.askName}`;
        }
        if (isOffScriptMessage(text)) {
            session.offScriptRetries += 1;
            this.options.sessionStore.save(session);
            const level = session.offScriptRetries > this.options.maxOffscriptRetries ? "warn" : "info";
            this.options.logger[level]("[ConversationHandler.processMessage] Off-script input", {
                chatId: input.chatId,
                offScriptRetries: session.offScriptRetries
            });
            if (session.offScriptRetries > this.options.maxOffscriptRetries) {
                this.options.logger.warn("[ConversationHandler.processMessage] Repeated off-script input", {
                    chatId: input.chatId
                });
            }
            return `${DialogMessages.fallback}\n\n${this.promptFor(session.step)}`;
        }
        session.offScriptRetries = 0;
        switch (session.step) {
            case "name": {
                session.draft.name = text;
                this.bumpStep(session, "contact");
                this.options.sessionStore.save(session);
                this.options.logger.info("[ConversationHandler.processMessage] Step completed", {
                    chatId: input.chatId,
                    completed: "name",
                    next: "contact"
                });
                return DialogMessages.askContact;
            }
            case "contact": {
                if (!this.tryAssignContact(session, text, input.username)) {
                    this.options.logger.warn("[ConversationHandler.processMessage] Invalid contact", {
                        chatId: input.chatId
                    });
                    return DialogMessages.invalidContact;
                }
                this.bumpStep(session, "request");
                this.options.sessionStore.save(session);
                this.options.logger.info("[ConversationHandler.processMessage] Step completed", {
                    chatId: input.chatId,
                    completed: "contact",
                    next: "request"
                });
                return DialogMessages.askRequest;
            }
            case "request": {
                session.draft.request = text;
                this.bumpStep(session, "confirm");
                this.options.sessionStore.save(session);
                this.options.logger.info("[ConversationHandler.processMessage] Step completed", {
                    chatId: input.chatId,
                    completed: "request",
                    next: "confirm"
                });
                return this.buildConfirmation(session);
            }
            case "confirm": {
                if (text.toLowerCase() === "нет") {
                    this.options.sessionStore.reset(input.chatId);
                    this.options.logger.info("[ConversationHandler.processMessage] Submission cancelled", {
                        chatId: input.chatId
                    });
                    return DialogMessages.restart;
                }
                if (text.toLowerCase() !== "да") {
                    this.options.logger.warn("[ConversationHandler.processMessage] Unknown confirm response", {
                        chatId: input.chatId,
                        value: text
                    });
                    return DialogMessages.unknown;
                }
                const submitResult = await this.options.submitHandler.submit(session.draft);
                this.options.sessionStore.reset(input.chatId);
                if (!submitResult.ok) {
                    this.options.logger.error("[ConversationHandler.processMessage] Submit failed", {
                        chatId: input.chatId
                    });
                    return submitResult.message;
                }
                this.options.logger.info("[ConversationHandler.processMessage] Submit success", {
                    chatId: input.chatId
                });
                return `${DialogMessages.saved}\n${submitResult.message}`;
            }
            default: {
                this.options.logger.warn("[ConversationHandler.processMessage] Invalid state, resetting", {
                    chatId: input.chatId,
                    step: session.step
                });
                this.options.sessionStore.reset(input.chatId);
                return `${DialogMessages.greeting}\n\n${DialogMessages.askName}`;
            }
        }
    }
    tryAssignContact(session, text, usernameFromMessage) {
        if (/^\+?[0-9]{10,15}$/.test(text.replace(/\s+/g, ""))) {
            session.draft.phone = text.replace(/\s+/g, "");
            return true;
        }
        const telegram = text.replace(/^@+/, "");
        if (/^[a-zA-Z0-9_]{5,32}$/.test(telegram)) {
            session.draft.telegram_username = telegram;
            return true;
        }
        if (usernameFromMessage && /^[a-zA-Z0-9_]{5,32}$/.test(usernameFromMessage)) {
            session.draft.telegram_username = usernameFromMessage;
            return true;
        }
        return false;
    }
    buildConfirmation(session) {
        const contact = session.draft.phone
            ? `Телефон: ${session.draft.phone}`
            : `Telegram: @${session.draft.telegram_username}`;
        return [
            "Проверьте данные заявки:",
            `Имя: ${session.draft.name}`,
            contact,
            `Запрос: ${session.draft.request}`,
            "",
            DialogMessages.askConfirmation
        ].join("\n");
    }
    promptFor(step) {
        if (step === "name") {
            return DialogMessages.askName;
        }
        if (step === "contact") {
            return DialogMessages.askContact;
        }
        if (step === "request") {
            return DialogMessages.askRequest;
        }
        return DialogMessages.askConfirmation;
    }
    bumpStep(session, next) {
        const fromIndex = STEP_ORDER.indexOf(session.step);
        const toIndex = STEP_ORDER.indexOf(next);
        this.options.logger.debug("[ConversationHandler.bumpStep] State transition", {
            chatId: session.chatId,
            from: session.step,
            to: next,
            isForward: toIndex >= fromIndex
        });
        session.step = next;
    }
}

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.validateLead = validateLead;
const SOURCES = new Set(["telegram_bot", "website_assistant", "web_form"]);
function normalizeText(value) {
    return value.trim().replace(/\s+/g, " ");
}
function normalizePhone(value) {
    return value.trim().replace(/\s+/g, "");
}
function normalizeTelegram(value) {
    return value.trim().replace(/^@+/, "");
}
function validateLead(input) {
    const issues = [];
    const name = normalizeText(input.name);
    const request = normalizeText(input.request);
    const telegram = input.telegram_username ? normalizeTelegram(input.telegram_username) : "";
    const phone = input.phone ? normalizePhone(input.phone) : "";
    if (name.length < 2) {
        issues.push({
            code: "name_too_short",
            message: "Name must contain at least 2 characters"
        });
    }
    if (request.length < 5) {
        issues.push({
            code: "request_too_short",
            message: "Request must contain at least 5 characters"
        });
    }
    if (!telegram && !phone) {
        issues.push({
            code: "contact_required",
            message: "At least one contact is required: telegram_username or phone"
        });
    }
    if (phone && !/^\+?[0-9]{10,15}$/.test(phone)) {
        issues.push({
            code: "phone_invalid",
            message: "Phone must contain 10 to 15 digits and optional leading +"
        });
    }
    if (telegram && !/^[a-zA-Z0-9_]{5,32}$/.test(telegram)) {
        issues.push({
            code: "telegram_invalid",
            message: "Telegram username must be 5-32 characters using letters, digits, and underscores"
        });
    }
    if (!SOURCES.has(input.source)) {
        issues.push({
            code: "source_invalid",
            message: "Source must be telegram_bot, website_assistant, or web_form"
        });
    }
    if (issues.length > 0) {
        return { ok: false, issues };
    }
    return {
        ok: true,
        value: {
            name,
            request,
            source: input.source,
            telegram_username: telegram || undefined,
            phone: phone || undefined,
            created_at: new Date().toISOString()
        }
    };
}

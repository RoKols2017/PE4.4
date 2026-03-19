import { describe, expect, it } from "vitest";
import { Logger } from "../../src/config/logger.js";
import { LeadValidator } from "../../src/domain/lead-validator.js";
describe("LeadValidator", () => {
    const validator = new LeadValidator(new Logger("error"));
    it("accepts valid lead with phone", () => {
        const result = validator.validate({
            name: "Alice",
            phone: "+79991234567",
            request: "Нужна консультация по продукту",
            source: "telegram_bot"
        });
        expect(result.ok).toBe(true);
    });
    it("rejects lead without contacts", () => {
        const result = validator.validate({
            name: "Alice",
            request: "Хочу детали",
            source: "telegram_bot"
        });
        expect(result.ok).toBe(false);
        if (!result.ok) {
            expect(result.issues.map((issue) => issue.code)).toContain("contact_required");
        }
    });
});

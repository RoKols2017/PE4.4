import { google } from "googleapis";
function parseServiceAccount(raw) {
    const parsed = JSON.parse(raw);
    if (!parsed.client_email || !parsed.private_key) {
        throw new Error("GOOGLE_SERVICE_ACCOUNT_JSON must include client_email and private_key");
    }
    return {
        client_email: parsed.client_email,
        private_key: parsed.private_key
    };
}
export class GoogleSheetsLeadRepository {
    options;
    sheets;
    constructor(options) {
        this.options = options;
        const account = parseServiceAccount(options.serviceAccountJson);
        const auth = new google.auth.JWT({
            email: account.client_email,
            key: account.private_key,
            scopes: ["https://www.googleapis.com/auth/spreadsheets"]
        });
        this.sheets = google.sheets({ version: "v4", auth });
    }
    async appendLead(lead) {
        const leadId = crypto.randomUUID();
        const values = [
            leadId,
            lead.created_at,
            lead.source,
            lead.name,
            lead.telegram_username ?? "",
            lead.phone ?? "",
            lead.request
        ];
        this.options.logger.debug("[GoogleSheetsLeadRepository.appendLead] Appending row", {
            sheetId: this.options.sheetId,
            range: this.options.range,
            leadId
        });
        let attempt = 0;
        while (attempt < 3) {
            attempt += 1;
            try {
                const result = await this.sheets.spreadsheets.values.append({
                    spreadsheetId: this.options.sheetId,
                    range: this.options.range,
                    valueInputOption: "RAW",
                    requestBody: {
                        values: [values]
                    }
                });
                this.options.logger.info("[GoogleSheetsLeadRepository.appendLead] Lead appended", {
                    leadId,
                    updatedRange: result.data.updates?.updatedRange
                });
                return { leadId };
            }
            catch (error) {
                const message = error instanceof Error ? error.message : "unknown";
                if (attempt < 3) {
                    this.options.logger.warn("[GoogleSheetsLeadRepository.appendLead] Retry append", {
                        leadId,
                        attempt,
                        error: message
                    });
                    await new Promise((resolve) => setTimeout(resolve, attempt * 400));
                    continue;
                }
                this.options.logger.error("[GoogleSheetsLeadRepository.appendLead] Failed to append lead", {
                    leadId,
                    attempts: attempt,
                    error: message
                });
                throw error;
            }
        }
        throw new Error("Unexpected append loop exit");
    }
}

export function isOffScriptMessage(text) {
    const normalized = text.toLowerCase();
    const offScriptSignals = ["прогноз", "гарант", "придум", "выдум", "100%"];
    return offScriptSignals.some((signal) => normalized.includes(signal));
}
export function sanitizeUserText(text) {
    return text.trim().replace(/\s+/g, " ");
}

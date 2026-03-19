export function isOffScriptMessage(text: string): boolean {
  const normalized = text.toLowerCase()
  const offScriptSignals = ["прогноз", "гарант", "придум", "выдум", "100%"]
  return offScriptSignals.some((signal) => normalized.includes(signal))
}

export function sanitizeUserText(text: string): string {
  return text.trim().replace(/\s+/g, " ")
}

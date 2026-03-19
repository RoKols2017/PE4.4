import dotenv from "dotenv"

dotenv.config()

export type LogLevel = "debug" | "info" | "warn" | "error"

export type BotConfig = {
  logLevel: LogLevel
  telegramToken: string
  telegramPollTimeoutSeconds: number
  maxOffscriptRetries: number
  googleSheetsId: string
  googleSheetsRange: string
  googleServiceAccountJson: string
}

const VALID_LOG_LEVELS: readonly LogLevel[] = ["debug", "info", "warn", "error"]

function readEnv(name: string, required: boolean): string {
  const value = process.env[name]?.trim() ?? ""
  if (!value && required) {
    throw new Error(`[config] Missing required environment variable: ${name}`)
  }
  return value
}

function parsePositiveInt(name: string, fallback: number): number {
  const value = process.env[name]
  if (!value) {
    return fallback
  }

  const parsed = Number(value)
  if (!Number.isInteger(parsed) || parsed <= 0) {
    throw new Error(`[config] ${name} must be a positive integer, got: ${value}`)
  }

  return parsed
}

function parseLogLevel(value: string): LogLevel {
  const normalized = (value || "info").toLowerCase() as LogLevel
  if (!VALID_LOG_LEVELS.includes(normalized)) {
    throw new Error(`[config] LOG_LEVEL must be one of: ${VALID_LOG_LEVELS.join(", ")}`)
  }
  return normalized
}

export function loadConfig(): BotConfig {
  return {
    logLevel: parseLogLevel(readEnv("LOG_LEVEL", false)),
    telegramToken: readEnv("TELEGRAM_BOT_TOKEN", true),
    telegramPollTimeoutSeconds: parsePositiveInt("TELEGRAM_POLL_TIMEOUT_SECONDS", 25),
    maxOffscriptRetries: parsePositiveInt("MAX_OFFSCRIPT_RETRIES", 2),
    googleSheetsId: readEnv("GOOGLE_SHEETS_ID", true),
    googleSheetsRange: readEnv("GOOGLE_SHEETS_RANGE", false) || "Leads!A:G",
    googleServiceAccountJson: readEnv("GOOGLE_SERVICE_ACCOUNT_JSON", true)
  }
}

export function safeConfigSnapshot(config: BotConfig): Record<string, string | number> {
  return {
    logLevel: config.logLevel,
    telegramPollTimeoutSeconds: config.telegramPollTimeoutSeconds,
    maxOffscriptRetries: config.maxOffscriptRetries,
    googleSheetsId: config.googleSheetsId,
    googleSheetsRange: config.googleSheetsRange
  }
}

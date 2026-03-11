import type { LogLevel } from "./env.js"

const ORDER: Record<LogLevel, number> = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40
}

export type LogContext = Record<string, unknown>

export class Logger {
  constructor(private readonly level: LogLevel) {}

  debug(message: string, context: LogContext = {}): void {
    this.log("debug", message, context)
  }

  info(message: string, context: LogContext = {}): void {
    this.log("info", message, context)
  }

  warn(message: string, context: LogContext = {}): void {
    this.log("warn", message, context)
  }

  error(message: string, context: LogContext = {}): void {
    this.log("error", message, context)
  }

  child(baseContext: LogContext): Logger {
    const parent = this
    return new (class extends Logger {
      constructor() {
        super(parent.level)
      }

      override debug(message: string, context: LogContext = {}): void {
        parent.debug(message, { ...baseContext, ...context })
      }

      override info(message: string, context: LogContext = {}): void {
        parent.info(message, { ...baseContext, ...context })
      }

      override warn(message: string, context: LogContext = {}): void {
        parent.warn(message, { ...baseContext, ...context })
      }

      override error(message: string, context: LogContext = {}): void {
        parent.error(message, { ...baseContext, ...context })
      }
    })()
  }

  private log(level: LogLevel, message: string, context: LogContext): void {
    if (ORDER[level] < ORDER[this.level]) {
      return
    }

    const payload = {
      ts: new Date().toISOString(),
      level,
      message,
      ...context
    }

    const line = JSON.stringify(payload)
    if (level === "error") {
      console.error(line)
      return
    }

    if (level === "warn") {
      console.warn(line)
      return
    }

    console.log(line)
  }
}

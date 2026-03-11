const ORDER = {
    debug: 10,
    info: 20,
    warn: 30,
    error: 40
};
export class Logger {
    level;
    constructor(level) {
        this.level = level;
    }
    debug(message, context = {}) {
        this.log("debug", message, context);
    }
    info(message, context = {}) {
        this.log("info", message, context);
    }
    warn(message, context = {}) {
        this.log("warn", message, context);
    }
    error(message, context = {}) {
        this.log("error", message, context);
    }
    child(baseContext) {
        const parent = this;
        return new (class extends Logger {
            constructor() {
                super(parent.level);
            }
            debug(message, context = {}) {
                parent.debug(message, { ...baseContext, ...context });
            }
            info(message, context = {}) {
                parent.info(message, { ...baseContext, ...context });
            }
            warn(message, context = {}) {
                parent.warn(message, { ...baseContext, ...context });
            }
            error(message, context = {}) {
                parent.error(message, { ...baseContext, ...context });
            }
        })();
    }
    log(level, message, context) {
        if (ORDER[level] < ORDER[this.level]) {
            return;
        }
        const payload = {
            ts: new Date().toISOString(),
            level,
            message,
            ...context
        };
        const line = JSON.stringify(payload);
        if (level === "error") {
            console.error(line);
            return;
        }
        if (level === "warn") {
            console.warn(line);
            return;
        }
        console.log(line);
    }
}

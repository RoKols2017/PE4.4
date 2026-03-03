const toggleBtn = document.getElementById("chat-toggle")
const widget = document.getElementById("chat-widget")
const closeBtn = document.getElementById("chat-close")
const form = document.getElementById("chat-form")
const input = document.getElementById("chat-input")
const messages = document.getElementById("chat-messages")
const typing = document.getElementById("typing-indicator")

const sessionStorageKey = "web-assistant-session-id"
let sessionId = localStorage.getItem(sessionStorageKey) || ""
let started = false

function randomSessionId() {
  if (window.crypto && window.crypto.randomUUID) {
    return window.crypto.randomUUID()
  }
  return `sid-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

if (!sessionId) {
  sessionId = randomSessionId()
  localStorage.setItem(sessionStorageKey, sessionId)
}

function addMessage(role, text) {
  const el = document.createElement("div")
  el.className = `msg ${role}`
  el.textContent = text
  messages.appendChild(el)
  messages.scrollTop = messages.scrollHeight
}

async function logClient(event, details = {}) {
  try {
    await fetch("/api/client-log", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Session-Id": sessionId },
      body: JSON.stringify({ event, details })
    })
  } catch (_error) {
    // No-op
  }
}

async function startChat() {
  typing.classList.remove("hidden")
  await logClient("open")
  const response = await fetch("/api/chat/start", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Session-Id": sessionId }
  })
  const data = await response.json()
  typing.classList.add("hidden")
  addMessage("assistant", data.assistant_message)
  started = true
}

async function sendMessage(message) {
  typing.classList.remove("hidden")
  await logClient("send", { length: message.length })
  const response = await fetch("/api/chat/message", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Session-Id": sessionId },
    body: JSON.stringify({ message })
  })
  const data = await response.json()
  typing.classList.add("hidden")
  if (!response.ok) {
    addMessage("assistant", "Ошибка отправки сообщения. Попробуйте еще раз.")
    await logClient("render_error", { status: response.status, error: data.error || "unknown" })
    return
  }
  addMessage("assistant", data.assistant_message)
}

toggleBtn.addEventListener("click", async () => {
  widget.classList.remove("hidden")
  if (!started) {
    await startChat()
  }
})

closeBtn.addEventListener("click", async () => {
  widget.classList.add("hidden")
  await logClient("close")
})

messages.addEventListener("scroll", async () => {
  await logClient("scroll", {
    top: messages.scrollTop,
    max: messages.scrollHeight
  })
})

form.addEventListener("submit", async (event) => {
  event.preventDefault()
  const text = input.value.trim()
  if (!text) {
    return
  }

  addMessage("user", text)
  input.value = ""
  await sendMessage(text)
})

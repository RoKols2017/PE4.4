const root = document.querySelector(".leads-page")
const sourceFilter = document.getElementById("source-filter")
const refreshBtn = document.getElementById("refresh-btn")
const leadsBody = document.getElementById("leads-body")
const leadsError = document.getElementById("leads-error")
const leadsEmpty = document.getElementById("leads-empty")
const prevBtn = document.getElementById("prev-btn")
const nextBtn = document.getElementById("next-btn")
const pageLabel = document.getElementById("page-label")

const leadsToken = root?.dataset.leadsToken || ""
const pageSize = 20
let offset = 0
let total = 0

function randomSessionId() {
  if (window.crypto && window.crypto.randomUUID) {
    return window.crypto.randomUUID()
  }
  return `leads-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

const sessionId = randomSessionId()

async function logClient(event, details = {}) {
  try {
    await fetch("/api/client-log", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Session-Id": sessionId },
      body: JSON.stringify({ event, details })
    })
  } catch (_error) {
    // no-op
  }
}

function setError(text) {
  if (!text) {
    leadsError.classList.add("hidden")
    leadsError.textContent = ""
    return
  }
  leadsError.textContent = text
  leadsError.classList.remove("hidden")
}

function renderRows(items) {
  leadsBody.innerHTML = ""
  for (const item of items) {
    const row = document.createElement("tr")
    row.innerHTML = `
      <td>${item.created_at_utc}</td>
      <td>${item.source}</td>
      <td>${item.name || "-"}</td>
      <td>${item.phone || "-"}</td>
      <td>${item.email || "-"}</td>
      <td>${item.request || "-"}</td>
      <td>${item.status || "-"}</td>
    `
    leadsBody.appendChild(row)
  }
}

function refreshPagingLabel() {
  const pageNumber = Math.floor(offset / pageSize) + 1
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  pageLabel.textContent = `Страница ${pageNumber} из ${totalPages}`
  prevBtn.disabled = offset <= 0
  nextBtn.disabled = offset + pageSize >= total
}

async function loadLeads() {
  setError("")
  const source = sourceFilter.value
  const query = new URLSearchParams({ limit: String(pageSize), offset: String(offset) })
  if (source) {
    query.set("source", source)
  }

  await logClient("leads_fetch_start", { offset, source: source || "all" })
  const response = await fetch(`/api/leads?${query.toString()}`, {
    headers: { "X-Leads-View-Token": leadsToken, "X-Session-Id": sessionId }
  })
  const data = await response.json()

  if (!response.ok) {
    setError(`Ошибка загрузки лидов: ${data.error || response.status}`)
    leadsBody.innerHTML = ""
    leadsEmpty.classList.remove("hidden")
    await logClient("leads_fetch_error", { status: response.status, error: data.error || "unknown" })
    return
  }

  total = data.pagination.total
  renderRows(data.items)
  leadsEmpty.classList.toggle("hidden", data.items.length > 0)
  refreshPagingLabel()
  await logClient("leads_fetch_success", { count: data.items.length, total, offset, source: source || "all" })
}

refreshBtn.addEventListener("click", async () => {
  offset = 0
  await logClient("leads_refresh_clicked")
  await loadLeads()
})

sourceFilter.addEventListener("change", async () => {
  offset = 0
  await logClient("leads_filter_changed", { source: sourceFilter.value || "all" })
  await loadLeads()
})

prevBtn.addEventListener("click", async () => {
  if (offset === 0) {
    return
  }
  offset = Math.max(0, offset - pageSize)
  await logClient("leads_page_changed", { direction: "prev", offset })
  await loadLeads()
})

nextBtn.addEventListener("click", async () => {
  if (offset + pageSize >= total) {
    return
  }
  offset += pageSize
  await logClient("leads_page_changed", { direction: "next", offset })
  await loadLeads()
})

void logClient("leads_view_opened")
void loadLeads()

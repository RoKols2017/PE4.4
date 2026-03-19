import type { Lead } from "../../../../shared/domain/lead.js"

export type PersistedLead = {
  leadId: string
}

export interface LeadRepository {
  appendLead(lead: Lead): Promise<PersistedLead>
}

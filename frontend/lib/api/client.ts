/* eslint-disable @typescript-eslint/no-explicit-any */
import type {
  TargetSummary,
  SearchResult,
  DrugSummary,
  ScoreBreakdown,
  IndicationSummary,
  PlatformStats,
  EditingAssetSummary,
  EditingTargetGeneSummary,
  CompanySummary,
  ChatRequest,
  ChatResponse,
  ScorecardRequest,
  ScorecardResponse,
  EditingAssetExplainRequest,
  EditingAssetExplainResponse,
  AIEntities,
  AIHealthStatus,
  ComboSummary,
  ComboDetail,
  ComboLabelsResponse,
  TargetActivity,
  PatentSummary,
  PatentDetail,
  NewsSummary,
  NewsDetail,
  TrialSummary,
  TrialDetail,
  CalendarStats,
  ConferenceSummary,
  DateConfidence,
} from "./types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message)
    this.name = "ApiError"
  }
}

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new ApiError(response.status, errorText || `HTTP error ${response.status}`)
  }

  return response.json()
}

// Targets API (matches /epi/targets endpoints)
export const targetsApi = {
  list: async (params?: {
    target_class?: string
    family?: string
  }): Promise<TargetSummary[]> => {
    const searchParams = new URLSearchParams()
    if (params?.target_class) searchParams.set("target_class", params.target_class)
    if (params?.family) searchParams.set("family", params.family)

    const query = searchParams.toString()
    return fetchApi<TargetSummary[]>(`/epi/targets${query ? `?${query}` : ""}`)
  },

  get: async (targetId: string): Promise<any> => {
    return fetchApi<any>(`/epi/targets/${targetId}`)
  },
}

// Drugs API (matches /epi/drugs endpoints)
export const drugsApi = {
  list: async (params?: {
    target_id?: string
    indication_id?: string
    approved_only?: boolean
  }): Promise<DrugSummary[]> => {
    const searchParams = new URLSearchParams()
    if (params?.target_id) searchParams.set("target_id", params.target_id)
    if (params?.indication_id) searchParams.set("indication_id", params.indication_id)
    if (params?.approved_only) searchParams.set("approved_only", "true")

    const query = searchParams.toString()
    return fetchApi<DrugSummary[]>(`/epi/drugs${query ? `?${query}` : ""}`)
  },

  get: async (drugId: string): Promise<any> => {
    return fetchApi<any>(`/epi/drugs/${drugId}`)
  },

  getTargetActivities: async (drugId: string): Promise<TargetActivity[]> => {
    return fetchApi<TargetActivity[]>(`/epi/drugs/${drugId}/target-activities`)
  },
}

// Indications API
export const indicationsApi = {
  list: async (): Promise<IndicationSummary[]> => {
    return fetchApi<IndicationSummary[]>("/epi/indications")
  },

  get: async (indicationId: string): Promise<any> => {
    return fetchApi<any>(`/epi/indications/${indicationId}`)
  },
}

// Scores API
export const scoresApi = {
  list: async (params?: {
    min_total_score?: number
    min_bio_score?: number
  }): Promise<ScoreBreakdown[]> => {
    const searchParams = new URLSearchParams()
    if (params?.min_total_score) searchParams.set("min_total_score", String(params.min_total_score))
    if (params?.min_bio_score) searchParams.set("min_bio_score", String(params.min_bio_score))

    const query = searchParams.toString()
    return fetchApi<ScoreBreakdown[]>(`/epi/scores${query ? `?${query}` : ""}`)
  },
}

// Signatures API
export const signaturesApi = {
  get: async (name: string): Promise<any> => {
    return fetchApi<any>(`/epi/signatures/${name}`)
  },
}

// Search API
export const searchApi = {
  search: async (q: string): Promise<SearchResult[]> => {
    return fetchApi<SearchResult[]>(`/epi/search?q=${encodeURIComponent(q)}`)
  },
}

// Stats API
export const statsApi = {
  get: async (): Promise<PlatformStats> => {
    return fetchApi<PlatformStats>("/epi/stats")
  },
}

// Editing Assets API (matches /epi/editing-assets endpoints)
export const editingAssetsApi = {
  list: async (params?: {
    sponsor?: string
    dbd_type?: string
    effector_type?: string
    status?: string
    min_phase?: number
  }): Promise<EditingAssetSummary[]> => {
    const searchParams = new URLSearchParams()
    if (params?.sponsor) searchParams.set("sponsor", params.sponsor)
    if (params?.dbd_type) searchParams.set("dbd_type", params.dbd_type)
    if (params?.effector_type) searchParams.set("effector_type", params.effector_type)
    if (params?.status) searchParams.set("status", params.status)
    if (params?.min_phase !== undefined) searchParams.set("min_phase", String(params.min_phase))

    const query = searchParams.toString()
    return fetchApi<EditingAssetSummary[]>(`/epi/editing-assets${query ? `?${query}` : ""}`)
  },

  get: async (assetId: string): Promise<any> => {
    return fetchApi<any>(`/epi/editing-assets/${assetId}`)
  },
}

// Editing Target Genes API
export const editingTargetsApi = {
  list: async (params?: {
    category?: string
    editor_ready_only?: boolean
  }): Promise<EditingTargetGeneSummary[]> => {
    const searchParams = new URLSearchParams()
    if (params?.category) searchParams.set("category", params.category)
    if (params?.editor_ready_only) searchParams.set("editor_ready_only", "true")

    const query = searchParams.toString()
    return fetchApi<EditingTargetGeneSummary[]>(`/epi/editing-targets${query ? `?${query}` : ""}`)
  },

  get: async (symbol: string): Promise<any> => {
    return fetchApi<any>(`/epi/editing-targets/${symbol}`)
  },
}

// Companies API (matches /epi/companies endpoints)
export const companiesApi = {
  list: async (params?: {
    pure_play_only?: boolean
    min_epi_focus?: number
    has_ticker?: boolean
  }): Promise<CompanySummary[]> => {
    const searchParams = new URLSearchParams()
    if (params?.pure_play_only) searchParams.set("pure_play_only", "true")
    if (params?.min_epi_focus !== undefined) searchParams.set("min_epi_focus", String(params.min_epi_focus))
    if (params?.has_ticker !== undefined) searchParams.set("has_ticker", String(params.has_ticker))

    const query = searchParams.toString()
    return fetchApi<CompanySummary[]>(`/epi/companies${query ? `?${query}` : ""}`)
  },

  get: async (companyId: string): Promise<any> => {
    return fetchApi<any>(`/epi/companies/${companyId}`)
  },

  getByTicker: async (ticker: string): Promise<any> => {
    return fetchApi<any>(`/epi/companies/ticker/${ticker}`)
  },
}

// Combos API (matches /epi/combos endpoints)
export const combosApi = {
  list: async (params?: {
    combo_label?: string
    epi_drug_id?: string
    indication_id?: string
    partner_class?: string
    min_phase?: number
  }): Promise<ComboSummary[]> => {
    const searchParams = new URLSearchParams()
    if (params?.combo_label) searchParams.set("combo_label", params.combo_label)
    if (params?.epi_drug_id) searchParams.set("epi_drug_id", params.epi_drug_id)
    if (params?.indication_id) searchParams.set("indication_id", params.indication_id)
    if (params?.partner_class) searchParams.set("partner_class", params.partner_class)
    if (params?.min_phase !== undefined) searchParams.set("min_phase", String(params.min_phase))

    const query = searchParams.toString()
    return fetchApi<ComboSummary[]>(`/epi/combos${query ? `?${query}` : ""}`)
  },

  get: async (comboId: string): Promise<{ combo: ComboDetail; epi_drug: any; partner_drug: any; indication: any }> => {
    return fetchApi<{ combo: ComboDetail; epi_drug: any; partner_drug: any; indication: any }>(`/epi/combos/${comboId}`)
  },

  getLabels: async (): Promise<ComboLabelsResponse> => {
    return fetchApi<ComboLabelsResponse>("/epi/combos/labels")
  },

  getByDrug: async (drugId: string): Promise<ComboSummary[]> => {
    return fetchApi<ComboSummary[]>(`/epi/drugs/${drugId}/combos`)
  },
}

// Patents API (matches /epi/patents endpoints)
export const patentsApi = {
  list: async (params?: {
    category?: string
    assignee?: string
    target_symbol?: string
  }): Promise<PatentSummary[]> => {
    const searchParams = new URLSearchParams()
    if (params?.category) searchParams.set("category", params.category)
    if (params?.assignee) searchParams.set("assignee", params.assignee)
    if (params?.target_symbol) searchParams.set("target_symbol", params.target_symbol)

    const query = searchParams.toString()
    return fetchApi<PatentSummary[]>(`/epi/patents${query ? `?${query}` : ""}`)
  },

  get: async (patentId: string): Promise<PatentDetail> => {
    return fetchApi<PatentDetail>(`/epi/patents/${patentId}`)
  },

  getCategories: async (): Promise<{ category: string; count: number }[]> => {
    // Fetch all patents and count categories
    const patents = await fetchApi<PatentSummary[]>("/epi/patents")
    const categoryMap: Record<string, number> = {}
    patents.forEach(p => {
      const cat = p.category || "other"
      categoryMap[cat] = (categoryMap[cat] || 0) + 1
    })
    return Object.entries(categoryMap).map(([category, count]) => ({ category, count }))
  },
}

// News API (matches /epi/news endpoints)
export const newsApi = {
  list: async (params?: {
    category?: string
    source?: string
    limit?: number
  }): Promise<NewsSummary[]> => {
    const searchParams = new URLSearchParams()
    if (params?.category) searchParams.set("category", params.category)
    if (params?.source) searchParams.set("source", params.source)
    if (params?.limit) searchParams.set("limit", String(params.limit))

    const query = searchParams.toString()
    return fetchApi<NewsSummary[]>(`/epi/news${query ? `?${query}` : ""}`)
  },

  get: async (newsId: string): Promise<NewsDetail> => {
    return fetchApi<NewsDetail>(`/epi/news/${newsId}`)
  },
}

// AI Chat API (matches /ai/* endpoints)
export const aiApi = {
  chat: async (request: ChatRequest): Promise<ChatResponse> => {
    return fetchApi<ChatResponse>("/ai/chat", {
      method: "POST",
      body: JSON.stringify(request),
    })
  },

  explainScorecard: async (request: ScorecardRequest): Promise<ScorecardResponse> => {
    return fetchApi<ScorecardResponse>("/ai/explain-scorecard", {
      method: "POST",
      body: JSON.stringify(request),
    })
  },

  explainEditingAsset: async (request: EditingAssetExplainRequest): Promise<EditingAssetExplainResponse> => {
    return fetchApi<EditingAssetExplainResponse>("/ai/explain-editing-asset", {
      method: "POST",
      body: JSON.stringify(request),
    })
  },

  getEntities: async (): Promise<AIEntities> => {
    return fetchApi<AIEntities>("/ai/entities")
  },

  getHealth: async (): Promise<AIHealthStatus> => {
    return fetchApi<AIHealthStatus>("/ai/health")
  },
}

// Auth API (matches /auth/* endpoints)
export const authApi = {
  getProfile: async (token: string): Promise<any> => {
    return fetchApi<any>("/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
  },

  updateProfile: async (token: string, data: { full_name?: string; company_name?: string; job_title?: string }): Promise<any> => {
    return fetchApi<any>("/auth/me", {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify(data),
    })
  },

  getUsage: async (token: string): Promise<any> => {
    return fetchApi<any>("/auth/me/usage", {
      headers: { Authorization: `Bearer ${token}` },
    })
  },

  getTiers: async (): Promise<any[]> => {
    return fetchApi<any[]>("/auth/tiers")
  },

  checkFeatureAccess: async (token: string, feature: string): Promise<any> => {
    return fetchApi<any>(`/auth/me/can-access/${feature}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  },

  trackLogin: async (token: string): Promise<any> => {
    return fetchApi<any>("/auth/me/track-login", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    })
  },
}

// Payments API (matches /payments/* endpoints)
export const paymentsApi = {
  createCheckoutSession: async (token: string, tierId: string, billingPeriod: string = "monthly"): Promise<any> => {
    return fetchApi<any>("/payments/create-checkout-session", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ tier_id: tierId, billing_period: billingPeriod }),
    })
  },

  createPortalSession: async (token: string): Promise<any> => {
    return fetchApi<any>("/payments/create-portal-session", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({}),
    })
  },

  getSubscription: async (token: string): Promise<any> => {
    return fetchApi<any>("/payments/subscription", {
      headers: { Authorization: `Bearer ${token}` },
    })
  },

  getPaymentHistory: async (token: string, limit: number = 10): Promise<any[]> => {
    return fetchApi<any[]>(`/payments/history?limit=${limit}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  },
}

// Watchlist API (matches /watchlist/* endpoints)
export const watchlistApi = {
  getItems: async (token: string, entityType?: string): Promise<any[]> => {
    const query = entityType ? `?entity_type=${entityType}` : ""
    return fetchApi<any[]>(`/watchlist/${query}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  },

  addItem: async (token: string, item: {
    entity_type: string
    entity_id: string
    entity_name: string
    alert_on_phase_change?: boolean
    alert_on_status_change?: boolean
    alert_on_score_change?: boolean
    alert_on_news?: boolean
    alert_on_pdufa?: boolean
    notes?: string
  }): Promise<any> => {
    return fetchApi<any>("/watchlist/", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify(item),
    })
  },

  updateItem: async (token: string, watchlistId: string, updates: any): Promise<any> => {
    return fetchApi<any>(`/watchlist/${watchlistId}`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify(updates),
    })
  },

  removeItem: async (token: string, watchlistId: string): Promise<any> => {
    return fetchApi<any>(`/watchlist/${watchlistId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    })
  },

  getAlerts: async (token: string, status?: string, limit: number = 50): Promise<any[]> => {
    const params = new URLSearchParams()
    if (status) params.set("status", status)
    params.set("limit", String(limit))
    return fetchApi<any[]>(`/watchlist/alerts?${params.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  },

  getUnreadCount: async (token: string): Promise<{ unread_count: number }> => {
    return fetchApi<{ unread_count: number }>("/watchlist/alerts/unread/count", {
      headers: { Authorization: `Bearer ${token}` },
    })
  },

  markAlertRead: async (token: string, alertId: string): Promise<any> => {
    return fetchApi<any>(`/watchlist/alerts/${alertId}/read`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}` },
    })
  },

  dismissAlert: async (token: string, alertId: string): Promise<any> => {
    return fetchApi<any>(`/watchlist/alerts/${alertId}/dismiss`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}` },
    })
  },

  getNotificationPrefs: async (token: string): Promise<any> => {
    return fetchApi<any>("/watchlist/notifications/preferences", {
      headers: { Authorization: `Bearer ${token}` },
    })
  },

  updateNotificationPrefs: async (token: string, prefs: any): Promise<any> => {
    return fetchApi<any>("/watchlist/notifications/preferences", {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify(prefs),
    })
  },
}

// Exports API (matches /exports/* endpoints)
export const exportsApi = {
  exportExcel: async (token: string, request: {
    entity_type: string
    entity_ids?: string[]
    include_scores?: boolean
    include_trials?: boolean
    filename?: string
  }): Promise<Blob> => {
    const response = await fetch(`${API_BASE_URL}/exports/excel`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(request),
    })
    if (!response.ok) throw new ApiError(response.status, "Export failed")
    return response.blob()
  },

  exportCsv: async (token: string, request: {
    entity_type: string
    entity_ids?: string[]
    include_scores?: boolean
    filename?: string
  }): Promise<Blob> => {
    const response = await fetch(`${API_BASE_URL}/exports/csv`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(request),
    })
    if (!response.ok) throw new ApiError(response.status, "Export failed")
    return response.blob()
  },

  exportDealMemo: async (token: string, request: {
    drug_id: string
    indication_id?: string
    include_chemistry?: boolean
    include_trials?: boolean
    include_competitors?: boolean
  }): Promise<Blob> => {
    const response = await fetch(`${API_BASE_URL}/exports/deal-memo`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(request),
    })
    if (!response.ok) throw new ApiError(response.status, "Export failed")
    return response.blob()
  },
}

// Calendar API (matches /calendar/* endpoints)
export const calendarApi = {
  getTrials: async (params?: {
    phase?: string
    status?: string
    drug_id?: string
    date_confidence?: DateConfidence
    exclude_placeholders?: boolean
    limit?: number
    offset?: number
  }): Promise<TrialSummary[]> => {
    const searchParams = new URLSearchParams()
    if (params?.phase) searchParams.set("phase", params.phase)
    if (params?.status) searchParams.set("status", params.status)
    if (params?.drug_id) searchParams.set("drug_id", params.drug_id)
    if (params?.date_confidence) searchParams.set("date_confidence", params.date_confidence)
    if (params?.exclude_placeholders) searchParams.set("exclude_placeholders", "true")
    if (params?.limit) searchParams.set("limit", String(params.limit))
    if (params?.offset) searchParams.set("offset", String(params.offset))

    const query = searchParams.toString()
    return fetchApi<TrialSummary[]>(`/calendar/trials${query ? `?${query}` : ""}`)
  },

  getUpcomingTrials: async (params?: {
    days?: number
    phase_min?: number
    exclude_placeholders?: boolean
  }): Promise<TrialSummary[]> => {
    const searchParams = new URLSearchParams()
    if (params?.days) searchParams.set("days", String(params.days))
    if (params?.phase_min) searchParams.set("phase_min", String(params.phase_min))
    if (params?.exclude_placeholders) searchParams.set("exclude_placeholders", "true")

    const query = searchParams.toString()
    return fetchApi<TrialSummary[]>(`/calendar/trials/upcoming${query ? `?${query}` : ""}`)
  },

  getTrial: async (nctId: string): Promise<TrialDetail> => {
    return fetchApi<TrialDetail>(`/calendar/trials/${nctId}`)
  },

  getStats: async (): Promise<CalendarStats> => {
    return fetchApi<CalendarStats>("/calendar/stats")
  },

  getTrialsByDrug: async (drugId: string): Promise<TrialSummary[]> => {
    return fetchApi<TrialSummary[]>(`/calendar/drugs/${drugId}/trials`)
  },

  getConferences: async (year?: number): Promise<ConferenceSummary[]> => {
    const query = year ? `?year=${year}` : ""
    return fetchApi<ConferenceSummary[]>(`/calendar/conferences${query}`)
  },
}

// Export all APIs
export const api = {
  targets: targetsApi,
  drugs: drugsApi,
  indications: indicationsApi,
  scores: scoresApi,
  signatures: signaturesApi,
  search: searchApi,
  stats: statsApi,
  editingAssets: editingAssetsApi,
  editingTargets: editingTargetsApi,
  companies: companiesApi,
  combos: combosApi,
  patents: patentsApi,
  news: newsApi,
  ai: aiApi,
  calendar: calendarApi,
  auth: authApi,
  payments: paymentsApi,
  watchlist: watchlistApi,
  exports: exportsApi,
}

export { ApiError }

// ============ Backward-compatible function exports ============
// These match the old api.ts interface for components that haven't been updated

export async function fetchTargets() {
  return targetsApi.list()
}

export async function fetchDrugs(params?: { target_id?: string; indication_id?: string; approved_only?: boolean }) {
  return drugsApi.list({
    target_id: params?.target_id,
    indication_id: params?.indication_id,
    approved_only: params?.approved_only,
  })
}

export async function fetchDrugDetails(drugId: string) {
  return drugsApi.get(drugId)
}

export async function fetchSignature(name: string) {
  return signaturesApi.get(name)
}

export async function fetchTarget(id: string) {
  return targetsApi.get(id)
}

export async function fetchIndication(id: string) {
  return indicationsApi.get(id)
}

export async function searchEntities(query: string) {
  const results = await searchApi.search(query)
  // Restructure flat array into categorized object
  return {
    targets: results.filter(r => r.type === "target").map(r => ({ id: r.id, symbol: r.name, family: r.subtitle })),
    drugs: results.filter(r => r.type === "drug").map(r => ({ id: r.id, name: r.name, drug_type: r.subtitle, total_score: r.score })),
    indications: results.filter(r => r.type === "indication").map(r => ({ id: r.id, name: r.name, disease_area: r.subtitle })),
    companies: results.filter(r => r.type === "company").map(r => ({ id: r.id, name: r.name, ticker: r.subtitle?.split(" ")[0] || null })),
  }
}

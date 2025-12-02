import type {
  Target,
  TargetSummary,
  TargetDetail,
  AssetSummary,
  AssetDetail,
  Company,
  CompanyWithPipeline,
  StockQuote,
  SearchResult,
  WatchlistEntity,
  DiseaseAssociation,
  ChemistryMetrics,
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

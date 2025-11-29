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

// Export all APIs
export const api = {
  targets: targetsApi,
  drugs: drugsApi,
  indications: indicationsApi,
  scores: scoresApi,
  signatures: signaturesApi,
  search: searchApi,
  stats: statsApi,
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
  }
}

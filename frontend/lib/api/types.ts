// Pilldreams API Types
// Based on the epi_* tables in Supabase

export interface Target {
  id: number
  symbol: string
  name: string
  family: string
  target_class: string
  ot_target_id: string | null
  uniprot_id: string | null
  description: string | null
  // Computed fields from joins
  asset_count?: number
  avg_bio_score?: number
  avg_total_score?: number
}

export interface TargetSummary {
  id: number
  symbol: string
  name: string
  family: string
  target_class: string
  asset_count: number
  avg_bio_score: number
  avg_tractability_score: number
}

export interface TargetDetail extends Target {
  diseases: DiseaseAssociation[]
  assets: AssetSummary[]
  chemistry_stats: ChemistryStats | null
}

export interface Drug {
  id: number
  name: string
  chembl_id: string | null
  drug_type: string | null
  fda_approved: boolean
  first_approval_date: string | null
  source: string | null
}

export interface DrugWithScores extends Drug {
  bio_score: number | null
  chem_score: number | null
  tractability_score: number | null
  total_score: number | null
}

export interface Indication {
  id: number
  name: string
  efo_id: string | null
  disease_area: string | null
}

export interface Score {
  id: number
  drug_id: number
  indication_id: number
  bio_score: number | null
  chem_score: number | null
  tractability_score: number | null
  total_score: number | null
}

export interface DiseaseAssociation {
  efo_id: string
  disease_name: string
  bio_score: number
  asset_count: number
}

export interface AssetSummary {
  id: number
  name: string
  chembl_id: string | null
  target_symbol: string
  target_id: number
  indication_name: string
  indication_id: number
  phase: number | null
  bio_score: number | null
  chem_score: number | null
  tractability_score: number | null
  total_score: number | null
}

export interface AssetDetail extends AssetSummary {
  drug_type: string | null
  fda_approved: boolean
  mechanism: string | null
  company?: Company | null
  chemistry: ChemistryMetrics | null
}

export interface ChemistryMetrics {
  drug_id: number
  p_act_median: number | null
  p_act_best: number | null
  p_off_best: number | null
  delta_p: number | null
  n_activities_primary: number | null
  n_activities_total: number | null
  chem_score: number | null
}

export interface ChemistryStats {
  best_potency: number | null
  median_potency: number | null
  selectivity: number | null
  data_points: number
}

export interface Company {
  id: number
  name: string
  ticker: string | null
  market_cap: number | null
  description: string | null
}

export interface CompanyWithPipeline extends Company {
  asset_count: number
  avg_total_score: number
  assets: AssetSummary[]
}

export interface StockQuote {
  ticker: string
  price: number
  change: number
  change_percent: number
  market_cap: number | null
  updated_at: string
}

export interface SearchResult {
  type: "target" | "drug" | "company" | "indication"
  id: number
  name: string
  subtitle: string
  score?: number
}

export interface WatchlistEntity {
  id: number
  user_id: string
  entity_type: "company" | "target" | "asset"
  entity_id: number
  created_at: string
}

// Drug types
export interface DrugSummary {
  id: string  // UUID
  name: string
  chembl_id: string | null
  drug_type: string | null
  fda_approved: boolean
  max_phase: number | null  // Clinical phase (1-4)
  total_score: number | null
  bio_score: number | null
  chem_score: number | null
  tractability_score: number | null
}

export interface ScoreBreakdown {
  drug_id: number
  drug_name: string
  indication_id: number
  indication_name: string
  bio_score: number | null
  chem_score: number | null
  tractability_score: number | null
  total_score: number | null
}

export interface IndicationSummary {
  id: number
  name: string
  efo_id: string | null
  disease_area: string | null
  drug_count: number
}

export interface PlatformStats {
  total_targets: number
  total_drugs: number
  approved_drugs: number
  total_indications: number
  target_families: Record<string, number>
}

// ============ Epigenetic Editing Types ============

export interface EditingAssetSummary {
  id: string  // UUID
  name: string
  sponsor: string | null
  delivery_type: string | null
  dbd_type: string | null
  effector_type: string | null
  effector_domains: string[] | null
  target_gene_symbol: string | null
  primary_indication: string | null
  phase: number
  status: string
  total_editing_score: number | null
  target_bio_score: number | null
  modality_score: number | null
  durability_score: number | null
}

export interface EditingAssetDetail {
  id: string
  name: string
  sponsor: string | null
  modality: string
  delivery_type: string | null
  dbd_type: string | null
  effector_type: string | null
  effector_domains: string[] | null
  target_gene_symbol: string | null
  target_locus_description: string | null
  primary_indication: string | null
  phase: number
  status: string
  mechanism_summary: string | null
  description: string | null
  source_url: string | null
}

export interface EditingScores {
  id: string
  editing_asset_id: string
  target_bio_score: number | null
  editing_modality_score: number | null
  durability_score: number | null
  total_editing_score: number | null
  score_rationale: string | null
}

export interface EditingTargetGeneSummary {
  id: string
  symbol: string
  full_name: string | null
  gene_category: string | null
  is_classic_epi_target: boolean
  editor_ready_status: string
  editing_program_count: number
}

export interface EditingTargetGeneDetail {
  id: string
  symbol: string
  full_name: string | null
  ensembl_id: string | null
  uniprot_id: string | null
  gene_category: string | null
  is_classic_epi_target: boolean
  epi_target_id: string | null
  editor_ready_status: string
  editor_notes: string | null
  lof_tolerance: string | null
  primary_disease_areas: string[] | null
  open_targets_score: number | null
}

// API Response wrappers
export interface ApiResponse<T> {
  data: T
  error?: string
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  page_size: number
}

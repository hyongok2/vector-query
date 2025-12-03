export type BackendType = 'fastembed' | 'st';
export type E5Mode = 'auto' | 'query' | 'passage';

export interface ModelSpec {
  backend: BackendType;
  name: string;
  normalize: boolean;
  e5_mode: E5Mode;
}

export interface PresetModel {
  preset_id: string;
  backend: BackendType;
  name: string;
  normalize: boolean;
  e5_mode: E5Mode;
}

export interface QdrantConfig {
  url: string;
  collection: string;
  query_filter?: Record<string, unknown>;
}

export interface SearchRequest {
  text: string;
  preset_id?: string;
  model?: ModelSpec;
  top_k?: number;
  threshold?: number;
  with_payload?: boolean;
  qdrant: QdrantConfig;
}

export interface Hit {
  id: string | number;
  score: number;
  payload?: Record<string, unknown>;
}

export interface SearchResponse {
  took_ms: number;
  model: ModelSpec;
  collection: string;
  total_candidates: number;
  hits: Hit[];
}

export interface HealthResponse {
  ok: boolean;
  qdrant_url: string;
}

export interface ModelsResponse {
  models: PresetModel[];
}

// UI State Types
export interface SearchState {
  loading: boolean;
  error: string | null;
  result: SearchResponse | null;
}

export interface UISettings {
  darkMode: boolean;
  compactMode: boolean;
  showAdvanced: boolean;
}
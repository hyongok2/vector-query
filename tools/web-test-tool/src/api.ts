let BASE_URL = 'http://localhost:5200';

// Local type definitions to avoid import issues
type BackendType = 'fastembed' | 'st';
type E5Mode = 'auto' | 'query' | 'passage';

interface ModelSpec {
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

interface QdrantConfig {
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

interface HealthResponse {
  ok: boolean;
  qdrant_url: string;
}

interface ModelsResponse {
  models: PresetModel[];
}

class ApiError extends Error {
  public status?: number;
  public response?: Response;

  constructor(
    message: string,
    status?: number,
    response?: Response
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.response = response;
  }
}

// Function to set API base URL
export const setApiBaseUrl = (url: string) => {
  BASE_URL = url.endsWith('/') ? url.slice(0, -1) : url;
};

// Function to get current API base URL
export const getApiBaseUrl = () => BASE_URL;

// Export types for use in other files

export const api = {
  async getHealth(): Promise<HealthResponse> {
    try {
      const response = await fetch(`${BASE_URL}/health`);
      if (!response.ok) {
        throw new ApiError('Health check failed', response.status, response);
      }
      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) throw error;
      throw new ApiError('Network error: Unable to connect to API server');
    }
  },

  async getModels(): Promise<ModelsResponse> {
    try {
      const response = await fetch(`${BASE_URL}/models`);
      if (!response.ok) {
        throw new ApiError('Failed to fetch models', response.status, response);
      }
      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) throw error;
      throw new ApiError('Network error: Unable to fetch models');
    }
  },

  async search(request: SearchRequest): Promise<SearchResponse> {
    try {
      const response = await fetch(`${BASE_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`;
        try {
          const errorText = await response.text();
          errorMessage = errorText || errorMessage;
        } catch {
          // ignore
        }
        throw new ApiError(`Search failed: ${errorMessage}`, response.status, response);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) throw error;
      throw new ApiError('Network error: Unable to perform search');
    }
  },
};

export { ApiError };
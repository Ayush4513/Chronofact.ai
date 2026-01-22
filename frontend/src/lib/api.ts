/**
 * Chronofact.ai - API Client
 * Communicates with the FastAPI backend
 */

const API_BASE = '/api';

export interface TimelineEvent {
  timestamp: string;
  summary: string;
  sources: string[];
  media?: string;
  credibility_score: number;
  verified_sources: number;
  location?: string;
}

export interface Timeline {
  topic: string;
  events: TimelineEvent[];
  total_sources: number;
  avg_credibility: number;
  predictions?: string[];
}

export interface CredibilityAssessment {
  post_id: string;
  credibility_score: number;
  factors: string[];
  reasoning: string;
}

export interface MisinformationAnalysis {
  is_suspicious: boolean;
  suspicious_patterns: string[];
  risk_level: string;
  recommendation: string;
}

export interface Recommendation {
  action: string;
  reason: string;
}

export interface QueryRequest {
  topic: string;
  limit: number;
  location?: string;
  min_credibility?: number;
  include_media_only?: boolean;
}

export interface VerifyRequest {
  text: string;
  author?: string;
  engagement?: string;
}

export interface DetectRequest {
  text: string;
}

export interface RecommendRequest {
  query: string;
  limit: number;
}

class XTimelineAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error((error as any).detail || `HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }

  async healthCheck() {
    return this.request<{
      status: string;
      baml_available: boolean;
      qdrant_connected: boolean;
    }>('/health');
  }

  async generateTimeline(request: QueryRequest): Promise<Timeline> {
    return this.request<Timeline>('/timeline', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async verifyClaim(request: VerifyRequest): Promise<CredibilityAssessment> {
    return this.request<CredibilityAssessment>('/verify', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async detectMisinformation(request: DetectRequest): Promise<MisinformationAnalysis> {
    return this.request<MisinformationAnalysis>('/detect', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getRecommendations(request: RecommendRequest): Promise<{
    query: string;
    count: number;
    recommendations: Recommendation[];
  }> {
    return this.request('/recommend', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getConfig() {
    return this.request('/config');
  }
}

export const api = new XTimelineAPI();
export default XTimelineAPI;

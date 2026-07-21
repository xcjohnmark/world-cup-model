import { 
  AccuracyMetric, 
  TeamChampionProb, 
  BracketFull, 
  FifaStandingsResponse, 
  ExternalPredictionsResponse 
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetcher<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  try {
    const res = await fetch(url, {
      cache: "no-store",
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    if (!res.ok) {
      const errorBody = await res.json().catch(() => ({}));
      throw new Error(errorBody.error || `HTTP error! status: ${res.status}`);
    }

    return (await res.json()) as T;
  } catch (error) {
    console.error(`Fetch error for ${url}:`, error);
    throw error;
  }
}

// 1. Fetch full bracket structure
export async function fetchBracket(stage?: string, group?: string): Promise<BracketFull> {
  let endpoint = "/bracket";
  const params = new URLSearchParams();
  if (stage) params.append("stage", stage);
  if (group) params.append("group", group);
  const queryString = params.toString();
  if (queryString) {
    endpoint += `?${queryString}`;
  }
  return fetcher<BracketFull>(endpoint);
}

// 1b. Fetch actual bracket structure
export async function fetchActualBracket(): Promise<BracketFull> {
  return fetcher<BracketFull>("/bracket/actual");
}

// 2. Fetch bracket completion status (locked/unlocked)
export async function fetchBracketStatus(): Promise<{ group_stage_complete: boolean }> {
  return fetcher<{ group_stage_complete: boolean }>("/bracket-status");
}

// 3. Fetch predicted vs official standings accuracy metrics for a group
export async function fetchGroupAccuracy(group: string): Promise<AccuracyMetric> {
  return fetcher<AccuracyMetric>(`/group-accuracy?group=${group}`);
}

// 4. Fetch live official FIFA standings for a group
export async function fetchFifaStandings(group: string): Promise<FifaStandingsResponse> {
  return fetcher<FifaStandingsResponse>(`/fifa-standings?group=${group}`);
}

// 5. Fetch our model's top 5 champion predictions
export async function fetchTop5(): Promise<TeamChampionProb[]> {
  return fetcher<TeamChampionProb[]>("/top5");
}

// 6. Fetch external Opta and Nate Silver predictions
export async function fetchExternalPredictions(): Promise<ExternalPredictionsResponse> {
  return fetcher<ExternalPredictionsResponse>("/external-predictions");
}

// 7. Fetch standings and accuracy metrics for all groups (A-L) in a single request
export async function fetchGroupComparisonAll(): Promise<Record<string, { fifaStandings: FifaStandingsResponse; groupAccuracy: AccuracyMetric }>> {
  return fetcher<Record<string, { fifaStandings: FifaStandingsResponse; groupAccuracy: AccuracyMetric }>>("/group-comparison-all");
}


export interface MatchPrediction {
  match_id: string;
  stage: string;
  group: string | null;
  date: string;
  team_a: string;
  team_a_prob: number;
  draw_prob: number;
  team_b: string;
  team_b_prob: number;
  actual_result?: string | null;
  actual_team_a_score?: number | null;
  actual_team_b_score?: number | null;
}

export interface GroupStanding {
  team: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  points: number;
  goals_for?: number;
  goals_against?: number;
  goal_difference?: number;
}

export interface AccuracyMetric {
  ranking_correct: number | null;
  ranking_total: number;
  avg_points_diff: number | null;
}

export interface TeamChampionProb {
  team: string;
  champion_prob: number;
  finalist_prob: number;
  semifinalist_prob?: number;
  quarterfinalist_prob?: number;
}

export interface ExternalPrediction {
  rank: number;
  team: string;
  value: number;
  value_type: "probability" | "rating";
  last_updated: string;
  source: "opta" | "nate_silver";
}

export interface KnockoutMatch {
  match_id: string;
  stage: string;
  date: string;
  team_a: string;
  team_a_prob: number;
  draw_prob: number;
  team_b: string;
  team_b_prob: number;
  actual_result?: string | null;
  actual_team_a_score?: number | null;
  actual_team_b_score?: number | null;
}

// --- Dynamic API response schemas ---

export interface BracketGroup {
  teams: string[];
  matches: MatchPrediction[];
  predicted_qualifiers: string[];
}

export interface SimulationSummary {
  total_simulations: number;
  run_date: string;
  champion_probabilities: Record<string, number>;
}

export interface BracketFull {
  group_stage: Record<string, BracketGroup>;
  round_of_32: { matches: MatchPrediction[] };
  round_of_16: { matches: MatchPrediction[] };
  quarterfinals: { matches: MatchPrediction[] };
  semifinals: { matches: MatchPrediction[] };
  final: { matches: MatchPrediction[] };
  simulation_summary: SimulationSummary;
}

export interface FifaStandingsResponse {
  group: string;
  status: "not_started" | "active" | "completed";
  standings: GroupStanding[];
}

export interface OptaPredictionEntry {
  rank: number;
  team: string;
  champion_prob: number;
  finalist_prob: number;
  semifinalist_prob: number;
}

export interface OptaSection {
  last_updated: string;
  source_url: string;
  predictions: OptaPredictionEntry[];
}

export interface NateSilverPredictionEntry {
  rank: number;
  team: string;
  pele_rating: number;
}

export interface NateSilverSection {
  last_updated: string;
  source_url: string;
  predictions: NateSilverPredictionEntry[];
}

export interface ExternalPredictionsResponse {
  opta: OptaSection;
  nate_silver: NateSilverSection;
  cache_date?: string;
}

export interface GroupComparisonData {
  fifaStandings: FifaStandingsResponse;
  groupAccuracy: AccuracyMetric;
}

export type GroupComparisonAllResponse = Record<string, GroupComparisonData>;


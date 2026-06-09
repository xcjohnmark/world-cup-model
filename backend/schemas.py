from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

# --- Predictions Schemas ---

class PredictionItem(BaseModel):
    match_id: str = Field(..., description="Unique ID of the match")
    stage: str = Field(..., description="Tournament stage (e.g. Group Stage, Round of 32)")
    group: Optional[str] = Field(None, description="Group letter (A-L) or null for knockout")
    date: str = Field(..., description="Date of the match in YYYY-MM-DD")
    team_a: str = Field(..., description="Canonical name of Team A")
    team_a_prob: Optional[float] = Field(None, description="Win probability of Team A")
    draw_prob: Optional[float] = Field(None, description="Draw probability")
    team_b: str = Field(..., description="Canonical name of Team B")
    team_b_prob: Optional[float] = Field(None, description="Win probability of Team B")
    probabilistic: Optional[bool] = Field(None, description="Whether the prediction is simulated/probabilistic")


# --- Simulations/Probabilities Schemas ---

class SimulationTeam(BaseModel):
    team: str = Field(..., description="Team name")
    win_prob: float = Field(..., description="Probability of winning the World Cup")
    final_prob: float = Field(..., description="Probability of reaching the final")
    semifinal_prob: float = Field(..., description="Probability of reaching the semi-final")
    quarterfinal_prob: float = Field(..., description="Probability of reaching the quarter-final")
    r16_prob: float = Field(..., description="Probability of reaching the round of 16")
    r32_prob: float = Field(..., description="Probability of reaching the round of 32")

class SimulationResults(BaseModel):
    total_simulations: int = Field(..., description="Total Monte Carlo runs")
    teams: List[SimulationTeam] = Field(..., description="Progression probabilities for all teams")


# --- Top 5 Teams Schema ---

class TopTeam(BaseModel):
    team: str = Field(..., description="Team name")
    win_prob: float = Field(..., description="Win probability")


# --- Bracket Schemas ---

class BracketMatch(BaseModel):
    match_id: str
    date: str
    team_a: str
    team_a_prob: Optional[float] = None
    draw_prob: Optional[float] = None
    team_b: str
    team_b_prob: Optional[float] = None
    actual_result: Optional[str] = None

class BracketGroup(BaseModel):
    teams: List[str]
    matches: List[BracketMatch]
    predicted_qualifiers: List[str]

class SimulationSummary(BaseModel):
    total_simulations: int
    run_date: str
    champion_probabilities: Dict[str, float]

class BracketFull(BaseModel):
    group_stage: Dict[str, BracketGroup]
    round_of_32: Dict[str, List[BracketMatch]]
    round_of_16: Dict[str, List[BracketMatch]]
    quarterfinals: Dict[str, List[BracketMatch]]
    semifinals: Dict[str, List[BracketMatch]]
    final: Dict[str, List[BracketMatch]]
    simulation_summary: SimulationSummary


# --- Predict Match Schemas ---

class CustomMatchRequest(BaseModel):
    team_a: str
    team_b: str

class CustomMatchResponse(BaseModel):
    team_a: str
    team_a_prob: float
    draw_prob: float
    team_b: str
    team_b_prob: float


# --- Explain Match Schemas ---

class TeamStats(BaseModel):
    elo: float
    fifa_rank: int
    form_last_5: float
    goals_scored_10: float
    goals_conceded_10: float

class MatchExplanationResponse(BaseModel):
    team_a: str
    team_b: str
    explanation: str
    team_a_stats: TeamStats
    team_b_stats: TeamStats
    global_importance: Dict[str, float]


# --- Leaderboard Schemas ---

class LeaderboardModel(BaseModel):
    display_name: str
    description: str
    log_loss: Optional[float] = None
    accuracy: Optional[float] = None
    matches_evaluated: int
    is_own_model: bool
    data_source: Optional[str] = None

class LeaderboardMatchScorePrediction(BaseModel):
    team_a_prob: Optional[float] = None
    draw_prob: Optional[float] = None
    team_b_prob: Optional[float] = None

class LeaderboardMatchScore(BaseModel):
    match_id: str
    stage: str
    team_a: str
    team_b: str
    actual_team_a_score: Optional[int] = None
    actual_team_b_score: Optional[int] = None
    actual_outcome: Optional[str] = None
    predictions: Dict[str, LeaderboardMatchScorePrediction]

class LeaderboardResults(BaseModel):
    models: Dict[str, LeaderboardModel]
    match_scores: List[LeaderboardMatchScore]

import { MatchPrediction, GroupStanding, AccuracyMetric, FifaStandingsResponse } from "@/lib/types";

interface GroupTableComparisonProps {
  groupLetter: string;
  matches: MatchPrediction[];
  fifaStandings: FifaStandingsResponse | null;
  groupAccuracy: AccuracyMetric | null;
  groupLoading: boolean;
  groupError: boolean;
}

// Robust team name normalizer for rank comparisons
const normalizeTeamName = (name: string): string => {
  const n = name.toLowerCase().trim();
  if (n.includes("korea")) return "korea";
  if (n.includes("czech")) return "czechia";
  if (n.includes("usa") || n.includes("united states")) return "usa";
  if (n.includes("iran")) return "iran";
  if (n.includes("congo")) return "congo";
  if (n.includes("ivory coast") || n.includes("côte d'ivoire")) return "ivorycoast";
  if (n.includes("cape verde") || n.includes("cabo verde")) return "capeverde";
  return n.replace(/[^a-z0-9]/g, "");
};

export default function GroupTableComparison({
  groupLetter,
  matches,
  fifaStandings,
  groupAccuracy,
  groupLoading,
  groupError,
}: GroupTableComparisonProps) {
  
  // 1. Error State
  if (groupError) {
    return (
      <div className="font-sans text-black mt-4 w-full">
        <div className="border border-black p-8 text-center my-6 bg-white">
          <p className="text-sm text-red-600 font-bold">Could not load data. Please try again later.</p>
        </div>
      </div>
    );
  }

  // 2. Loading State
  if (groupLoading) {
    return (
      <div className="font-sans text-black mt-4 w-full">
        <div className="py-16 text-center text-sm text-gray-500 font-mono">
          Loading...
        </div>
      </div>
    );
  }

  // 3. Normal rendering calculation
  // Find all unique teams in these matches
  const teams = Array.from(
    new Set(matches.flatMap((m) => [m.team_a, m.team_b]))
  );

  const predictedStandings = teams.map((team) => {
    let played = 0;
    let won = 0;
    let drawn = 0;
    let lost = 0;
    let points = 0;

    matches.forEach((m) => {
      if (m.team_a === team) {
        played++;
        won += m.team_a_prob;
        drawn += m.draw_prob;
        lost += m.team_b_prob;
        points += 3 * m.team_a_prob + 1 * m.draw_prob;
      } else if (m.team_b === team) {
        played++;
        won += m.team_b_prob;
        drawn += m.draw_prob;
        lost += m.team_a_prob;
        points += 3 * m.team_b_prob + 1 * m.draw_prob;
      }
    });

    return {
      team,
      played,
      won,
      drawn,
      lost,
      points,
    };
  });

  // Sort by expected points descending
  predictedStandings.sort((a, b) => b.points - a.points);

  // Extract official standings list
  let officialStandings = fifaStandings?.standings || [];
  if (officialStandings.length === 0) {
    officialStandings = teams.map((team) => ({
      team,
      played: 0,
      won: 0,
      drawn: 0,
      lost: 0,
      points: 0,
    })).sort((a, b) => a.team.localeCompare(b.team));
  }
  const isStandingsActive = fifaStandings?.status && fifaStandings.status !== "not_started";

  // Check if accuracy is available (matches have been played)
  const showAccuracy =
    groupAccuracy &&
    groupAccuracy.ranking_correct !== null &&
    groupAccuracy.avg_points_diff !== null;

  return (
    <div className="mt-4 font-sans text-black w-full">
      {/* Accuracy Row */}
      <div className="bg-[#f9fafb] border border-black px-4 py-2 text-xs font-mono mb-4 text-center">
        {showAccuracy ? (
          <div>
            Ranking Accuracy: <span className="font-bold">{groupAccuracy.ranking_correct}/{groupAccuracy.ranking_total} correct</span>
            <span className="mx-3">|</span>
            Points Accuracy: <span className="font-bold">±{groupAccuracy.avg_points_diff?.toFixed(1)} pts avg</span>
          </div>
        ) : (
          <span className="text-gray-500 italic">Accuracy shown once matches are played</span>
        )}
      </div>

      {/* Side-by-Side Tables Grid (stacks vertically on mobile: predicted above, official below) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {/* Left Column: My Predicted Table */}
        <div className="w-full">
          <h4 className="text-xs font-bold uppercase tracking-wider text-black border-b border-black pb-1 mb-2">
            My Predicted Table (Group {groupLetter})
          </h4>
          <table className="min-w-full text-xs font-mono">
            <thead>
              <tr className="border-b border-black">
                <th className="text-left font-bold py-1 px-1 uppercase text-[10px]">Team</th>
                <th className="text-center font-bold py-1 px-1 uppercase text-[10px] w-10">MP</th>
                <th className="text-center font-bold py-1 px-1 uppercase text-[10px] w-10">W</th>
                <th className="text-center font-bold py-1 px-1 uppercase text-[10px] w-10">D</th>
                <th className="text-center font-bold py-1 px-1 uppercase text-[10px] w-10">L</th>
                <th className="text-right font-bold py-1 px-1 uppercase text-[10px] w-12">Pts</th>
              </tr>
            </thead>
            <tbody>
              {predictedStandings.map((row, idx) => {
                // Determine if predicted rank matches official rank
                let isRankCorrect = false;
                if (isStandingsActive && officialStandings.length > idx) {
                  const predictedNorm = normalizeTeamName(row.team);
                  const officialNorm = normalizeTeamName(officialStandings[idx]?.team);
                  isRankCorrect = predictedNorm === officialNorm;
                }

                return (
                  <tr key={row.team} className="border-b border-gray-200">
                    <td className={`py-1.5 px-1 text-left ${isRankCorrect ? "font-bold text-black underline decoration-1" : "text-gray-900"}`}>
                      {row.team}
                    </td>
                    <td className="py-1.5 px-1 text-center text-gray-600">{row.played}</td>
                    <td className="py-1.5 px-1 text-center text-gray-600">{row.won.toFixed(1)}</td>
                    <td className="py-1.5 px-1 text-center text-gray-600">{row.drawn.toFixed(1)}</td>
                    <td className="py-1.5 px-1 text-center text-gray-600">{row.lost.toFixed(1)}</td>
                    <td className="py-1.5 px-1 text-right font-bold text-black">{row.points.toFixed(1)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Right Column: FIFA Official Table */}
        <div className="w-full">
          <h4 className="text-xs font-bold uppercase tracking-wider text-black border-b border-black pb-1 mb-2">
            FIFA Official Table (Group {groupLetter})
          </h4>
          
          <table className="min-w-full text-xs font-mono">
            <thead>
              <tr className="border-b border-black">
                <th className="text-left font-bold py-1 px-1 uppercase text-[10px]">Team</th>
                <th className="text-center font-bold py-1 px-1 uppercase text-[10px] w-10">MP</th>
                <th className="text-center font-bold py-1 px-1 uppercase text-[10px] w-10">W</th>
                <th className="text-center font-bold py-1 px-1 uppercase text-[10px] w-10">D</th>
                <th className="text-center font-bold py-1 px-1 uppercase text-[10px] w-10">L</th>
                <th className="text-right font-bold py-1 px-1 uppercase text-[10px] w-12">Pts</th>
              </tr>
            </thead>
            <tbody>
              {officialStandings.map((row: GroupStanding) => (
                <tr key={row.team} className="border-b border-gray-200">
                  <td className="py-1.5 px-1 text-left font-bold text-black">{row.team}</td>
                  <td className="py-1.5 px-1 text-center text-gray-600">{row.played}</td>
                  <td className="py-1.5 px-1 text-center text-gray-600">{row.won}</td>
                  <td className="py-1.5 px-1 text-center text-gray-600">{row.drawn}</td>
                  <td className="py-1.5 px-1 text-center text-gray-600">{row.lost}</td>
                  <td className="py-1.5 px-1 text-right font-bold text-black">{row.points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

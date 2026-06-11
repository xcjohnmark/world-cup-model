import React from "react";
import { MatchPrediction } from "@/lib/types";

interface MatchCardProps {
  match: MatchPrediction;
}

export default function MatchCard({ match }: MatchCardProps) {
  // Format probability decimal to percentage string (X.X%)
  const formatPct = (prob: number) => {
    return `${(prob * 100).toFixed(1)}%`;
  };

  const hasResult = match.actual_result !== null && match.actual_result !== undefined;
  const teamAScore = match.actual_team_a_score ?? 0;
  const teamBScore = match.actual_team_b_score ?? 0;

  // Option 1 color resolver
  const getProbabilityColors = (prob: number, isDraw: boolean) => {
    if (isDraw) {
      return {
        bg: "#FEF7E0", // soft pale gold
        text: "#B06000", // muted amber
        dot: "#B06000"
      };
    }
    if (prob >= 0.50) {
      return {
        bg: "#E6F4EA", // soft mint-sage
        text: "#137333", // deep forest green
        dot: "#137333"
      };
    }
    if (prob < 0.30) {
      return {
        bg: "#FCE8E6", // soft rose blush
        text: "#C5221F", // muted crimson
        dot: "#C5221F"
      };
    }
    // Moderate win probability (30% - 49%)
    return {
      bg: "#F1F3F4", // soft slate grey
      text: "#424242", // muted slate
      dot: "#757575"
    };
  };

  const colorsA = getProbabilityColors(match.team_a_prob, false);
  const colorsDraw = getProbabilityColors(match.draw_prob, true);
  const colorsB = getProbabilityColors(match.team_b_prob, false);

  return (
    <div className="py-2 border-b border-[#eee] text-black font-sans w-full">
      {/* 3 Probability Rows - text-sm for minimum 14px font size */}
      <div className="flex flex-col gap-1 my-1">
        {/* Team A Row */}
        <div className="flex justify-between items-center text-sm">
          <span className={`${match.actual_result === "team_a" ? "font-bold text-black" : "text-gray-900"}`}>
            {match.team_a}
          </span>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full inline-block animate-pulse-subtle" style={{ backgroundColor: colorsA.dot }} />
            <span className="font-mono text-gray-700">{formatPct(match.team_a_prob)}</span>
          </div>
        </div>

        {/* Draw Row */}
        <div className="flex justify-between items-center text-sm text-gray-500">
          <span>Draw</span>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ backgroundColor: colorsDraw.dot }} />
            <span className="font-mono text-gray-500">{formatPct(match.draw_prob)}</span>
          </div>
        </div>

        {/* Team B Row */}
        <div className="flex justify-between items-center text-sm">
          <span className={`${match.actual_result === "team_b" ? "font-bold text-black" : "text-gray-900"}`}>
            {match.team_b}
          </span>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ backgroundColor: colorsB.dot }} />
            <span className="font-mono text-gray-700">{formatPct(match.team_b_prob)}</span>
          </div>
        </div>
      </div>

      {/* Proportional Probability Bar */}
      <div className="flex h-1.5 w-full bg-[#f5f5f5] gap-[1px] my-2">
        <div
          style={{ width: `${match.team_a_prob * 100}%`, backgroundColor: colorsA.bg }}
          title={`Win ${match.team_a}: ${formatPct(match.team_a_prob)}`}
        />
        <div
          style={{ width: `${match.draw_prob * 100}%`, backgroundColor: colorsDraw.bg }}
          title={`Draw: ${formatPct(match.draw_prob)}`}
        />
        <div
          style={{ width: `${match.team_b_prob * 100}%`, backgroundColor: colorsB.bg }}
          title={`Win ${match.team_b}: ${formatPct(match.team_b_prob)}`}
        />
      </div>

      {/* Actual Result Info Row - text-sm for minimum 14px */}
      {hasResult && (
        <div className="text-sm text-gray-500 font-sans italic mt-1.5">
          Result: {match.team_a} {teamAScore}–{teamBScore} {match.team_b}
        </div>
      )}
    </div>
  );
}

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

  return (
    <div className="py-2 border-b border-[#eee] text-black font-sans w-full">
      {/* 3 Probability Rows - text-sm for minimum 14px font size */}
      <div className="flex flex-col gap-1 my-1">
        {/* Team A Row */}
        <div className="flex justify-between items-center text-sm">
          <span className={`${match.actual_result === "team_a" ? "font-bold text-black" : "text-gray-900"}`}>
            {match.team_a}
          </span>
          <span className="font-mono text-gray-600">{formatPct(match.team_a_prob)}</span>
        </div>

        {/* Draw Row */}
        <div className="flex justify-between items-center text-sm text-gray-500">
          <span>Draw</span>
          <span className="font-mono">{formatPct(match.draw_prob)}</span>
        </div>

        {/* Team B Row */}
        <div className="flex justify-between items-center text-sm">
          <span className={`${match.actual_result === "team_b" ? "font-bold text-black" : "text-gray-900"}`}>
            {match.team_b}
          </span>
          <span className="font-mono text-gray-600">{formatPct(match.team_b_prob)}</span>
        </div>
      </div>

      {/* Proportional Probability Bar */}
      <div className="flex h-1.5 w-full bg-white gap-[1px] my-2">
        <div
          className="bg-[#e0e0e0]"
          style={{ width: `${match.team_a_prob * 100}%` }}
          title={`Win ${match.team_a}: ${formatPct(match.team_a_prob)}`}
        />
        <div
          className="bg-[#e0e0e0]"
          style={{ width: `${match.draw_prob * 100}%` }}
          title={`Draw: ${formatPct(match.draw_prob)}`}
        />
        <div
          className="bg-[#e0e0e0]"
          style={{ width: `${match.team_b_prob * 100}%` }}
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

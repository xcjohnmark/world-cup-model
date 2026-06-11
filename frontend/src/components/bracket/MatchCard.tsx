import React from "react";
import { MatchPrediction } from "@/lib/types";
import { getMatchScheduleDetails } from "@/lib/schedule";
import { Flag } from "@/lib/flags";

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

  // Retrieve schedule details (date, stadium, city, kickoff time)
  const schedule = getMatchScheduleDetails(match.team_a, match.team_b);

  // Timezone-safe date formatting (Thu, Jun 11, 2026)
  const formatDateString = (dateStr: string) => {
    const parts = dateStr.split("-");
    if (parts.length !== 3) return dateStr;
    const year = parseInt(parts[0], 10);
    const monthIdx = parseInt(parts[1], 10) - 1;
    const day = parseInt(parts[2], 10);
    
    const date = new Date(year, monthIdx, day);
    return date.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric"
    });
  };

  // Option 1 color resolver (Green, Blue, Red based on probability context)
  const getProbabilityColors = (prob: number, isDraw: boolean, isHigherWin: boolean) => {
    if (isDraw) {
      return {
        bg: "#2563EB", // vibrant primary blue
        text: "#1A73E8", // blue
        dot: "#1A73E8"
      };
    }
    if (isHigherWin) {
      return {
        bg: "#16A34A", // vibrant primary green
        text: "#137333", // green
        dot: "#137333"
      };
    }
    // Lower win probability
    return {
      bg: "#DC2626", // vibrant primary red
      text: "#C5221F", // red
      dot: "#C5221F"
    };
  };

  const isTeamA_higher = match.team_a_prob >= match.team_b_prob;
  const colorsA = getProbabilityColors(match.team_a_prob, false, isTeamA_higher);
  const colorsDraw = getProbabilityColors(match.draw_prob, true, false);
  const colorsB = getProbabilityColors(match.team_b_prob, false, !isTeamA_higher);

  return (
    <div className="py-2 border-b border-[#eee] text-black font-sans w-full">
      {/* 3 Probability Rows - text-sm for minimum 14px font size */}
      <div className="flex flex-col gap-1 my-1">
        {/* Team A Row */}
        <div className="flex justify-between items-center text-sm">
          <span className={`${match.actual_result === "team_a" ? "font-bold text-black" : "text-gray-900"} flex items-center`}>
            <Flag countryName={match.team_a} />
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
          <span className={`${match.actual_result === "team_b" ? "font-bold text-black" : "text-gray-900"} flex items-center`}>
            <Flag countryName={match.team_b} />
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

      {/* Schedule Info Row (Stadium, City, Date, Kickoff Time) */}
      {schedule && (
        <div className="text-[11px] text-gray-500 font-mono mt-1.5 flex flex-wrap gap-x-2 gap-y-0.5 items-center leading-normal">
          <span>{formatDateString(schedule.date)}</span>
          <span className="text-gray-300">•</span>
          <span>{schedule.time}</span>
          <span className="text-gray-300">•</span>
          <span className="italic">{schedule.stadium} ({schedule.city})</span>
        </div>
      )}
    </div>
  );
}

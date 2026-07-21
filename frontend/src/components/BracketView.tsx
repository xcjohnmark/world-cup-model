import React, { useState, useEffect } from "react";
import { AccuracyMetric, BracketFull, FifaStandingsResponse } from "@/lib/types";
import GroupSection from "./bracket/GroupSection";
import GroupTableComparison from "./bracket/GroupTableComparison";
import KnockoutBracket from "./bracket/KnockoutBracket";
import { fetchActualBracket } from "@/lib/api";

interface BracketViewProps {
  bracketData: BracketFull | null;
  bracketStatus: { group_stage_complete: boolean } | null;
  selectedGroup: string;
  setSelectedGroup: (group: string) => void;
  fifaStandings: FifaStandingsResponse | null;
  groupAccuracy: AccuracyMetric | null;
  groupLoading: boolean;
  groupError: boolean;
}

export default function BracketView({
  bracketData,
  bracketStatus,
  selectedGroup,
  setSelectedGroup,
  fifaStandings,
  groupAccuracy,
  groupLoading,
  groupError,
}: BracketViewProps) {
  const groupsList = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"];
  const [bracketType, setBracketType] = useState<"predicted" | "actual">("predicted");
  const [actualBracketData, setActualBracketData] = useState<BracketFull | null>(null);

  useEffect(() => {
    if (bracketType === "actual" && !actualBracketData) {
      fetchActualBracket()
        .then((data) => setActualBracketData(data))
        .catch((err) => console.error("Failed to load actual bracket data:", err));
    }
  }, [bracketType, actualBracketData]);

  const currentBracketData = bracketType === "predicted" ? bracketData : (actualBracketData || bracketData);

  // Extract matches for the selected group from bracketData
  const groupKey = `Group ${selectedGroup}`;
  const groupMatches = currentBracketData?.group_stage?.[groupKey]?.matches || [];
  const isGroupStageComplete = bracketStatus?.group_stage_complete ?? false;

  // Calculate total matches played and correct predictions across all groups
  let totalPlayed = 0;
  let correctCount = 0;

  if (currentBracketData?.group_stage) {
    Object.values(currentBracketData.group_stage).forEach((group) => {
      group.matches.forEach((match) => {
        const hasResult = match.actual_result !== null && match.actual_result !== undefined;
        if (hasResult) {
          totalPlayed++;
          const maxProb = Math.max(match.team_a_prob, match.draw_prob, match.team_b_prob);
          const predictedOutcome =
            maxProb === match.team_a_prob
              ? "team_a"
              : maxProb === match.team_b_prob
              ? "team_b"
              : "draw";
          if (predictedOutcome === match.actual_result) {
            correctCount++;
          }
        }
      });
    });
  }

  const accuracy = totalPlayed > 0 ? ((correctCount / totalPlayed) * 100).toFixed(1) : "0.0";

  return (
    <div className="text-black font-sans">
      {/* View Title */}
      <div className="border-b border-black pb-2 mb-6 flex flex-col md:flex-row md:justify-between md:items-end gap-3">
        <div>
          <h2 className="text-lg font-bold font-serif uppercase tracking-tight text-black">
            Tournament Bracket & Group Stage
          </h2>
          <p className="text-xs text-gray-500 italic mt-0.5">
            Group stage match predictions compared side-by-side with live FIFA standings.
          </p>
        </div>

        {/* Toggle between Predicted and Actual brackets */}
        <div className="flex gap-2 self-start md:self-auto my-2 md:my-0">
          <button
            onClick={() => setBracketType("predicted")}
            className={`px-3 py-1.5 border border-black text-xs font-bold uppercase transition-none ${
              bracketType === "predicted"
                ? "bg-black text-white"
                : "bg-white text-black hover:bg-gray-100"
            }`}
          >
            Predicted Bracket
          </button>
          <button
            onClick={() => setBracketType("actual")}
            className={`px-3 py-1.5 border border-black text-xs font-bold uppercase transition-none ${
              bracketType === "actual"
                ? "bg-black text-white"
                : "bg-white text-black hover:bg-gray-100"
            }`}
          >
            Actual Bracket
          </button>
        </div>

        {totalPlayed > 0 && bracketType === "predicted" && (
          <div className="bg-[#f9fafb] border border-black px-3 py-1.5 text-xs font-mono font-bold text-black self-start md:self-auto shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
            Matches Predicted Correctly: <span className="underline">{correctCount}/{totalPlayed}</span> ({accuracy}%)
          </div>
        )}
      </div>

      {/* Group Selector Bar */}
      <div className="flex flex-wrap justify-between items-center border border-black p-2 mb-6">
        <span className="text-xs font-bold uppercase tracking-wider px-2">Select Group:</span>
        <div className="flex gap-1 sm:gap-2">
          {groupsList.map((g) => (
            <button
              key={g}
              onClick={() => setSelectedGroup(g)}
              className={`w-7 h-7 flex items-center justify-center text-xs font-bold border transition-none ${
                selectedGroup === g
                  ? "bg-black text-white border-black"
                  : "bg-white text-black border-transparent hover:border-black"
              }`}
            >
              {g}
            </button>
          ))}
        </div>
      </div>

      {/* Side-by-Side Match Cards and Table Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
        {/* Left: 6 Match Cards */}
        <div>
          <GroupSection groupLetter={selectedGroup} matches={groupMatches} />
        </div>

        {/* Right: Predicted vs Official Standings Comparison */}
        <div>
          <GroupTableComparison
            groupLetter={selectedGroup}
            matches={groupMatches}
            fifaStandings={fifaStandings}
            groupAccuracy={groupAccuracy}
            groupLoading={groupLoading}
            groupError={groupError}
          />
        </div>
      </div>

      {/* Knockout Bracket Footer Section */}
      <div className="mt-12 border-t-2 border-black pt-6">
        <h3 className="text-sm font-bold font-sans uppercase tracking-widest text-black mb-4">
          Knockout Bracket
        </h3>

        <KnockoutBracket
          bracketData={currentBracketData}
          isGroupStageComplete={isGroupStageComplete}
        />
      </div>
    </div>
  );
}

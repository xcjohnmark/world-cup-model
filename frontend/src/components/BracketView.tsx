import React from "react";
import { AccuracyMetric, BracketFull, FifaStandingsResponse } from "@/lib/types";
import GroupSection from "./bracket/GroupSection";
import GroupTableComparison from "./bracket/GroupTableComparison";
import KnockoutBracket from "./bracket/KnockoutBracket";

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

  // Extract matches for the selected group from bracketData
  const groupKey = `Group ${selectedGroup}`;
  const groupMatches = bracketData?.group_stage?.[groupKey]?.matches || [];
  const isGroupStageComplete = bracketStatus?.group_stage_complete ?? false;

  return (
    <div className="text-black font-sans">
      {/* View Title */}
      <div className="border-b border-black pb-2 mb-6">
        <h2 className="text-lg font-bold font-serif uppercase tracking-tight text-black">
          Tournament Bracket & Group Stage
        </h2>
        <p className="text-xs text-gray-500 italic mt-0.5">
          Group stage match predictions compared side-by-side with live FIFA standings.
        </p>
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
          bracketData={bracketData}
          isGroupStageComplete={isGroupStageComplete}
        />
      </div>
    </div>
  );
}

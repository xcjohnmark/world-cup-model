import React from "react";
import MatchCard from "./MatchCard";
import { MatchPrediction } from "@/lib/types";

interface GroupSectionProps {
  groupLetter: string;
  matches: MatchPrediction[];
}

export default function GroupSection({ groupLetter, matches }: GroupSectionProps) {
  return (
    <div className="mb-6 font-sans">
      {/* Group Title Header */}
      <h3 className="text-sm font-bold font-sans uppercase tracking-widest text-black mb-2 pb-1 border-b-2 border-black">
        GROUP {groupLetter}
      </h3>
      
      {/* 6 Matches */}
      <div className="flex flex-col">
        {matches.map((match) => (
          <MatchCard key={match.match_id} match={match} />
        ))}
      </div>
    </div>
  );
}

import React from "react";
import MatchCard from "./MatchCard";
import { MatchPrediction, BracketFull } from "@/lib/types";

interface KnockoutBracketProps {
  bracketData: BracketFull | null;
  isGroupStageComplete: boolean;
}

export default function KnockoutBracket({
  bracketData,
  isGroupStageComplete,
}: KnockoutBracketProps) {
  // If locked, display the locked message board
  if (!isGroupStageComplete) {
    return (
      <div className="border border-black p-8 text-center my-6 bg-white font-sans text-black">
        <p className="text-base font-bold mb-1">
          🔒 Knockout bracket unlocks when group stage is complete
        </p>
        <p className="text-xs text-gray-500 font-mono">(Check back after June 27, 2026)</p>
      </div>
    );
  }

  // If unlocked, render knockout rounds in a vertical list sequence
  const roundOf32: MatchPrediction[] = bracketData?.round_of_32?.matches || [];
  const roundOf16: MatchPrediction[] = bracketData?.round_of_16?.matches || [];
  const quarterfinals: MatchPrediction[] = bracketData?.quarterfinals?.matches || [];
  const semifinals: MatchPrediction[] = bracketData?.semifinals?.matches || [];
  const final: MatchPrediction[] = bracketData?.final?.matches || [];

  return (
    <div className="font-sans text-black mt-6">
      {/* Round of 32 */}
      {roundOf32.length > 0 && (
        <div className="mb-8">
          <h4 className="text-sm font-bold uppercase tracking-widest text-black mb-3 border-b-2 border-black pb-1">
            ROUND OF 32
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-2">
            {roundOf32.map((match) => (
              <MatchCard key={match.match_id} match={match} />
            ))}
          </div>
        </div>
      )}

      {roundOf32.length > 0 && <hr className="my-6 border-black" />}

      {/* Round of 16 */}
      {roundOf16.length > 0 && (
        <div className="mb-8">
          <h4 className="text-sm font-bold uppercase tracking-widest text-black mb-3 border-b-2 border-black pb-1">
            ROUND OF 16
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-2">
            {roundOf16.map((match) => (
              <MatchCard key={match.match_id} match={match} />
            ))}
          </div>
        </div>
      )}

      {roundOf16.length > 0 && <hr className="my-6 border-black" />}

      {/* Quarterfinals */}
      {quarterfinals.length > 0 && (
        <div className="mb-8">
          <h4 className="text-sm font-bold uppercase tracking-widest text-black mb-3 border-b-2 border-black pb-1">
            QUARTERFINALS
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
            {quarterfinals.map((match) => (
              <MatchCard key={match.match_id} match={match} />
            ))}
          </div>
        </div>
      )}

      {quarterfinals.length > 0 && <hr className="my-6 border-black" />}

      {/* Semifinals */}
      {semifinals.length > 0 && (
        <div className="mb-8">
          <h4 className="text-sm font-bold uppercase tracking-widest text-black mb-3 border-b-2 border-black pb-1">
            SEMIFINALS
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
            {semifinals.map((match) => (
              <MatchCard key={match.match_id} match={match} />
            ))}
          </div>
        </div>
      )}

      {semifinals.length > 0 && <hr className="my-6 border-black" />}

      {/* Final */}
      {final.length > 0 && (
        <div className="mb-8">
          <h4 className="text-sm font-bold uppercase tracking-widest text-black mb-3 border-b-2 border-black pb-1">
            FINAL & THIRD PLACE
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
            {final.map((match) => (
              <MatchCard key={match.match_id} match={match} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

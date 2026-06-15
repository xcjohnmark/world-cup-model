import React, { useState, useEffect, useRef } from "react";
import { TeamChampionProb, ExternalPredictionsResponse } from "@/lib/types";
import { Flag } from "@/lib/flags";

interface Top5ComparisonProps {
  top5Teams: TeamChampionProb[];
  externalPredictions: ExternalPredictionsResponse | null;
}

interface ModelInfoTooltipProps {
  modelKey: string;
  title: string;
  methodology: string;
  description: string;
  activeTooltip: string | null;
  setActiveTooltip: (key: string | null) => void;
  align?: "left" | "right";
}

function ModelInfoTooltip({
  modelKey,
  title,
  methodology,
  description,
  activeTooltip,
  setActiveTooltip,
  align = "left",
}: ModelInfoTooltipProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isOpen = activeTooltip === modelKey;

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (isOpen && ref.current && !ref.current.contains(event.target as Node)) {
        setActiveTooltip(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, setActiveTooltip]);

  return (
    <div ref={ref} className="relative inline-block ml-1.5 select-none">
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setActiveTooltip(isOpen ? null : modelKey);
        }}
        className="text-gray-400 hover:text-black focus:outline-none transition-colors duration-150"
        aria-label={`About ${title}`}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="w-3.5 h-3.5 align-middle"
        >
          <path
            fillRule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {isOpen && (
        <div className={`absolute ${align === "right" ? "right-0" : "left-0"} mt-2 w-64 p-3 bg-white border border-black shadow-md rounded-none text-left normal-case font-sans z-50 text-[11px] leading-relaxed text-black`}>
          <div className="font-bold border-b border-black pb-1 mb-1.5 text-xs font-serif uppercase tracking-tight">
            {title}
          </div>
          <div className="mb-2">
            <span className="font-bold font-mono text-[9px] uppercase tracking-wider block text-gray-500 mb-0.5">
              Methodology
            </span>
            <p className="text-gray-900">{methodology}</p>
          </div>
          <div>
            <span className="font-bold font-mono text-[9px] uppercase tracking-wider block text-gray-500 mb-0.5">
              Description
            </span>
            <p className="text-gray-600">{description}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Top5Comparison({
  top5Teams,
  externalPredictions,
}: Top5ComparisonProps) {
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

  // Format probability decimal to percentage string
  const formatPct = (prob: number) => {
    return `${(prob * 100).toFixed(1)}%`;
  };

  // Compile row data (ranks 1 to 5)
  const rows = [0, 1, 2, 3, 4].map((idx) => {
    const rank = idx + 1;
    
    // My model prediction
    const myData = top5Teams[idx];
    const myText = myData ? `${myData.team}` : "—";
    const myVal = myData ? formatPct(myData.champion_prob) : "";

    // Opta prediction
    const optaData = externalPredictions?.opta?.predictions?.[idx];
    const optaText = optaData ? `${optaData.team}` : "—";
    const optaVal = optaData ? formatPct(optaData.champion_prob) : "";

    // Nate Silver prediction
    const nsData = externalPredictions?.nate_silver?.predictions?.[idx];
    const nsText = nsData ? `${nsData.team}` : "—";
    const nsVal = nsData ? `${nsData.pele_rating}` : "";

    return {
      rank,
      my: { text: myText, val: myVal },
      opta: { text: optaText, val: optaVal },
      ns: { text: nsText, val: nsVal },
    };
  });

  return (
    <div className="font-sans text-black my-6">
      {/* Section Header */}
      <h3 className="text-sm font-bold uppercase tracking-widest text-black mb-4 border-b-2 border-black pb-1">
        TOP 5 WORLD CUP WINNER PREDICTIONS
      </h3>

      {/* Grid of Stacked Cards (stacks vertically on mobile, columns on desktop) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1: My Model */}
        <div className="border border-black p-4 bg-white shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
          <div className="flex justify-between items-center border-b border-black pb-2 mb-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-black">MY MODEL</span>
            <ModelInfoTooltip
              modelKey="my"
              title="My XGBoost Simulator"
              methodology="Monte Carlo Tournament Simulation"
              description="Simulates the entire World Cup bracket 1,000,000 times using a machine learning model trained on historical match results, current FIFA rankings, Elo ratings, and team form trends."
              activeTooltip={activeTooltip}
              setActiveTooltip={setActiveTooltip}
              align="right"
            />
          </div>
          <table className="w-full text-xs font-mono">
            <tbody>
              {rows.map((row) => (
                <tr key={`my-${row.rank}`} className="border-b border-gray-100 last:border-0">
                  <td className="py-2.5 text-left">
                    <span className="text-gray-400 mr-2">{row.rank}.</span>
                    <span className="font-bold text-black inline-flex items-center">
                      <Flag countryName={row.my.text} />
                      {row.my.text}
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-bold text-gray-700">{row.my.val}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Card 2: Opta Analytics */}
        <div className="border border-black p-4 bg-white shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
          <div className="flex justify-between items-center border-b border-black pb-2 mb-3">
            <a
              href="https://theanalyst.com/articles/who-will-win-2026-fifa-world-cup-predictions-opta-supercomputer"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] font-bold uppercase tracking-wider text-black hover:underline"
            >
              OPTA ANALYTICS
            </a>
            <ModelInfoTooltip
              modelKey="opta"
              title="Opta Predictions"
              methodology="Proprietary Power Rankings & Betting Odds"
              description="Calculates outcome probabilities based on historical statistics, opponent strengths, betting markets, and Opta's proprietary global team power rankings."
              activeTooltip={activeTooltip}
              setActiveTooltip={setActiveTooltip}
              align="right"
            />
          </div>
          <table className="w-full text-xs font-mono">
            <tbody>
              {rows.map((row) => (
                <tr key={`opta-${row.rank}`} className="border-b border-gray-100 last:border-0">
                  <td className="py-2.5 text-left">
                    <span className="text-gray-400 mr-2">{row.rank}.</span>
                    <span className="font-bold text-black inline-flex items-center">
                      <Flag countryName={row.opta.text} />
                      {row.opta.text}
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-bold text-gray-700">{row.opta.val}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Card 3: Nate Silver (PELE) */}
        <div className="border border-black p-4 bg-white shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
          <div className="flex justify-between items-center border-b border-black pb-2 mb-3">
            <a
              href="https://www.natesilver.net/p/world-cup-2026-odds-predictions"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] font-bold uppercase tracking-wider text-black hover:underline"
            >
              NATE SILVER (PELE)
            </a>
            <ModelInfoTooltip
              modelKey="ns"
              title="Nate Silver (PELE)"
              methodology="Soccer Strength Rating Model"
              description="Nate Silver's PELE soccer rating outputs a team strength rating (numerical value representing overall quality) rather than a direct progression percentage."
              activeTooltip={activeTooltip}
              setActiveTooltip={setActiveTooltip}
              align="right"
            />
          </div>
          <table className="w-full text-xs font-mono">
            <tbody>
              {rows.map((row) => (
                <tr key={`ns-${row.rank}`} className="border-b border-gray-100 last:border-0">
                  <td className="py-2.5 text-left">
                    <span className="text-gray-400 mr-2">{row.rank}.</span>
                    <span className="font-bold text-black inline-flex items-center">
                      <Flag countryName={row.ns.text} />
                      {row.ns.text}
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-bold text-gray-700">{row.ns.val}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Table Legend/Explanation Note */}
      <p className="text-[11px] text-gray-500 italic font-sans mt-5 leading-relaxed">
        Note: My model and{" "}
        <a
          href="https://theanalyst.com/articles/who-will-win-2026-fifa-world-cup-predictions-opta-supercomputer"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-black"
        >
          Opta
        </a>{" "}
        express predictions as win probability (%).{" "}
        <a
          href="https://www.natesilver.net/p/world-cup-2026-odds-predictions"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-black"
        >
          Nate Silver
        </a>
        &apos;s PELE model outputs a team strength rating — a different methodology producing a different output format.
        Both are valid approaches to the same question.
      </p>
    </div>
  );
}

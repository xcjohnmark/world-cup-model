import React from "react";

interface FooterProps {
  runDate?: string;
  totalSimulations?: number;
}

export default function Footer({ runDate = "2026-06-09", totalSimulations = 1000000 }: FooterProps) {
  // Format the simulation count with commas (e.g. 1,000,000)
  const formattedSims = totalSimulations.toLocaleString();

  return (
    <footer className="w-full border-t border-[#eee] py-6 mt-12 bg-white text-center">
      <div className="journal-shell flex flex-col items-center gap-3">
        {/* Social Links Row */}
        <div className="flex flex-wrap justify-center items-center gap-2 text-sm font-sans font-medium text-black">
          <a
            href="https://x.com/xcjohnmark"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:underline"
          >
            Twitter/X
          </a>
          <span className="text-gray-300 mx-1">·</span>
          <a
            href="https://github.com/xcjohnmark"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:underline"
          >
            GitHub
          </a>
        </div>

        {/* Model Metadata Row */}
        <div className="text-xs text-gray-500 font-sans tracking-wide">
          <span>{formattedSims} simulations</span>
          <span className="text-gray-300 mx-2">·</span>
          <span>Model: XGBoost</span>
          <span className="text-gray-300 mx-2">·</span>
          <span>Last updated: <span className="font-mono text-gray-600">{runDate}</span></span>
        </div>
      </div>
    </footer>
  );
}

import React from "react";

export default function ArticleSection() {
  return (
    <div className="font-sans text-black mt-8">
      {/* Section Header */}
      <h3 className="text-sm font-bold uppercase tracking-widest text-black mb-1">
        HOW I PREDICTED THE WORLD CUP WINNER
      </h3>
      
      {/* Divider */}
      <hr className="border-black mb-6 mt-2" />

      {/* Styled Placeholder Block */}
      <div className="bg-[#f5f5f5] border border-gray-300 p-6 font-mono text-xs text-gray-700 leading-relaxed max-w-[75ch] w-full">
        <div className="font-bold text-center text-sm uppercase mb-4 text-black tracking-wider">
          [ARTICLE — TO BE WRITTEN]
        </div>
        
        <p className="mb-4 text-center italic text-gray-500 font-sans">
          Developer reminder: When writing the final article, replace this entire component&apos;s contents
          with plain HTML tags (like &lt;p&gt;, &lt;h3&gt;, &lt;ul&gt;) to display readable, editorial prose.
        </p>
        
        <div className="border-t border-gray-200 pt-4">
          <div className="font-bold uppercase mb-2 text-black text-[10px] tracking-wide">
            Suggested Article Structure:
          </div>
          <ol className="list-decimal list-inside space-y-2 pl-1 font-sans text-xs">
            <li>
              <span className="font-bold text-black">Introduction</span> — Why I built this model, what question it answers, and general context.
            </li>
            <li>
              <span className="font-bold text-black">The Data</span> — Training on 32,000+ international matches dating back to 1872, sourced from Kaggle.
            </li>
            <li>
              <span className="font-bold text-black">Feature Engineering</span> — Dynamically updating team Elo ratings, rolling form windows, and symmetric differences between opponent strengths.
            </li>
            <li>
              <span className="font-bold text-black">The XGBoost Model</span> — Training an XGBoost classifier to predict each match as a 3-class probability distribution (Win A, Draw, Win B).
            </li>
            <li>
              <span className="font-bold text-black">Probability Calibration</span> — Applying Platt scaling/calibration to correct raw model outputs so they act as reliable probabilities.
            </li>
            <li>
              <span className="font-bold text-black">The Monte Carlo Simulation</span> — Simulating the full 48-team 104-match tournament 1,000,000 times to calculate champion progression probabilities.
            </li>
            <li>
              <span className="font-bold text-black">Comparing to Opta</span> — Explaining why both models yielded the same top 5 favorites despite differences in underlying supercomputer methodologies.
            </li>
            <li>
              <span className="font-bold text-black">Comparing to Nate Silver</span> — Contrasting dynamic win probabilities (%) with static Elo-based strength ratings (PELE), and what each metric measures.
            </li>
            <li>
              <span className="font-bold text-black">What makes my model dynamic</span> — Demonstrating how standing arrays, match outcomes, and progression trees update in real-time after actual scores are entered.
            </li>
            <li>
              <span className="font-bold text-black">Limitations</span> — Reflecting on team squad listings, fatigue indexes, and home-field advantages to improve future iterations.
            </li>
          </ol>
        </div>
      </div>
    </div>
  );
}

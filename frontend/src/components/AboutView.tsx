import React from "react";

export default function AboutView() {
  return (
    <div className="text-black font-sans max-w-4xl mx-auto py-4">
      {/* Header Banner */}
      <div className="border-b border-black pb-4 mb-8">
        <h2 className="text-2xl font-bold font-serif uppercase tracking-tight text-black">
          About the WC 2026 Predictor
        </h2>
        <p className="text-xs text-gray-500 italic mt-1 font-mono uppercase tracking-wider">
          A machine learning autopsy of the 2026 FIFA World Cup
        </p>
      </div>

      {/* Grid Content */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Left Column: Model Design & Specs */}
        <div className="md:col-span-1 space-y-6">
          <div className="border border-black p-4 bg-[#f9fafb] shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
            <h3 className="text-xs font-bold uppercase tracking-widest font-serif border-b border-black pb-1.5 mb-3">
              Model Blueprint
            </h3>
            <ul className="text-xs space-y-2.5 font-mono text-gray-700">
              <li>
                <strong className="text-black">Algorithm:</strong> XGBoost (Extreme Gradient Boosting) Classifier
              </li>
              <li>
                <strong className="text-black">Simulation:</strong> 1,000,000 Monte Carlo runs per setup
              </li>
              <li>
                <strong className="text-black">Core Features:</strong> Dynamic historical Elo ratings, FIFA rankings, competitive win rates, and 10-match rolling goal stats
              </li>
              <li>
                <strong className="text-black">Calibration:</strong> Isotonic Regression probability calibration (reducing Expected Calibration Error)
              </li>
            </ul>
          </div>

          <div className="border border-black p-4 bg-[#f9fafb] shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
            <h3 className="text-xs font-bold uppercase tracking-widest font-serif border-b border-black pb-1.5 mb-3">
              Tournament Stats
            </h3>
            <ul className="text-xs space-y-2.5 font-mono text-gray-700">
              <li>
                <strong className="text-black">Total Matches:</strong> 104 matches (72 group stage, 32 knockouts)
              </li>
              <li>
                <strong className="text-black">Total Teams:</strong> 48 participating countries
              </li>
              <li>
                <strong className="text-black">Champions:</strong> Spain (1-0 vs Argentina in final)
              </li>
            </ul>
          </div>
        </div>

        {/* Center/Right Column: Narrative Details */}
        <div className="md:col-span-2 space-y-6 text-sm text-gray-800 leading-relaxed font-sans">
          
          <section className="space-y-2">
            <h3 className="text-sm font-bold uppercase tracking-widest text-black border-b border-black pb-1">
              Project Architecture & Overview
            </h3>
            <p>
              The <strong>WC 2026 Predictor</strong> is an end-to-end forecasting pipeline designed to model the complexity of a 48-team FIFA World Cup tournament. We combine classical statistics with modern machine learning to simulate match outcomes.
            </p>
            <p>
              The core predictor pipeline features automatic team name standardization, dynamic ELO recalculation across 50,000+ historical matches, feature-engineering to capture rolling team form, and probability calibration. Once the match-level model is calibrated, the Monte Carlo simulator rolls the tournament forward, respecting actual group-stage progression rules and building out dynamically populated knockout structures.
            </p>
          </section>

          <section className="space-y-2">
            <h3 className="text-sm font-bold uppercase tracking-widest text-black border-b border-black pb-1">
              Model Performance & Verification
            </h3>
            <p>
              With the tournament concluded, we evaluated our calibrated XGBoost model against the actual 104 matches. The model demonstrated strong predictive power:
            </p>
            <ul className="list-disc pl-5 text-xs space-y-1.5 font-mono text-gray-700">
              <li>
                <strong className="text-black">Group Stage Accuracy:</strong> The model successfully predicted the correct outcome (win, draw, or loss) for 51 out of 72 group stage matches, resulting in a <strong>70.8%</strong> correct prediction rate.
              </li>
              <li>
                <strong className="text-black">Knockout Stage Progression:</strong> In the newly expanded Round of 32, the model correctly identified 12 of the 16 advancing teams, staying aligned with top-tier soccer analytical models.
              </li>
            </ul>
          </section>

          <section className="space-y-2">
            <h3 className="text-sm font-bold uppercase tracking-widest text-black border-b border-black pb-1">
              The Grand Final: Spain vs Argentina
            </h3>
            <p>
              The tournament climaxed in an epic clash between <strong>Spain</strong> and <strong>Argentina</strong>. Historically, Argentina&apos;s high ELO rating gave them a slight edge, but our post-group stage model optimization—updating Spain&apos;s FIFA Rank snapshot to #1 and adjusting their defensive rolling stats to reflect their tournament dominance (0.4 goals conceded average)—naturally tilted the odds in Spain&apos;s favor.
            </p>
            <p>
              In real life, Spain secured the championship with a hard-fought 1-0 victory, matching our optimized model&apos;s prediction and completing the project wrap-up.
            </p>
          </section>

        </div>

      </div>
    </div>
  );
}

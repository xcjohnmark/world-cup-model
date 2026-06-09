import React from "react";
import { TeamChampionProb, ExternalPredictionsResponse } from "@/lib/types";
import Top5Comparison from "./predictions/Top5Comparison";
import ArticleSection from "./predictions/ArticleSection";

interface PredictionsViewProps {
  top5Teams: TeamChampionProb[];
  externalPredictions: ExternalPredictionsResponse | null;
}

export default function PredictionsView({
  top5Teams,
  externalPredictions,
}: PredictionsViewProps) {
  return (
    <div className="text-black font-sans">
      {/* Title Header */}
      <div className="border-b border-black pb-2 mb-6">
        <h2 className="text-lg font-bold font-serif uppercase tracking-tight text-black">
          Model Forecasts & Predictions
        </h2>
        <p className="text-xs text-gray-500 italic mt-0.5">
          Comparing Monte Carlo simulation models with Opta Analytics and Nate Silver PELE ratings.
        </p>
      </div>

      {/* Top 5 Comparison Table */}
      <Top5Comparison
        top5Teams={top5Teams}
        externalPredictions={externalPredictions}
      />

      {/* Editorial Article Section */}
      <ArticleSection />
    </div>
  );
}

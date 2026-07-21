"use client";

import { useState, useEffect } from "react";
import { 
  fetchBracket,
  fetchBracketStatus,
  fetchTop5,
  fetchExternalPredictions,
  fetchGroupComparisonAll
} from "@/lib/api";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import BracketView from "@/components/BracketView";
import PredictionsView from "@/components/PredictionsView";
import AboutView from "@/components/AboutView";
import SupportModal from "@/components/SupportModal";
import { 
  AccuracyMetric, 
  TeamChampionProb,
  BracketFull,
  FifaStandingsResponse,
  ExternalPredictionsResponse
} from "@/lib/types";

export default function Home() {
  // Views: 'bracket' or 'predictions' or 'about'
  const [activeView, setActiveView] = useState<"bracket" | "predictions" | "about">("bracket");
  
  // Support Modal State
  const [isSupportModalOpen, setIsSupportModalOpen] = useState<boolean>(false);
  
  // Selected World Cup group for Bracket view (A to L)
  const [selectedGroup, setSelectedGroup] = useState<string>("A");
  
  // API Data States
  const [bracketData, setBracketData] = useState<BracketFull | null>(null);
  const [bracketStatus, setBracketStatus] = useState<{ group_stage_complete: boolean } | null>(null);
  const [fifaStandings, setFifaStandings] = useState<FifaStandingsResponse | null>(null);
  const [groupAccuracy, setGroupAccuracy] = useState<AccuracyMetric | null>(null);
  const [externalPredictions, setExternalPredictions] = useState<ExternalPredictionsResponse | null>(null);
  const [top5Teams, setTop5Teams] = useState<TeamChampionProb[]>([]);
  
  // Preloaded standings and accuracy for all groups
  const [groupComparisonAll, setGroupComparisonAll] = useState<Record<string, { fifaStandings: FifaStandingsResponse, groupAccuracy: AccuracyMetric }> | null>(null);
  
  // Loading & Error States
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Group-level loading & error states
  const [groupLoading, setGroupLoading] = useState<boolean>(false);
  const [groupError, setGroupError] = useState<boolean>(false);
  
  // Refresh controller for when matches are updated
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  // Fetch initial data (bracket structure, status, external predictions, top 5, and all group comparisons)
  useEffect(() => {
    async function loadInitialData() {
      try {
        setLoading(true);
        const [bracket, status, external, top5, comparisonAll] = await Promise.all([
          fetchBracket(),
          fetchBracketStatus(),
          fetchExternalPredictions(),
          fetchTop5(),
          fetchGroupComparisonAll()
        ]);
        
        setBracketData(bracket);
        setBracketStatus(status);
        setExternalPredictions(external);
        setTop5Teams(top5);
        setGroupComparisonAll(comparisonAll);
        setError(null);
      } catch (err) {
        console.error("Failed to load initial predictor data:", err);
        setError("The prediction engine is temporarily unavailable.");
      } finally {
        setLoading(false);
      }
    }
    
    loadInitialData();
  }, [refreshTrigger]);

  // Load selected group standings instantly from memory cache when group selection changes
  useEffect(() => {
    if (!groupComparisonAll || !selectedGroup) return;
    
    const currentData = groupComparisonAll[selectedGroup];
    if (currentData) {
      setFifaStandings(currentData.fifaStandings);
      setGroupAccuracy(currentData.groupAccuracy);
      setGroupLoading(false);
      setGroupError(false);
    } else {
      setFifaStandings(null);
      setGroupAccuracy(null);
    }
  }, [selectedGroup, groupComparisonAll]);

  const triggerRefresh = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const runDate = bracketData?.simulation_summary?.run_date || "2026-06-09";
  const totalSimulations = bracketData?.simulation_summary?.total_simulations || 1000000;

  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* Navbar */}
      <Navbar 
        activeView={activeView} 
        setActiveView={setActiveView} 
        onSupportClick={() => setIsSupportModalOpen(true)}
      />

      {/* Main Content Container */}
      <div className="journal-shell flex-1 py-6">
        {/* Loading and Error States */}
        {loading && !bracketData ? (
          <div className="py-20 text-center font-sans text-sm text-gray-500">
            Loading...
          </div>
        ) : error ? (
          <div className="py-12 border border-black p-6 text-center my-6 bg-white font-sans max-w-lg mx-auto">
            <p className="font-bold text-red-600 mb-2">Error</p>
            <p className="text-sm text-gray-700 font-medium mb-4">{error}</p>
            <button 
              onClick={triggerRefresh}
              className="px-4 py-2 border border-black text-xs font-bold uppercase hover:bg-gray-100 transition-none"
            >
              Retry Connection
            </button>
          </div>
        ) : (
          <main className="min-h-[500px]">
            {activeView === "bracket" ? (
              <BracketView
                bracketData={bracketData}
                bracketStatus={bracketStatus}
                selectedGroup={selectedGroup}
                setSelectedGroup={setSelectedGroup}
                fifaStandings={fifaStandings}
                groupAccuracy={groupAccuracy}
                groupLoading={groupLoading}
                groupError={groupError}
              />
            ) : activeView === "predictions" ? (
              <PredictionsView
                top5Teams={top5Teams}
                externalPredictions={externalPredictions}
              />
            ) : (
              <AboutView />
            )}
          </main>
        )}
      </div>

      {/* Footer */}
      <Footer runDate={runDate} totalSimulations={totalSimulations} />

      {/* Support Modal */}
      <SupportModal 
        isOpen={isSupportModalOpen} 
        onClose={() => setIsSupportModalOpen(false)} 
      />
    </div>
  );
}

import { TeamChampionProb, ExternalPredictionsResponse } from "@/lib/types";
import { Flag } from "@/lib/flags";

interface Top5ComparisonProps {
  top5Teams: TeamChampionProb[];
  externalPredictions: ExternalPredictionsResponse | null;
}

// Format date string (e.g. "2026-06-09T07:00:00Z" -> "June 9")
const formatDate = (dateStr?: string) => {
  if (!dateStr) return "";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", { month: "long", day: "numeric" });
  } catch {
    return dateStr;
  }
};

export default function Top5Comparison({
  top5Teams,
  externalPredictions,
}: Top5ComparisonProps) {
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

  // Extract cache date if scraper fell back to cache
  const cacheDate = externalPredictions?.cache_date;
  const formattedCache = cacheDate ? formatDate(cacheDate) : null;

  return (
    <div className="font-sans text-black my-6">
      {/* Section Header */}
      <h3 className="text-sm font-bold uppercase tracking-widest text-black mb-3 border-b-2 border-black pb-1">
        TOP 5 WORLD CUP WINNER PREDICTIONS
      </h3>

      {/* Comparison Table */}
      <div className="overflow-x-auto">
        <table className="min-w-[600px] w-full text-xs font-mono border-t border-b border-black">
          <thead>
            <tr className="border-b border-black text-[10px] uppercase">
              <th className="py-2.5 px-3 text-left font-bold border-r border-gray-200">
                MY MODEL
                <span className="block text-[8px] font-normal text-gray-500 lowercase font-sans mt-0.5">
                  (Monte Carlo, June 2026)
                </span>
              </th>
              <th className="py-2.5 px-3 text-left font-bold border-r border-gray-200">
                OPTA ANALYTICS
                <span className="block text-[8px] font-normal text-gray-500 lowercase font-sans mt-0.5">
                  (Opta Analyst, 1 June 2026{formattedCache ? ` · cached ${formattedCache}` : ""})
                </span>
              </th>
              <th className="py-2.5 px-3 text-left font-bold">
                NATE SILVER (PELE)
                <span className="block text-[8px] font-normal text-gray-500 lowercase font-sans mt-0.5">
                  (Strength Rating, June 2026)
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.rank} className="border-b border-gray-200">
                {/* Column 1: My Model */}
                <td className="py-2 px-3 border-r border-gray-200">
                  <div className="flex justify-between items-center">
                    <span className="inline-flex items-center">
                      <span className="text-gray-400 mr-1.5">{row.rank}.</span>
                      <span className="font-bold text-black inline-flex items-center">
                        <Flag countryName={row.my.text} />
                        {row.my.text}
                      </span>
                    </span>
                    <span className="font-bold text-gray-700">{row.my.val}</span>
                  </div>
                </td>
                {/* Column 2: Opta */}
                <td className="py-2 px-3 border-r border-gray-200">
                  <div className="flex justify-between items-center">
                    <span className="inline-flex items-center">
                      <span className="text-gray-400 mr-1.5">{row.rank}.</span>
                      <span className="font-bold text-black inline-flex items-center">
                        <Flag countryName={row.opta.text} />
                        {row.opta.text}
                      </span>
                    </span>
                    <span className="font-bold text-gray-700">{row.opta.val}</span>
                  </div>
                </td>
                {/* Column 3: Nate Silver */}
                <td className="py-2 px-3">
                  <div className="flex justify-between items-center">
                    <span className="inline-flex items-center">
                      <span className="text-gray-400 mr-1.5">{row.rank}.</span>
                      <span className="font-bold text-black inline-flex items-center">
                        <Flag countryName={row.ns.text} />
                        {row.ns.text}
                      </span>
                    </span>
                    <span className="font-bold text-gray-700">{row.ns.val}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Table Legend/Explanation Note */}
      <p className="text-[11px] text-gray-500 italic font-sans mt-3 leading-relaxed">
        Note: My model and Opta express predictions as win probability (%). Nate Silver&apos;s PELE model
        outputs a team strength rating — a different methodology producing a different output format.
        Both are valid approaches to the same question.
      </p>
    </div>
  );
}

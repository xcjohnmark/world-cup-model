import scheduleData from "./wc_2026_schedule.json";

// Mappings from openfootball names to canonical names used in our app
const openFootballToCanonical: Record<string, string> = {
  "Bosnia & Herzegovina": "Bosnia and Herzegovina",
  "Cape Verde": "Cabo Verde",
  "Curaçao": "Curaçao",
  "Czech Republic": "Czechia",
  "DR Congo": "Congo DR",
  "Iran": "IR Iran",
  "Ivory Coast": "Côte d'Ivoire",
  "South Korea": "Korea Republic",
  "Turkey": "Türkiye",
  "USA": "United States"
};

// Mappings from match grounds to stadium names and city details
const groundToDetails: Record<string, { stadium: string; city: string }> = {
  "Atlanta": { stadium: "Mercedes-Benz Stadium", city: "Atlanta, USA" },
  "Boston (Foxborough)": { stadium: "Gillette Stadium", city: "Foxborough, USA" },
  "Dallas (Arlington)": { stadium: "AT&T Stadium", city: "Arlington, USA" },
  "Guadalajara (Zapopan)": { stadium: "Estadio Akron", city: "Zapopan, Mexico" },
  "Houston": { stadium: "NRG Stadium", city: "Houston, USA" },
  "Kansas City": { stadium: "Arrowhead Stadium", city: "Kansas City, USA" },
  "Los Angeles (Inglewood)": { stadium: "SoFi Stadium", city: "Inglewood, USA" },
  "Mexico City": { stadium: "Estadio Azteca", city: "Mexico City, Mexico" },
  "Miami (Miami Gardens)": { stadium: "Hard Rock Stadium", city: "Miami Gardens, USA" },
  "Monterrey (Guadalupe)": { stadium: "Estadio BBVA", city: "Guadalupe, Mexico" },
  "New York/New Jersey (East Rutherford)": { stadium: "MetLife Stadium", city: "East Rutherford, USA" },
  "Philadelphia": { stadium: "Lincoln Financial Field", city: "Philadelphia, USA" },
  "San Francisco Bay Area (Santa Clara)": { stadium: "Levi's Stadium", city: "Santa Clara, USA" },
  "Seattle": { stadium: "Lumen Field", city: "Seattle, USA" },
  "Toronto": { stadium: "BMO Field", city: "Toronto, Canada" },
  "Vancouver": { stadium: "BC Place", city: "Vancouver, Canada" }
};

// Helper to normalize team names for comparison (strips accents, punctuation, spaces)
const normalizeName = (name: string): string => {
  return name
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "") // remove accents
    .replace(/[^a-z0-9]/g, "");     // remove all non-alphanumeric chars
};

export interface MatchScheduleDetails {
  date: string;
  stadium: string;
  city: string;
  time: string;
}

/**
 * Looks up a group stage match by team names (in either order)
 * and returns the official date, stadium name, city, and kickoff time.
 */
export function getMatchScheduleDetails(teamA: string, teamB: string): MatchScheduleDetails | null {
  if (!teamA || !teamB || teamA === "TBD" || teamB === "TBD") {
    return null;
  }

  const normA = normalizeName(teamA);
  const normB = normalizeName(teamB);

  const match = scheduleData.matches.find((m) => {
    const t1 = openFootballToCanonical[m.team1] || m.team1;
    const t2 = openFootballToCanonical[m.team2] || m.team2;
    const norm1 = normalizeName(t1);
    const norm2 = normalizeName(t2);

    return (normA === norm1 && normB === norm2) || (normA === norm2 && normB === norm1);
  });

  if (!match) {
    return null;
  }

  const ground = match.ground || "";
  const details = groundToDetails[ground] || { stadium: ground || "Unknown Stadium", city: ground || "Unknown City" };

  return {
    date: match.date,
    stadium: details.stadium,
    city: details.city,
    time: match.time || "TBD"
  };
}

import React from "react";

// Mappings from team name (canonical or external) to ISO country code (2-letter)
const countryToIsoCode: Record<string, string> = {
  "Algeria": "dz",
  "Argentina": "ar",
  "Australia": "au",
  "Austria": "at",
  "Belgium": "be",
  "Bosnia and Herzegovina": "ba",
  "Bosnia & Herzegovina": "ba",
  "Brazil": "br",
  "Cabo Verde": "cv",
  "Cape Verde": "cv",
  "Canada": "ca",
  "Colombia": "co",
  "Congo DR": "cd",
  "DR Congo": "cd",
  "Croatia": "hr",
  "Curaçao": "cw",
  "Curaao": "cw",
  "Czechia": "cz",
  "Czech Republic": "cz",
  "Côte d'Ivoire": "ci",
  "Côte d’Ivoire": "ci",
  "Cote d'Ivoire": "ci",
  "Ecuador": "ec",
  "Egypt": "eg",
  "England": "gb-eng",
  "France": "fr",
  "Germany": "de",
  "Ghana": "gh",
  "Haiti": "ht",
  "IR Iran": "ir",
  "Iran": "ir",
  "Iraq": "iq",
  "Japan": "jp",
  "Jordan": "jo",
  "Korea Republic": "kr",
  "South Korea": "kr",
  "Mexico": "mx",
  "Morocco": "ma",
  "Netherlands": "nl",
  "New Zealand": "nz",
  "Norway": "no",
  "Panama": "pa",
  "Paraguay": "py",
  "Portugal": "pt",
  "Qatar": "qa",
  "Saudi Arabia": "sa",
  "Scotland": "gb-sct",
  "Senegal": "sn",
  "South Africa": "za",
  "Spain": "es",
  "Sweden": "se",
  "Switzerland": "ch",
  "Tunisia": "tn",
  "Türkiye": "tr",
  "Turkey": "tr",
  "United States": "us",
  "USA": "us",
  "Uruguay": "uy",
  "Uzbekistan": "uz"
};

// Helper to normalize names to match keys in countryToIsoCode
const normalizeKey = (name: string): string => {
  return name
    .trim()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, ""); // remove accents
};

/**
 * Returns the Flag CDN URL for a country name
 */
export function getCountryFlagUrl(countryName: string): string | null {
  if (!countryName || countryName === "TBD" || countryName === "—" || countryName === "TBD (W1)" || countryName === "TBD (W2)") {
    return null;
  }

  // Exact match
  const code = countryToIsoCode[countryName];
  if (code) {
    return `https://flagcdn.com/w40/${code}.png`;
  }

  // Match normalized key
  const normalized = normalizeKey(countryName);
  for (const [key, value] of Object.entries(countryToIsoCode)) {
    if (normalizeKey(key).toLowerCase() === normalized.toLowerCase()) {
      return `https://flagcdn.com/w40/${value}.png`;
    }
  }

  return null;
}

interface FlagProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  countryName: string;
  className?: string;
}

/**
 * Flag component that renders a resized PNG flag just before the country name
 */
export function Flag({ countryName, className, ...props }: FlagProps) {
  const url = getCountryFlagUrl(countryName);
  
  if (!url) {
    return null;
  }

  return (
    <img
      src={url}
      alt={`${countryName} flag`}
      className={`inline-block mr-1.5 align-middle border border-[#ccc] shadow-sm ${className || ""}`}
      style={{
        width: "18px",
        height: "12px",
        objectFit: "cover",
        display: "inline-block",
        verticalAlign: "middle",
        ...props.style
      }}
      loading="lazy"
      {...props}
    />
  );
}

import React from "react";

interface NavbarProps {
  activeView: "bracket" | "predictions" | "about";
  setActiveView: (view: "bracket" | "predictions" | "about") => void;
  onSupportClick: () => void;
}

export default function Navbar({ activeView, setActiveView, onSupportClick }: NavbarProps) {
  return (
    <nav className="sticky top-0 bg-white z-[100] border-b border-[#eee] py-3.5 w-full">
      {/* 
        Responsive behavior: 
        - Screens < 600px: Wrap items, gap-y-3. Title and Support side-by-side, Toggles on their own row.
        - Screens >= 600px: No wrap, items in a single horizontal row.
      */}
      <div className="journal-shell flex flex-wrap min-[600px]:flex-nowrap justify-between items-center gap-y-3 gap-x-2">
        {/* Left: Site Title */}
        <div className="min-[600px]:flex-1 text-left">
          <span className="text-base font-bold uppercase tracking-tight text-black font-serif block">
            WC 2026 Predictor
          </span>
        </div>

        {/* Right: Support Button */}
        <div className="flex justify-end order-2 min-[600px]:order-3 min-[600px]:flex-1">
          <button
            onClick={onSupportClick}
            className="px-3 py-1.5 border border-black text-[10px] font-bold uppercase hover:bg-black hover:text-white transition-none text-black text-center"
          >
            SUPPORT PROJECT
          </button>
        </div>

        {/* Center: Toggle Buttons */}
        <div className="w-full min-[600px]:w-auto flex justify-center gap-6 order-3 min-[600px]:order-2 mt-1 min-[600px]:mt-0">
          <button
            onClick={() => setActiveView("bracket")}
            className={`text-xs tracking-widest font-bold font-sans py-1 transition-none border-b-2 ${
              activeView === "bracket"
                ? "border-black text-black"
                : "border-transparent text-gray-400 hover:text-black"
            }`}
          >
            BRACKET
          </button>
          <button
            onClick={() => setActiveView("predictions")}
            className={`text-xs tracking-widest font-bold font-sans py-1 transition-none border-b-2 ${
              activeView === "predictions"
                ? "border-black text-black"
                : "border-transparent text-gray-400 hover:text-black"
            }`}
          >
            PREDICTIONS
          </button>
          <button
            onClick={() => setActiveView("about")}
            className={`text-xs tracking-widest font-bold font-sans py-1 transition-none border-b-2 ${
              activeView === "about"
                ? "border-black text-black"
                : "border-transparent text-gray-400 hover:text-black"
            }`}
          >
            ABOUT
          </button>
        </div>
      </div>
    </nav>
  );
}

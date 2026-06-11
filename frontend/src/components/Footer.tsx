import React from "react";

interface FooterProps {
  runDate?: string;
  totalSimulations?: number;
}

export default function Footer(props: FooterProps) {
  return (
    <footer 
      className="w-full border-t border-[#eee] py-6 mt-12 bg-white text-center"
      data-run-date={props.runDate}
      data-simulations={props.totalSimulations}
    >
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
      </div>
    </footer>
  );
}

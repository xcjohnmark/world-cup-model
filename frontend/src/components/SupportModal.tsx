"use client";

import React, { useState, useEffect } from "react";
import { X, Copy, Check, Wallet, CreditCard, AlertTriangle } from "lucide-react";

interface SupportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type CryptoAsset = "USDT" | "USDC";

interface NetworkOption {
  name: string;
  displayName: string;
  address: string;
  networkType: string;
}

const ASSET_OPTIONS: CryptoAsset[] = ["USDT", "USDC"];

// Read addresses from environment variables or fall back to configured values
const evmAddress = process.env.NEXT_PUBLIC_CRYPTO_EVM_ADDRESS || "0x44a85db3E66D74059A469ade98ED2A33E21Cd279";
const tronAddress = process.env.NEXT_PUBLIC_CRYPTO_TRON_ADDRESS || "";
const solanaAddress = process.env.NEXT_PUBLIC_CRYPTO_SOLANA_ADDRESS || "Ek9xMDhceBrCn7ArHEg8mZmTrHb6xdUmK8vdJ7JZxBgD";

// Networks available for USDT
const usdtNetworks: NetworkOption[] = [
  { name: "Arbitrum", displayName: "Arbitrum One", address: evmAddress, networkType: "EVM" },
  { name: "Polygon", displayName: "Polygon PoS", address: evmAddress, networkType: "EVM" },
  { name: "BSC", displayName: "BNB Smart Chain (BEP20)", address: evmAddress, networkType: "EVM" },
  { name: "TRC20", displayName: "TRON (TRC20)", address: tronAddress, networkType: "TRON" },
].filter(net => net.address !== "");

// Networks available for USDC
const usdcNetworks: NetworkOption[] = [
  { name: "Arbitrum", displayName: "Arbitrum One", address: evmAddress, networkType: "EVM" },
  { name: "Polygon", displayName: "Polygon PoS", address: evmAddress, networkType: "EVM" },
  { name: "Solana", displayName: "Solana", address: solanaAddress, networkType: "Solana" },
].filter(net => net.address !== "");

export default function SupportModal({ isOpen, onClose }: SupportModalProps) {
  const [activeTab, setActiveTab] = useState<"crypto" | "fiat">("crypto");
  const [selectedAsset, setSelectedAsset] = useState<CryptoAsset>("USDT");
  const [copied, setCopied] = useState(false);
  const [qrLoaded, setQrLoaded] = useState(false);

  const networks = selectedAsset === "USDT" ? usdtNetworks : usdcNetworks;
  const [selectedNetwork, setSelectedNetwork] = useState<NetworkOption | null>(networks[0] || null);

  // Sync selected network when asset changes
  useEffect(() => {
    const defaultNetworks = selectedAsset === "USDT" ? usdtNetworks : usdcNetworks;
    setSelectedNetwork(defaultNetworks[0] || null);
    setQrLoaded(false);
  }, [selectedAsset]);

  // Reset QR code loaded state when network changes
  useEffect(() => {
    setQrLoaded(false);
  }, [selectedNetwork]);

  const handleCopy = async () => {
    if (!selectedNetwork) return;
    try {
      await navigator.clipboard.writeText(selectedNetwork.address);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  // Close modal on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden"; // Prevent background scroll
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  const qrCodeUrl = selectedNetwork
    ? `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(selectedNetwork.address)}`
    : "";

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-black/40 backdrop-blur-[2px]"
      />

      {/* Modal Container */}
      <div
        className="relative bg-white border border-black max-w-[480px] w-full p-6 font-sans shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] z-10 flex flex-col"
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 text-black border border-transparent hover:border-black transition-none focus:outline-none"
          aria-label="Close modal"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header */}
        <div className="mb-6">
          <h2 className="text-lg font-bold uppercase tracking-tight text-black font-serif">
            Support the Project
          </h2>
          <p className="text-xs text-gray-500 mt-2 leading-relaxed">
            WC 2026 Predictor is built and maintained independently. Your support helps cover server costs and data API subscriptions to keep the engine running.
          </p>
        </div>

        {/* Payment Method Selectors */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {/* Crypto Method */}
          <button
            onClick={() => setActiveTab("crypto")}
            className={`flex items-center justify-center gap-2 p-3 border text-xs font-bold uppercase transition-none ${
              activeTab === "crypto"
                ? "border-black bg-black text-white"
                : "border-gray-200 text-black hover:border-black"
            }`}
          >
            <Wallet className="w-4 h-4" />
            Crypto Transfer
          </button>

          {/* Fiat Method (Disabled / Coming Soon) */}
          <div
            className="relative flex flex-col items-center justify-center p-3 border border-gray-100 bg-gray-50 text-gray-400 cursor-not-allowed group"
            title="Naira & USD Card/Bank payments are coming soon"
          >
            <div className="flex items-center gap-2 text-xs font-bold uppercase">
              <CreditCard className="w-4 h-4 text-gray-300" />
              Card / Bank
            </div>
            <span className="text-[8px] font-bold tracking-wider uppercase mt-1 bg-gray-200 text-gray-600 px-1 py-0.5 rounded-none">
              Coming Soon
            </span>
          </div>
        </div>

        {/* Crypto Donation Body */}
        {activeTab === "crypto" && (
          <div className="flex flex-col flex-1">
            {/* Step 1: Asset Selection */}
            <div className="mb-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400 block mb-2">
                1. Select Asset
              </span>
              <div className="flex gap-2">
                {ASSET_OPTIONS.map((asset) => (
                  <button
                    key={asset}
                    onClick={() => setSelectedAsset(asset)}
                    className={`px-4 py-1.5 border text-xs font-bold transition-none ${
                      selectedAsset === asset
                        ? "border-black bg-black text-white"
                        : "border-gray-200 text-black hover:border-black"
                    }`}
                  >
                    {asset}
                  </button>
                ))}
              </div>
            </div>

            {/* Step 2: Network Selection */}
            <div className="mb-5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400 block mb-2">
                2. Select Network
              </span>
              <div className="flex flex-wrap gap-2">
                {networks.map((net) => (
                  <button
                    key={net.name}
                    onClick={() => setSelectedNetwork(net)}
                    className={`px-3 py-1.5 border text-xs font-medium transition-none ${
                      selectedNetwork && selectedNetwork.name === net.name
                        ? "border-black bg-black text-white font-bold"
                        : "border-gray-200 text-black hover:border-black"
                    }`}
                  >
                    {net.displayName}
                  </button>
                ))}
              </div>
            </div>

            {/* QR Code and Address Area */}
            {selectedNetwork ? (
              <>
                <div className="border border-black p-4 bg-gray-50 flex flex-col items-center justify-center mb-4">
                  {/* QR Code */}
                  <div className="w-[180px] h-[180px] bg-white border border-gray-200 flex items-center justify-center relative mb-4">
                    {!qrLoaded && (
                      <div className="absolute inset-0 flex items-center justify-center bg-white">
                        <div className="w-5 h-5 border-2 border-black border-t-transparent animate-spin" />
                      </div>
                    )}
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={qrCodeUrl}
                      alt={`${selectedAsset} QR Code`}
                      width={180}
                      height={180}
                      onLoad={() => setQrLoaded(true)}
                      className={`transition-opacity duration-200 ${qrLoaded ? "opacity-100" : "opacity-0"}`}
                    />
                  </div>

                  {/* Monospace Address Display */}
                  <div className="w-full flex items-center gap-2">
                    <div className="flex-1 bg-white border border-gray-200 p-2 font-mono text-[10px] break-all select-all text-center leading-normal text-black font-semibold min-h-[36px] flex items-center justify-center">
                      {selectedNetwork.address}
                    </div>
                    <button
                      onClick={handleCopy}
                      className="p-2.5 border border-black bg-white hover:bg-black hover:text-white transition-none shrink-0"
                      title="Copy Address"
                    >
                      {copied ? (
                        <Check className="w-3.5 h-3.5 text-green-600 group-hover:text-white" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                  {copied ? (
                    <span className="text-[10px] text-green-600 font-bold mt-1.5 animate-pulse-subtle">
                      Copied address to clipboard!
                    </span>
                  ) : null}
                </div>

                {/* Network Alert Warning */}
                <div className="border border-[#ffcd00] bg-yellow-50/40 p-3 flex gap-2.5 items-start">
                  <AlertTriangle className="w-4 h-4 text-[#d97706] shrink-0 mt-0.5" />
                  <p className="text-[10px] leading-relaxed text-[#92400e] font-medium">
                    Please only send <strong className="font-bold">{selectedAsset}</strong> via the <strong className="font-bold">{selectedNetwork.displayName}</strong> network. Sending any other token or using a different network will result in permanent loss of funds.
                  </p>
                </div>
              </>
            ) : (
              <div className="border border-black p-6 bg-gray-50 flex flex-col items-center justify-center mb-4 text-center">
                <Wallet className="w-8 h-8 text-gray-400 mb-2" />
                <p className="text-xs text-gray-500 font-medium leading-relaxed">
                  No payment address configured. Please set environment variables for EVM, TRON, or Solana.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

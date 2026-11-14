"use client";

import { useState } from "react";
import { Sparkles, ChevronDown, ChevronUp, AlertTriangle, TrendingUp, Info } from "lucide-react";
import { toast } from "@/lib/toast";

interface AIInsightCardProps {
  ratioCode: string;
  ratioName: string;
  currentValue: string;
  band: string;
  dateFrom: string;
  dateTo: string;
}

interface AIExplanation {
  explanation: string;
  action: string;
  warning?: string;
  source: "llm" | "fallback" | "cache";
  llm_available: boolean;
  model?: string;
}

export function AIInsightCard({
  ratioCode,
  ratioName,
  currentValue,
  band,
  dateFrom,
  dateTo,
}: AIInsightCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [explanation, setExplanation] = useState<AIExplanation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchExplanation = async () => {
    if (explanation) {
      setIsExpanded(!isExpanded);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        from: dateFrom,
        to: dateTo,
      });

      const response = await fetch(
        `/api/v1/ratios/${ratioCode}/explain?${params}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${localStorage.getItem("access_token") || ""}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      
      setExplanation({
        explanation: data.explanation,
        action: data.action,
        warning: data.warning,
        source: data.source,
        llm_available: data.llm_available,
        model: data.model,
      });

      setIsExpanded(true);

      // Show success toast
      if (data.source === "llm") {
        toast.success(
          "AI Analisis Berhasil",
          `Insight dari ${data.model || "AI"} tersedia`
        );
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      setError(errorMessage);
      toast.error("Gagal Memuat Analisis", errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const getBandColor = (band: string) => {
    switch (band) {
      case "above_target":
        return "bg-green-50 border-green-200 text-green-700";
      case "between_target_warning":
        return "bg-yellow-50 border-yellow-200 text-yellow-700";
      case "between_warning_critical":
        return "bg-orange-50 border-orange-200 text-orange-700";
      case "below_critical":
        return "bg-red-50 border-red-200 text-red-700";
      default:
        return "bg-gray-50 border-gray-200 text-gray-700";
    }
  };

  const getBandIcon = (band: string) => {
    switch (band) {
      case "above_target":
        return <TrendingUp className="w-4 h-4" />;
      case "between_target_warning":
      case "between_warning_critical":
        return <AlertTriangle className="w-4 h-4" />;
      case "below_critical":
        return <AlertTriangle className="w-4 h-4 text-red-600" />;
      default:
        return <Info className="w-4 h-4" />;
    }
  };

  return (
    <div className={`rounded-lg border-2 p-4 transition-all ${getBandColor(band)}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {getBandIcon(band)}
          <div>
            <h3 className="font-semibold text-sm">{ratioName}</h3>
            <p className="text-xs opacity-75">
              Nilai saat ini: <span className="font-mono font-semibold">{currentValue}</span>
            </p>
          </div>
        </div>

        <button
          onClick={fetchExplanation}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-2 bg-white rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm font-medium"
        >
          <Sparkles className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          {loading ? "Loading..." : explanation ? "AI Insight" : "Analisis AI"}
          {explanation && (
            isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
          )}
        </button>
      </div>

      {error && (
        <div className="mt-3 p-3 bg-red-100 border border-red-300 rounded text-sm text-red-800">
          <strong>Error:</strong> {error}
        </div>
      )}

      {explanation && isExpanded && (
        <div className="mt-4 space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
          {/* Source Badge */}
          <div className="flex items-center gap-2 text-xs">
            <span className={`px-2 py-1 rounded-full ${
              explanation.source === "llm" 
                ? "bg-purple-100 text-purple-700" 
                : explanation.source === "cache"
                ? "bg-blue-100 text-blue-700"
                : "bg-gray-100 text-gray-700"
            }`}>
              {explanation.source === "llm" ? `🤖 AI (${explanation.model})` : 
               explanation.source === "cache" ? "⚡ Cached" : 
               "📋 Fallback"}
            </span>
          </div>

          {/* Explanation */}
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
              <Info className="w-4 h-4" />
              Penjelasan Kondisi
            </h4>
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
              {explanation.explanation}
            </p>
          </div>

          {/* Action Recommendation */}
          {explanation.action && (
            <div className="bg-white p-4 rounded-lg shadow-sm border border-blue-200">
              <h4 className="font-semibold text-sm mb-2 flex items-center gap-2 text-blue-700">
                <TrendingUp className="w-4 h-4" />
                Rekomendasi Tindakan
              </h4>
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
                {explanation.action}
              </p>
            </div>
          )}

          {/* Warning */}
          {explanation.warning && (
            <div className="bg-amber-50 p-4 rounded-lg border border-amber-200">
              <h4 className="font-semibold text-sm mb-2 flex items-center gap-2 text-amber-700">
                <AlertTriangle className="w-4 h-4" />
                Peringatan
              </h4>
              <p className="text-sm text-amber-800 leading-relaxed">
                {explanation.warning}
              </p>
            </div>
          )}

          {/* Disclaimer */}
          <p className="text-xs text-gray-500 italic">
            * Narasi ini bersifat informatif, bukan saran keuangan profesional.
          </p>
        </div>
      )}
    </div>
  );
}

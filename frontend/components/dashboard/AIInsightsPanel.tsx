"use client";

import { useState } from "react";
import { AIInsightCard } from "./AIInsightCard";
import { useRatioInsights } from "@/hooks/use-ratio-insights";
import { Sparkles, RefreshCw, Calendar } from "lucide-react";

interface AIInsightsPanelProps {
  initialDateFrom?: string;
  initialDateTo?: string;
}

export function AIInsightsPanel({
  initialDateFrom,
  initialDateTo,
}: AIInsightsPanelProps) {
  // Default to current month
  const today = new Date();
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
  const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);

  const [dateFrom, setDateFrom] = useState(
    initialDateFrom || firstDay.toISOString().split("T")[0]
  );
  const [dateTo, setDateTo] = useState(
    initialDateTo || lastDay.toISOString().split("T")[0]
  );

  const { insights, loading, error, refetch } = useRatioInsights({
    dateFrom,
    dateTo,
    autoFetch: true,
  });

  // Filter only critical/warning ratios for AI insights
  const criticalInsights = insights.filter(
    (insight) =>
      insight.band === "below_critical" ||
      insight.band === "between_warning_critical" ||
      insight.band === "between_target_warning"
  );

  // All insights for overview
  const allInsights = insights;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Sparkles className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              AI Financial Insights
            </h2>
            <p className="text-sm text-gray-600">
              Analisis cerdas kondisi keuangan bisnis Anda
            </p>
          </div>
        </div>

        <button
          onClick={() => refetch()}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Date Range Filter */}
      <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <div className="flex items-center gap-4">
          <Calendar className="w-5 h-5 text-gray-500" />
          <div className="flex items-center gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Dari
              </label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Sampai
              </label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 animate-spin text-purple-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Memuat data rasio...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">
            <strong>Error:</strong> {error}
          </p>
        </div>
      )}

      {/* Critical Insights Section */}
      {!loading && !error && criticalInsights.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            🚨 Perlu Perhatian Segera ({criticalInsights.length})
          </h3>
          <div className="grid gap-4">
            {criticalInsights.map((insight) => (
              <AIInsightCard
                key={insight.ratio_code}
                ratioCode={insight.ratio_code}
                ratioName={insight.ratio_name}
                currentValue={insight.value || "N/A"}
                band={insight.band}
                dateFrom={dateFrom}
                dateTo={dateTo}
              />
            ))}
          </div>
        </div>
      )}

      {/* All Ratios Overview */}
      {!loading && !error && allInsights.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            📊 Semua Rasio Keuangan ({allInsights.length})
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {allInsights.map((insight) => (
              <AIInsightCard
                key={insight.ratio_code}
                ratioCode={insight.ratio_code}
                ratioName={insight.ratio_name}
                currentValue={insight.value || "N/A"}
                band={insight.band}
                dateFrom={dateFrom}
                dateTo={dateTo}
              />
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && allInsights.length === 0 && (
        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
          <Sparkles className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-gray-700 mb-1">
            Belum Ada Data
          </h3>
          <p className="text-sm text-gray-600">
            Masukkan transaksi terlebih dahulu untuk melihat analisis rasio keuangan.
          </p>
        </div>
      )}
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { TrendingUp, TrendingDown, Minus, AlertTriangle, Activity, RefreshCw } from "lucide-react";
import { toast } from "@/lib/toast";
import { apiClient, getErrorMessage } from "@/lib/api-client";

interface PredictiveSeries {
  code: string;
  name: string;
  category: string;
  unit: string;
  status: string;
  points: number;
  current: string;
  projected: string;
  horizon: number;
  trend: "up" | "down" | "flat";
  risk: boolean;
  note: string;
  method: string;
}

interface PredictiveData {
  horizon: number;
  min_points: number;
  method: string;
  series: PredictiveSeries[];
}

interface PredictiveInsightsPanelProps {
  dateFrom: string;
  dateTo: string;
}

export function PredictiveInsightsPanel({
  dateFrom,
  dateTo,
}: PredictiveInsightsPanelProps) {
  const [predictive, setPredictive] = useState<PredictiveData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPredictiveInsights = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = {
        from: dateFrom,
        to: dateTo,
      };

      const response = await apiClient.get("/ratio-insights", { params });
      const data = response.data;
      setPredictive(data.predictive);
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      toast.error("Gagal Memuat Prediksi", errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (dateFrom && dateTo) {
      fetchPredictiveInsights();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateFrom, dateTo]);

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "up":
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case "down":
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <Minus className="w-4 h-4 text-gray-600" />;
    }
  };

  const getTrendColor = (trend: string, risk: boolean) => {
    if (risk) return "text-red-700 bg-red-50 border-red-200";
    switch (trend) {
      case "up":
        return "text-green-700 bg-green-50 border-green-200";
      case "down":
        return "text-orange-700 bg-orange-50 border-orange-200";
      default:
        return "text-gray-700 bg-gray-50 border-gray-200";
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "Likuiditas":
        return "bg-blue-100 text-blue-800";
      case "Solvabilitas":
        return "bg-purple-100 text-purple-800";
      case "Aktivitas":
        return "bg-yellow-100 text-yellow-800";
      case "Profitabilitas":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-6 border border-[#e5e5e5] shadow-sm">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 animate-spin text-purple-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Memuat prediksi trend...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-2xl p-6 border border-[#e5e5e5] shadow-sm">
        <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">
            <strong>Error:</strong> {error}
          </p>
        </div>
      </div>
    );
  }

  if (!predictive || predictive.series.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-6 border border-[#e5e5e5] shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Activity className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              Prediksi Trend Rasio
            </h2>
            <p className="text-sm text-gray-600">
              Proyeksi berbasis analisis historis
            </p>
          </div>
        </div>
        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <Activity className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-sm text-gray-600">
            Belum cukup data historis untuk membuat prediksi.
            <br />
            Minimal {predictive?.min_points || 3} periode data diperlukan.
          </p>
        </div>
      </div>
    );
  }

  // Separate available and insufficient
  const availablePredictions = predictive.series.filter(
    (s) => s.status === "available"
  );
  const insufficientPredictions = predictive.series.filter(
    (s) => s.status === "insufficient"
  );

  // Risk predictions first
  const riskPredictions = availablePredictions.filter((s) => s.risk);
  const normalPredictions = availablePredictions.filter((s) => !s.risk);

  return (
    <div className="bg-white rounded-2xl p-6 border border-[#e5e5e5] shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Activity className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              Prediksi Trend Rasio (Predictive AI)
            </h2>
            <p className="text-sm text-gray-600">
              Proyeksi {predictive.horizon} periode ke depan menggunakan{" "}
              {predictive.method}
            </p>
          </div>
        </div>
        <button
          onClick={fetchPredictiveInsights}
          className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-all text-sm font-medium"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Risk Predictions */}
      {riskPredictions.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-red-700 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Proyeksi Berisiko ({riskPredictions.length})
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {riskPredictions.map((series) => (
              <div
                key={series.code}
                className={`rounded-lg border-2 p-4 ${getTrendColor(series.trend, series.risk)}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`text-xs font-bold px-2 py-0.5 rounded ${getCategoryColor(series.category)}`}
                      >
                        {series.category}
                      </span>
                      {getTrendIcon(series.trend)}
                    </div>
                    <h4 className="font-semibold text-sm">{series.name}</h4>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div>
                    <p className="text-xs text-gray-600">Saat Ini</p>
                    <p className="text-lg font-bold">
                      {series.current} {series.unit}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Proyeksi</p>
                    <p className="text-lg font-bold">
                      {series.projected} {series.unit}
                    </p>
                  </div>
                </div>

                <div className="bg-white bg-opacity-60 rounded p-2">
                  <p className="text-xs font-medium leading-relaxed">
                    {series.note}
                  </p>
                </div>

                <div className="mt-2 text-[10px] text-gray-500">
                  Berdasarkan {series.points} periode historis
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Normal Predictions */}
      {normalPredictions.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            Proyeksi Normal ({normalPredictions.length})
          </h3>
          <div className="grid gap-4 md:grid-cols-3">
            {normalPredictions.map((series) => (
              <div
                key={series.code}
                className={`rounded-lg border p-3 ${getTrendColor(series.trend, false)}`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className={`text-xs font-bold px-2 py-0.5 rounded ${getCategoryColor(series.category)}`}
                  >
                    {series.category}
                  </span>
                  {getTrendIcon(series.trend)}
                </div>
                <h4 className="font-semibold text-sm mb-2">{series.name}</h4>

                <div className="flex items-baseline gap-2 mb-1">
                  <span className="text-xs text-gray-600">Saat ini:</span>
                  <span className="font-mono font-semibold text-sm">
                    {series.current} {series.unit}
                  </span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-xs text-gray-600">Proyeksi:</span>
                  <span className="font-mono font-semibold text-sm">
                    {series.projected} {series.unit}
                  </span>
                </div>

                <div className="mt-2 text-[10px] text-gray-500">
                  {series.points} periode data
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Insufficient Data Notice */}
      {insufficientPredictions.length > 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-700 mb-2">
            <strong>Catatan:</strong> {insufficientPredictions.length} rasio
            belum dapat diproyeksikan karena data historis kurang dari{" "}
            {predictive.min_points} periode.
          </p>
          <p className="text-xs text-gray-600">
            Rasio: {insufficientPredictions.map((s) => s.code).join(", ")}
          </p>
        </div>
      )}

      {/* Disclaimer */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500 italic">
          * Proyeksi menggunakan metode {predictive.method} berbasis data
          historis. Proyeksi bukan jaminan hasil di masa depan dan bersifat
          indikatif untuk perencanaan.
        </p>
      </div>
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { Bell, Clock, AlertCircle, CheckCircle2, AlertTriangle, TrendingDown } from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface Alert {
  code: string;
  category: string;
  category_label: string;
  level: "critical" | "warning";
  title: string;
  message: string;
  ratio_codes: string[];
  direction: string;
  evidence: string[];
  timestamp?: string;
}

interface AlertHistoryPanelProps {
  dateFrom: string;
  dateTo: string;
}

export function AlertHistoryPanel({
  dateFrom,
  dateTo,
}: AlertHistoryPanelProps) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchAlerts = async () => {
      setLoading(true);
      try {
        const params = {
          from: dateFrom,
          to: dateTo,
        };

        const response = await apiClient.get("/ratio-insights", { params });
        const data = response.data;
        
        const alertsWithTimestamp = (data.alerts || []).map((alert: Alert) => ({
          ...alert,
          timestamp: new Date().toISOString(),
        }));
        setAlerts(alertsWithTimestamp);
      } catch (error) {
        console.error("Failed to fetch alerts:", error);
      } finally {
        setLoading(false);
      }
    };

    if (dateFrom && dateTo) {
      fetchAlerts();
    }
  }, [dateFrom, dateTo]);

  const getLevelIcon = (level: string) => {
    switch (level) {
      case "critical":
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      case "warning":
        return <AlertTriangle className="w-5 h-5 text-amber-600" />;
      default:
        return <Bell className="w-5 h-5 text-blue-600" />;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case "critical":
        return "bg-red-50 border-red-200 text-red-900";
      case "warning":
        return "bg-amber-50 border-amber-200 text-amber-900";
      default:
        return "bg-blue-50 border-blue-200 text-blue-900";
    }
  };

  const getCategoryBadgeColor = (category: string) => {
    switch (category) {
      case "liquidity":
        return "bg-blue-100 text-blue-800";
      case "solvency":
        return "bg-purple-100 text-purple-800";
      case "activity":
        return "bg-yellow-100 text-yellow-800";
      case "profitability":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-6 border border-[#e5e5e5] shadow-sm">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-100 rounded"></div>
            <div className="h-20 bg-gray-100 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl p-6 border border-[#e5e5e5] shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-orange-100 rounded-lg">
            <Bell className="w-6 h-6 text-orange-600" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Riwayat Peringatan</h2>
            <p className="text-sm text-gray-600">
              Alert yang terdeteksi pada periode ini
            </p>
          </div>
        </div>
        {alerts.length > 0 && (
          <span className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm font-semibold">
            {alerts.length} Alert
          </span>
        )}
      </div>

      {/* Alerts List */}
      {alerts.length === 0 ? (
        <div className="bg-green-50 border-2 border-dashed border-green-300 rounded-lg p-8 text-center">
          <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-green-800 mb-1">
            Tidak Ada Peringatan
          </h3>
          <p className="text-sm text-green-700">
            Semua rasio keuangan dalam kondisi baik pada periode ini.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert, index) => (
            <div
              key={`${alert.code}-${index}`}
              className={`rounded-lg border-2 p-4 ${getLevelColor(alert.level)}`}
            >
              <div className="flex items-start gap-3">
                {getLevelIcon(alert.level)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-semibold text-sm">{alert.title}</h3>
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded ${getCategoryBadgeColor(alert.category)}`}
                    >
                      {alert.category_label}
                    </span>
                    {alert.direction === "down" && (
                      <TrendingDown className="w-4 h-4 text-red-600" />
                    )}
                  </div>

                  <p className="text-sm leading-relaxed mb-3">{alert.message}</p>

                  {alert.evidence && alert.evidence.length > 0 && (
                    <div className="bg-white bg-opacity-60 rounded p-3 mb-2">
                      <p className="text-xs font-semibold text-gray-700 mb-1">
                        Evidence:
                      </p>
                      <ul className="space-y-1">
                        {alert.evidence.map((ev, idx) => (
                          <li
                            key={idx}
                            className="text-xs text-gray-700 flex items-start gap-2"
                          >
                            <span className="text-gray-400">•</span>
                            <span>{ev}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="flex items-center gap-2 text-xs text-gray-600">
                    <Clock className="w-3 h-3" />
                    <span>
                      Rasio terdampak: {alert.ratio_codes.join(", ")}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Footer Note */}
      {alerts.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            💡 <strong>Tip:</strong> Klik "Analisis AI" pada rasio terkait untuk
            mendapat rekomendasi tindakan detail.
          </p>
        </div>
      )}
    </div>
  );
}

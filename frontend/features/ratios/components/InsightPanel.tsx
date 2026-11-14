"use client";

import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import type {
  PredictiveSeries,
  RatioAlert,
  RatioInsightsResponse,
  RatioPrescriptive,
} from "@/types/ratios";
import {
  AlertTriangle,
  BellRing,
  CheckCircle2,
  Info,
  ListChecks,
  Minus,
  Sparkles,
  TrendingDown,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import { formatRatioValue } from "../ratio-format";

interface InsightPanelProps {
  insights?: RatioInsightsResponse;
  isLoading: boolean;
  error?: string;
  onRetry?: () => void;
}

const PRIORITY_LABEL: Record<RatioPrescriptive["priority"], string> = {
  high: "Prioritas tinggi",
  medium: "Prioritas sedang",
  low: "Prioritas rendah",
};

const PRIORITY_VARIANT: Record<
  RatioPrescriptive["priority"],
  "error" | "warning" | "default"
> = {
  high: "error",
  medium: "warning",
  low: "default",
};

function SectionHeading({
  icon: Icon,
  title,
  description,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
}) {
  return (
    <div className="mb-3 flex items-start gap-2.5">
      <span className="mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg bg-[#FAF7F2] text-[#273420]">
        <Icon className="h-4 w-4" />
      </span>
      <div>
        <h3 className="text-sm font-bold text-[#1F241D]">{title}</h3>
        <p className="text-[11px] leading-relaxed text-[#9A9F94]">
          {description}
        </p>
      </div>
    </div>
  );
}

function AlertCard({ alert }: { alert: RatioAlert }) {
  const isCritical = alert.level === "critical";

  return (
    <div
      className={cn(
        "rounded-2xl border border-l-4 bg-white p-4",
        isCritical
          ? "border-red-200/70 border-l-red-500"
          : "border-amber-200/70 border-l-amber-500",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="flex items-center gap-2 text-sm font-bold text-[#1F241D]">
          <AlertTriangle
            className={cn(
              "h-4 w-4 flex-shrink-0",
              isCritical ? "text-red-500" : "text-amber-500",
            )}
          />
          {alert.title}
        </p>
        <Badge variant={isCritical ? "error" : "warning"}>
          {isCritical ? "Kritis" : "Perlu dipantau"}
        </Badge>
      </div>
      <p className="mt-2 text-xs leading-relaxed text-[#666A61]">
        {alert.message}
      </p>
      <p className="mt-2 text-[10px] font-medium uppercase tracking-wide text-[#A0A59B]">
        Rasio: {alert.ratio_codes.join(", ")}
      </p>
    </div>
  );
}

function PredictiveCard({ series }: { series: PredictiveSeries }) {
  if (series.status === "insufficient") {
    return (
      <div className="rounded-2xl border border-[#EBE5DC]/70 bg-[#FAF7F2]/60 p-4">
        <div className="flex items-center justify-between gap-2">
          <p className="text-xs font-bold text-[#4C5348]">{series.name}</p>
          <Badge variant="default">Data belum cukup</Badge>
        </div>
        <p className="mt-2 text-[11px] leading-relaxed text-[#9A9F94]">
          {series.reason}
        </p>
      </div>
    );
  }

  const TrendIcon =
    series.trend === "up" ? TrendingUp : series.trend === "down" ? TrendingDown : Minus;
  const trendClass =
    series.trend === "up"
      ? "text-emerald-600"
      : series.trend === "down"
        ? "text-red-500"
        : "text-[#9A9F94]";

  return (
    <div
      className={cn(
        "rounded-2xl border bg-white p-4",
        series.risk ? "border-amber-300/80" : "border-[#EBE5DC]/70",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-bold text-[#4C5348]">{series.name}</p>
        {series.risk ? (
          <Badge variant="warning">Risiko</Badge>
        ) : (
          <Badge variant="success">Aman</Badge>
        )}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-lg font-bold text-[#1F241D]">
          {formatRatioValue(series.current, series.unit)}
        </span>
        <span className={cn("flex items-center gap-1 text-xs font-semibold", trendClass)}>
          <TrendIcon className="h-3.5 w-3.5" />
          {formatRatioValue(series.projected, series.unit)}
        </span>
      </div>
      <p className="mt-1 text-[10px] text-[#A0A59B]">
        Proyeksi {series.horizon} periode ke depan · {series.points} titik data
      </p>
      <p className="mt-2 text-[11px] leading-relaxed text-[#666A61]">
        {series.note}
      </p>
    </div>
  );
}

function PrescriptiveCard({ item }: { item: RatioPrescriptive }) {
  return (
    <div className="rounded-2xl border border-[#EBE5DC]/70 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-bold text-[#1F241D]">{item.title}</p>
        <Badge variant={PRIORITY_VARIANT[item.priority]}>
          {PRIORITY_LABEL[item.priority]}
        </Badge>
      </div>
      <ul className="mt-3 space-y-2">
        {item.suggested_actions.map((action, index) => (
          <li
            key={index}
            className="flex items-start gap-2 text-xs leading-relaxed text-[#666A61]"
          >
            <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-emerald-500" />
            <span>{action}</span>
          </li>
        ))}
      </ul>
      {item.limitations.length > 0 && (
        <p className="mt-3 text-[10px] leading-relaxed text-[#A0A59B]">
          {item.limitations.join(" ")}
        </p>
      )}
    </div>
  );
}

export function InsightPanel({
  insights,
  isLoading,
  error,
  onRetry,
}: InsightPanelProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {[0, 1, 2].map((item) => (
          <div
            key={item}
            className="h-40 animate-pulse rounded-2xl border border-[#EBE5DC]/70 bg-white"
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="error" title="Analisis AI gagal dimuat">
        <p>{error}</p>
        {onRetry && (
          <Button
            type="button"
            variant="secondary"
            size="sm"
            className="mt-3"
            onClick={onRetry}
          >
            Coba lagi
          </Button>
        )}
      </Alert>
    );
  }

  if (!insights) return null;

  const predictiveSeries = insights.predictive.series;
  const hasEnoughHistory = insights.history_points >= insights.predictive.min_points;

  return (
    <section className="rounded-2xl border border-[#EBE5DC]/70 bg-gradient-to-br from-white to-[#FAF7F2] p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-violet-500" />
          <h2 className="text-base font-bold text-[#1F241D]">Analisis AI</h2>
        </div>
        <span className="font-mono text-[10px] text-[#A0A59B]">
          rules v{insights.rules_version} · {insights.history_points} titik riwayat
        </span>
      </div>

      <div className="space-y-6">
        {/* Descriptive → notifikasi/alert */}
        <div>
          <SectionHeading
            icon={BellRing}
            title="Peringatan dini"
            description="Perubahan arah rasio dibanding periode sebelumnya. Angka dihitung engine deterministik."
          />
          {insights.alerts.length > 0 ? (
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
              {insights.alerts.map((alert) => (
                <AlertCard key={alert.code} alert={alert} />
              ))}
            </div>
          ) : (
            <div className="flex items-start gap-2 rounded-2xl border border-emerald-200/70 bg-emerald-50/60 p-4">
              <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-600" />
              <p className="text-xs leading-relaxed text-emerald-900">
                {insights.has_previous_period
                  ? "Tidak ada rasio yang memburuk signifikan dibanding periode sebelumnya."
                  : "Belum ada periode pembanding. Peringatan akan muncul setelah ada snapshot neraca periode sebelumnya."}
              </p>
            </div>
          )}
        </div>

        {/* Predictive → proyeksi tren */}
        <div>
          <SectionHeading
            icon={TrendingUp}
            title="Proyeksi tren"
            description="Ekstrapolasi linear sederhana dari riwayat rasio. Indikatif, bukan jaminan."
          />
          {predictiveSeries.length > 0 ? (
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-2 xl:grid-cols-3">
              {predictiveSeries.map((series) => (
                <PredictiveCard key={series.code} series={series} />
              ))}
            </div>
          ) : (
            <div className="flex items-start gap-2 rounded-2xl border border-[#EBE5DC]/70 bg-white p-4">
              <Info className="mt-0.5 h-4 w-4 flex-shrink-0 text-[#7E8379]" />
              <p className="text-xs leading-relaxed text-[#666A61]">
                {hasEnoughHistory
                  ? "Tidak ada rasio kunci dengan data proyeksi pada periode ini."
                  : `Butuh minimal ${insights.predictive.min_points} periode snapshot rasio untuk menampilkan proyeksi. Tersedia ${insights.history_points} titik.`}
              </p>
            </div>
          )}
        </div>

        {/* Prescriptive → rekomendasi tindakan */}
        <div>
          <SectionHeading
            icon={ListChecks}
            title="Rekomendasi tindakan"
            description="Langkah konkret untuk rasio yang berada di bawah target."
          />
          {insights.prescriptive.length > 0 ? (
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
              {insights.prescriptive.map((item) => (
                <PrescriptiveCard key={item.rule_id} item={item} />
              ))}
            </div>
          ) : (
            <div className="flex items-start gap-2 rounded-2xl border border-emerald-200/70 bg-emerald-50/60 p-4">
              <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-600" />
              <p className="text-xs leading-relaxed text-emerald-900">
                Semua rasio berada pada atau di atas target. Tidak ada tindakan
                perbaikan yang mendesak untuk periode ini.
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

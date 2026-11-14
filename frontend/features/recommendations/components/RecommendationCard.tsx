"use client";

import type {
  Recommendation,
  RecommendationExplanation,
} from "@/types/financial";
import {
  Lightbulb,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/Button";

interface RecommendationCardProps {
  recommendation: Recommendation;
  canAct?: boolean;
  onMarkDone?: (id: string) => void;
  onExplain?: (id: string) => void;
  explanation?: RecommendationExplanation;
  isExplaining?: boolean;
  explainError?: string;
}

const priorityColorMap = {
  low: "bg-blue-100 text-blue-800 border-blue-300",
  medium: "bg-yellow-100 text-yellow-800 border-yellow-300",
  high: "bg-red-100 text-red-800 border-red-300",
};

const priorityLabelMap = {
  low: "Rendah",
  medium: "Sedang",
  high: "Tinggi",
};

export function RecommendationCard({
  recommendation,
  onMarkDone,
  onExplain,
  explanation,
  isExplaining = false,
  explainError,
}: RecommendationCardProps) {
  const { id, title, priority, evidence, suggested_actions, assumptions, limitations, status } = recommendation;

  return (
    <div className="bg-white rounded-2xl border border-gray-200/60 shadow-premium p-6 space-y-5 hover:border-emerald-200 hover:shadow-md transition-all">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          <div className="w-11 h-11 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm">
            <Lightbulb className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 leading-snug">
              {title}
            </h3>
            {recommendation.period && (
              <p className="text-xs text-gray-600 mt-1">
                Periode: {recommendation.period.from} - {recommendation.period.to}
              </p>
            )}
            <p className="text-xs text-gray-500 mt-0.5">
              Dibuat: {new Date(recommendation.created_at).toLocaleDateString("id-ID")}
            </p>
          </div>
        </div>
        <span
          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${priorityColorMap[priority]}`}
        >
          {priorityLabelMap[priority]}
        </span>
      </div>

      {isExplaining && (
        <div className="flex items-center gap-2 rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Menyiapkan penjelasan...</span>
        </div>
      )}

      {explainError && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Gagal memuat penjelasan: {explainError}
        </div>
      )}

      {explanation && (
        <div className="p-4 bg-gray-50 rounded-xl border border-gray-200/60 shadow-sm space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center rounded-full border border-gray-300 bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-gray-700">
              {explanation.source === "llm" ? "Narasi LLM" : "Narasi Rule-based"}
            </span>
            <span className="text-[11px] text-gray-500">
              {explanation.llm_enabled
                ? explanation.llm_available
                  ? "LLM aktif"
                  : "LLM fallback"
                : "LLM nonaktif"}
            </span>
          </div>
          <p className="text-sm text-gray-900 leading-relaxed">
            {explanation.explanation}
          </p>
          {explanation.fallback_reason && (
            <p className="text-xs text-amber-700">
              Alasan fallback: {explanation.fallback_reason}
            </p>
          )}
          {explanation.privacy_note && (
            <p className="text-xs text-gray-500">{explanation.privacy_note}</p>
          )}
          {explanation.disclaimer && (
            <p className="text-[11px] text-gray-400">{explanation.disclaimer}</p>
          )}
        </div>
      )}

      <div className="space-y-4">
        <div>
          <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Evidence / Bukti</span>
          </h4>
          <ul className="space-y-1.5">
            {evidence.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-gray-900">
                <span className="text-emerald-600 mt-1">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Tindakan yang Disarankan</span>
          </h4>
          <ol className="space-y-2">
            {suggested_actions.map((action, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-sm text-gray-900">
                <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-gradient-to-br from-emerald-600 to-emerald-700 text-white text-xs font-semibold flex-shrink-0 mt-0.5 shadow-sm">
                  {idx + 1}
                </span>
                <span>{action}</span>
              </li>
            ))}
          </ol>
        </div>

        {(assumptions.length > 0 || limitations.length > 0) && (
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-xl space-y-3">
            {assumptions.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-yellow-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>Asumsi</span>
                </h4>
                <ul className="space-y-1">
                  {assumptions.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-xs text-yellow-800">
                      <span className="mt-1">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {limitations.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-yellow-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>Keterbatasan</span>
                </h4>
                <ul className="space-y-1">
                  {limitations.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-xs text-yellow-800">
                      <span className="mt-1">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {status === "active" && onMarkDone && (
        <div className="flex gap-3 pt-2">
          <Button
            variant="primary"
            size="sm"
            onClick={() => onMarkDone(id)}
            className="flex-1"
          >
            Tandai Selesai
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onExplain?.(id)}
            disabled={isExplaining || !onExplain}
          >
            {isExplaining
              ? "Memuat..."
              : explanation
                ? "Muat Ulang Penjelasan"
                : "Jelaskan"}
          </Button>
        </div>
      )}

      {status === "reviewed" && (
        <div className="flex items-center gap-2 text-sm text-emerald-700 pt-2">
          <CheckCircle2 className="w-4 h-4" />
          <span className="font-medium">Sudah ditinjau</span>
        </div>
      )}
    </div>
  );
}

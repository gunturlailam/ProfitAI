import { useState, useEffect } from "react";
import { toast } from "@/lib/toast";
import { apiClient, getErrorMessage } from "@/lib/api-client";

interface RatioInsight {
  ratio_code: string;
  ratio_name: string;
  category: string;
  value: string | null;
  band: string;
  quality: string;
  explanation?: string;
  action?: string;
  warning?: string;
  source?: "llm" | "fallback" | "cache";
  llm_available?: boolean;
  model?: string;
}

interface UseRatioInsightsOptions {
  dateFrom: string;
  dateTo: string;
  asOf?: string;
  autoFetch?: boolean;
}

interface UseRatioInsightsReturn {
  insights: RatioInsight[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  explainRatio: (ratioCode: string) => Promise<RatioInsight | null>;
}

export function useRatioInsights(
  options: UseRatioInsightsOptions
): UseRatioInsightsReturn {
  const { dateFrom, dateTo, asOf, autoFetch = true } = options;
  const [insights, setInsights] = useState<RatioInsight[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRatios = async () => {
    setLoading(true);
    setError(null);

    try {
      const params: Record<string, string> = {
        from: dateFrom,
        to: dateTo,
      };

      if (asOf) {
        params.as_of = asOf;
      }

      const response = await apiClient.get("/ratios", { params });
      const data = response.data;

      // Transform API response to insights format
      const ratioInsights: RatioInsight[] = (data.ratios || []).map((ratio: any) => ({
        ratio_code: ratio.code,
        ratio_name: ratio.name,
        category: ratio.category,
        value: ratio.value,
        band: ratio.band,
        quality: ratio.quality,
      }));

      setInsights(ratioInsights);
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      toast.error("Gagal Memuat Rasio", errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const explainRatio = async (ratioCode: string): Promise<RatioInsight | null> => {
    try {
      const params: Record<string, string> = {
        from: dateFrom,
        to: dateTo,
      };

      if (asOf) {
        params.as_of = asOf;
      }

      const response = await apiClient.post(`/ratios/${ratioCode}/explain`, {}, { params });
      const data = response.data;

      // Update insight in state
      setInsights((prev) =>
        prev.map((insight) =>
          insight.ratio_code === ratioCode
            ? {
                ...insight,
                explanation: data.explanation,
                action: data.action,
                warning: data.warning,
                source: data.source,
                llm_available: data.llm_available,
                model: data.model,
              }
            : insight
        )
      );

      return {
        ratio_code: data.ratio_code,
        ratio_name: data.ratio_name,
        category: data.category,
        value: data.value,
        band: data.band,
        quality: data.quality,
        explanation: data.explanation,
        action: data.action,
        warning: data.warning,
        source: data.source,
        llm_available: data.llm_available,
        model: data.model,
      };
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      toast.error("Gagal Memuat Analisis AI", errorMessage);
      return null;
    }
  };

  const refetch = async () => {
    await fetchRatios();
  };

  useEffect(() => {
    if (autoFetch && dateFrom && dateTo) {
      fetchRatios();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateFrom, dateTo, asOf, autoFetch]);

  return {
    insights,
    loading,
    error,
    refetch,
    explainRatio,
  };
}

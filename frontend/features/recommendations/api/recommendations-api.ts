import { apiClient } from "@/lib/api-client";
import type {
  RecommendationsResponse,
  FinancialQueryParams,
} from "@/types/api";
import type { RecommendationExplanation } from "@/types/financial";

export const recommendationsApi = {
  getRecommendations: async (
    params: FinancialQueryParams,
    options?: { persist?: boolean },
  ): Promise<RecommendationsResponse> => {
    const { data } = await apiClient.get<RecommendationsResponse>("/recommendations", {
      params: {
        from: params.from,
        to: params.to,
        // Persistensi histori harus eksplisit. Viewer tidak boleh menulis,
        // jadi halaman meminta `persist=false` untuk role read-only.
        persist: options?.persist ?? true,
      },
    });

    // Periode berasal dari backend. Jangan menempelkan periode request ke
    // record lama karena itu membuat evidence basi terlihat milik periode baru.
    return data;
  },

  explainRecommendation: async (
    id: string,
  ): Promise<RecommendationExplanation> => {
    const { data } = await apiClient.post<RecommendationExplanation>(
      `/recommendations/${id}/explain`,
    );
    return data;
  },
};

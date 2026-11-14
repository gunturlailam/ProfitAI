import { apiClient } from "@/lib/api-client";
import { recommendationsApi } from "@/features/recommendations/api/recommendations-api";

jest.mock("@/lib/api-client", () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

const mockedGet = apiClient.get as jest.Mock;
const mockedPost = apiClient.post as jest.Mock;

describe("recommendationsApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("requests persisted, backend-scoped recommendations", async () => {
    const response = {
      recommendations: [
        {
          id: "12",
          rule_id: "RULE-EXP-01",
          period: { from: "2026-01-01", to: "2026-01-31" },
          title: "Evaluasi beban",
          priority: "medium",
          evidence: ["Beban tinggi"],
          suggested_actions: [],
          assumptions: [],
          limitations: [],
          status: "active",
          created_at: "2026-01-31T00:00:00Z",
        },
      ],
      period: { from: "2026-01-01", to: "2026-01-31" },
      generated_at: "2026-01-31T00:00:00Z",
    };
    mockedGet.mockResolvedValueOnce({ data: response });

    const result = await recommendationsApi.getRecommendations({
      from: "2026-01-01",
      to: "2026-01-31",
    });

    expect(mockedGet).toHaveBeenCalledWith("/recommendations", {
      params: {
        from: "2026-01-01",
        to: "2026-01-31",
        persist: true,
      },
    });
    expect(result).toEqual(response);
  });

  it("does not overwrite a missing period with the request period", async () => {
    mockedGet.mockResolvedValueOnce({
      data: {
        recommendations: [
          {
            id: null,
            rule_id: "RULE-CF-01",
            title: "Likuiditas",
            priority: "high",
            evidence: [],
            suggested_actions: [],
            assumptions: [],
            limitations: [],
            status: "active",
            created_at: "2026-01-31T00:00:00Z",
          },
        ],
        period: { from: "2026-01-01", to: "2026-01-31" },
        generated_at: "2026-01-31T00:00:00Z",
      },
    });

    const result = await recommendationsApi.getRecommendations({
      from: "2026-01-01",
      to: "2026-01-31",
    });

    expect(result.recommendations[0].period).toBeUndefined();
  });

  it("calls the explain endpoint without sending financial payloads", async () => {
    mockedPost.mockResolvedValueOnce({
      data: {
        recommendation_id: 12,
        rule_id: "RULE-EXP-01",
        title: "Evaluasi beban",
        explanation: "Beban perlu ditinjau.",
        source: "fallback",
        llm_enabled: false,
        llm_available: false,
        fallback_reason: "GEMINI_API_KEY belum dikonfigurasi.",
      },
    });

    const result = await recommendationsApi.explainRecommendation("12");

    expect(mockedPost).toHaveBeenCalledWith("/recommendations/12/explain");
    expect(result.source).toBe("fallback");
  });
});

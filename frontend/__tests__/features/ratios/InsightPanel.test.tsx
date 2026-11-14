import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { InsightPanel } from "@/features/ratios/components/InsightPanel";
import type { RatioInsightsResponse } from "@/types/ratios";

function makeInsights(
  overrides: Partial<RatioInsightsResponse> = {},
): RatioInsightsResponse {
  return {
    period: { from: "2026-10-01", to: "2026-10-31" },
    as_of: "2026-10-31",
    currency: "IDR",
    formula_version: "1.1.0",
    rules_version: "1.0.0",
    has_previous_period: true,
    history_points: 4,
    alerts: [
      {
        code: "ALERT_LIQUIDITY_DOWN",
        category: "liquidity",
        category_label: "Likuiditas",
        level: "warning",
        title: "Likuiditas berubah ke arah kurang sehat",
        message: "Likuiditas jangka pendek menurun.",
        ratio_codes: ["CR"],
        direction: "down",
        rule_version: "1.0.0",
        evidence: ["CR bergerak ke arah kurang sehat."],
      },
    ],
    predictive: {
      horizon: 1,
      min_points: 3,
      method: "linear_trend_v1",
      series: [
        {
          code: "CR",
          name: "Current Ratio",
          category: "liquidity",
          unit: "x",
          status: "available",
          points: 4,
          current: "1.40",
          projected: "1.30",
          horizon: 1,
          trend: "down",
          risk: true,
          note: "Proyeksi berada di bawah batas warning; perlu perhatian.",
          method: "linear_trend_v1",
        },
        {
          code: "QR",
          name: "Quick Ratio",
          category: "liquidity",
          status: "insufficient",
          points: 2,
          reason:
            "Butuh minimal 3 periode data rasio untuk memproyeksikan tren.",
        },
      ],
    },
    prescriptive: [
      {
        rule_id: "RATIO-CR",
        rule_version: "1.0.0",
        ratio_code: "CR",
        ratio_name: "Current Ratio",
        category: "liquidity",
        priority: "high",
        band: "between_warning_critical",
        display: "1.10x",
        title: "Perbaiki Current Ratio",
        trigger_metrics: { CR: "1.10x" },
        suggested_actions: ["Percepat penagihan piutang."],
        evidence: ["CR berada pada band warning."],
        assumptions: ["Data dianggap lengkap."],
        limitations: ["Rekomendasi bersifat indikatif."],
        confidence_label: "berbasis aturan",
      },
    ],
    ...overrides,
  };
}

describe("InsightPanel", () => {
  it("renders alerts, forecasts, and recommendations", () => {
    render(<InsightPanel insights={makeInsights()} isLoading={false} />);

    expect(
      screen.getByText("Likuiditas berubah ke arah kurang sehat"),
    ).toBeInTheDocument();
    expect(screen.getByText("1.40x")).toBeInTheDocument();
    expect(screen.getByText("1.30x")).toBeInTheDocument();
    expect(screen.getByText("Perbaiki Current Ratio")).toBeInTheDocument();
    expect(
      screen.getByText("Percepat penagihan piutang."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Butuh minimal 3 periode data rasio/i),
    ).toBeInTheDocument();
  });

  it("shows a calm empty state when there are no alerts or actions", () => {
    render(
      <InsightPanel
        insights={makeInsights({
          alerts: [],
          prescriptive: [],
          predictive: {
            horizon: 1,
            min_points: 3,
            method: "linear_trend_v1",
            series: [],
          },
        })}
        isLoading={false}
      />,
    );

    expect(
      screen.getByText(
        /Tidak ada rasio yang memburuk signifikan dibanding periode sebelumnya/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Semua rasio berada pada atau di atas target/i),
    ).toBeInTheDocument();
  });

  it("explains missing comparison period when no prior history exists", () => {
    render(
      <InsightPanel
        insights={makeInsights({
          alerts: [],
          has_previous_period: false,
          history_points: 1,
          predictive: {
            horizon: 1,
            min_points: 3,
            method: "linear_trend_v1",
            series: [],
          },
        })}
        isLoading={false}
      />,
    );

    expect(
      screen.getByText(/Belum ada periode pembanding/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Butuh minimal 3 periode snapshot rasio/i),
    ).toBeInTheDocument();
  });

  it("renders an error state with a retry action", async () => {
    const onRetry = jest.fn();
    render(
      <InsightPanel
        isLoading={false}
        error="Gagal terhubung ke server."
        onRetry={onRetry}
      />,
    );

    expect(screen.getByText("Analisis AI gagal dimuat")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /coba lagi/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("renders a loading placeholder before data arrives", () => {
    render(<InsightPanel isLoading />);
    expect(screen.queryByText("Analisis AI")).not.toBeInTheDocument();
  });
});

import { useEffect, useRef } from "react";
import { toast } from "@/lib/toast";

interface RatioData {
  code: string;
  name: string;
  value: string | null;
  band: string;
  category: string;
}

interface UseAutoAlertsOptions {
  ratios: RatioData[];
  enabled?: boolean;
}

/**
 * Hook untuk auto-trigger toast notification saat ada rasio critical
 * Sesuai vision: "AI akan menampilkan pop-up notifikasi Toastr"
 */
export function useAutoAlerts({ ratios, enabled = true }: UseAutoAlertsOptions) {
  const hasShownRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!enabled || ratios.length === 0) return;

    const criticalRatios = ratios.filter(
      (ratio) => ratio.band === "below_critical" && ratio.value !== null
    );

    const warningRatios = ratios.filter(
      (ratio) =>
        ratio.band === "between_warning_critical" && ratio.value !== null
    );

    // Group by category for better messaging
    const criticalByCategory: Record<string, RatioData[]> = {};
    const warningByCategory: Record<string, RatioData[]> = {};

    criticalRatios.forEach((ratio) => {
      if (!criticalByCategory[ratio.category]) {
        criticalByCategory[ratio.category] = [];
      }
      criticalByCategory[ratio.category].push(ratio);
    });

    warningRatios.forEach((ratio) => {
      if (!warningByCategory[ratio.category]) {
        warningByCategory[ratio.category] = [];
      }
      warningByCategory[ratio.category].push(ratio);
    });

    // Show critical alerts
    Object.entries(criticalByCategory).forEach(([category, ratios]) => {
      const key = `critical-${category}`;
      if (!hasShownRef.current.has(key)) {
        const ratioNames = ratios.map((r) => r.name).join(", ");

        if (category === "Likuiditas") {
          toast.error(
            "⚠️ Likuiditas Jangka Pendek Menurun",
            `${ratioNames} berada di zona kritis. Perusahaan mungkin kesulitan menutupi kewajiban mendesak jika arus kas masuk terhambat.`,
            { duration: 0 } // Manual close untuk critical
          );
        } else if (category === "Solvabilitas") {
          toast.error(
            "⚠️ Risiko Solvabilitas Meningkat",
            `${ratioNames} mendekati batas bahaya. Batasi penambahan utang baru dan evaluasi beban bunga.`,
            { duration: 0 }
          );
        } else if (category === "Aktivitas") {
          toast.error(
            "⚠️ Efisiensi Aktivitas Menurun",
            `${ratioNames} menunjukkan perlambatan. Potensi dead stock di gudang atau keterlambatan pembayaran klien.`,
            { duration: 0 }
          );
        } else if (category === "Profitabilitas") {
          toast.error(
            "⚠️ Profitabilitas Menurun",
            `${ratioNames} di bawah target. Tinjau harga jual, HPP, dan beban operasional.`,
            { duration: 0 }
          );
        } else {
          toast.error(
            `⚠️ ${category} Kritis`,
            `${ratioNames} memerlukan perhatian segera.`,
            { duration: 0 }
          );
        }

        hasShownRef.current.add(key);
      }
    });

    // Show warning alerts (auto-dismiss after 10s)
    Object.entries(warningByCategory).forEach(([category, ratios]) => {
      const key = `warning-${category}`;
      if (!hasShownRef.current.has(key)) {
        const ratioNames = ratios.map((r) => r.name).join(", ");

        toast.warning(
          `${category} Perlu Perhatian`,
          `${ratioNames} mendekati zona warning. Monitoring ketat diperlukan.`,
          { duration: 10000 }
        );

        hasShownRef.current.add(key);
      }
    });
  }, [ratios, enabled]);

  const clearAlertHistory = () => {
    hasShownRef.current.clear();
  };

  return { clearAlertHistory };
}

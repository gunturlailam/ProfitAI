"use client";

import { useSyncExternalStore } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  Info,
  X,
  type LucideIcon,
} from "lucide-react";
import {
  dismissToast,
  getToasts,
  subscribe,
  type ToastVariant,
} from "@/lib/toast";
import { cn } from "@/lib/utils";

const TOAST_ICON: Record<ToastVariant, LucideIcon> = {
  info: Info,
  success: CheckCircle,
  warning: AlertTriangle,
  error: AlertCircle,
};

const TOAST_STYLE: Record<ToastVariant, string> = {
  info: "border-l-blue-500",
  success: "border-l-emerald-500",
  warning: "border-l-amber-500",
  error: "border-l-red-500",
};

const ICON_STYLE: Record<ToastVariant, string> = {
  info: "text-blue-500",
  success: "text-emerald-500",
  warning: "text-amber-500",
  error: "text-red-500",
};

export function Toaster() {
  const toasts = useSyncExternalStore(subscribe, getToasts, getToasts);

  return (
    <div
      aria-live="polite"
      aria-atomic="false"
      className="pointer-events-none fixed inset-x-0 top-4 z-[100] flex flex-col items-stretch gap-2 px-4 sm:left-auto sm:right-4 sm:max-w-sm"
    >
      {toasts.map((item) => {
        const Icon = TOAST_ICON[item.variant];

        return (
          <div
            key={item.id}
            role={item.variant === "error" ? "alert" : "status"}
            className={cn(
              "pointer-events-auto flex w-full items-start gap-3 rounded-2xl border border-[#EBE5DC]/80 border-l-4 bg-white p-4 shadow-[0_12px_32px_rgba(31,36,29,0.14)]",
              TOAST_STYLE[item.variant],
            )}
          >
            <Icon
              className={cn("mt-0.5 h-5 w-5 flex-shrink-0", ICON_STYLE[item.variant])}
            />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-bold text-[#1F241D]">{item.title}</p>
              {item.message && (
                <p className="mt-1 text-xs leading-relaxed text-[#666A61]">
                  {item.message}
                </p>
              )}
            </div>
            <button
              type="button"
              onClick={() => dismissToast(item.id)}
              aria-label="Tutup notifikasi"
              className="rounded-lg p-1 text-[#9A9F94] transition-colors hover:bg-[#FAF7F2] hover:text-[#1F241D]"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}

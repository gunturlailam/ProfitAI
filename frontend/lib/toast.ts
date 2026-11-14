/**
 * Toast store minimal tanpa dependency eksternal.
 *
 * Cocok dengan React 19 via `useSyncExternalStore` (lihat `components/ui/Toaster`).
 * Store hidup di module scope sehingga bisa dipanggil dari mana saja (hook,
 * event handler, efek) tanpa React Context tambahan.
 */

export type ToastVariant = "info" | "success" | "warning" | "error";

export interface ToastOptions {
  title: string;
  message?: string;
  variant?: ToastVariant;
  /** Milidetik sebelum auto-dismiss. `0` berarti harus ditutup manual. */
  duration?: number;
}

export interface ToastItem {
  id: string;
  title: string;
  message?: string;
  variant: ToastVariant;
  duration: number;
}

export const DEFAULT_TOAST_DURATION = 6000;

let toasts: ToastItem[] = [];
const listeners = new Set<() => void>();
const timers = new Map<string, ReturnType<typeof setTimeout>>();
let counter = 0;

function emit(): void {
  for (const listener of listeners) {
    listener();
  }
}

function setToasts(next: ToastItem[]): void {
  toasts = next;
  emit();
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/**
 * Snapshot stabil: referensi array hanya berubah saat daftar toast berubah,
 * sehingga aman untuk `useSyncExternalStore`.
 */
export function getToasts(): ToastItem[] {
  return toasts;
}

export function dismissToast(id: string): void {
  const timer = timers.get(id);
  if (timer) {
    clearTimeout(timer);
    timers.delete(id);
  }
  if (!toasts.some((item) => item.id === id)) return;
  setToasts(toasts.filter((item) => item.id !== id));
}

export function clearToasts(): void {
  for (const timer of timers.values()) {
    clearTimeout(timer);
  }
  timers.clear();
  if (toasts.length === 0) return;
  setToasts([]);
}

export function showToast(options: ToastOptions): string {
  const id = `toast-${++counter}`;
  const duration = options.duration ?? DEFAULT_TOAST_DURATION;
  const item: ToastItem = {
    id,
    title: options.title,
    message: options.message,
    variant: options.variant ?? "info",
    duration,
  };

  setToasts([...toasts, item]);

  if (duration > 0) {
    timers.set(
      id,
      setTimeout(() => dismissToast(id), duration),
    );
  }

  return id;
}

export const toast = {
  show: showToast,
  info: (title: string, message?: string) =>
    showToast({ title, message, variant: "info" }),
  success: (title: string, message?: string) =>
    showToast({ title, message, variant: "success" }),
  warning: (title: string, message?: string) =>
    showToast({ title, message, variant: "warning" }),
  error: (title: string, message?: string) =>
    showToast({ title, message, variant: "error" }),
  dismiss: dismissToast,
  clear: clearToasts,
};

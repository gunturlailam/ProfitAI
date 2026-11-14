import {
  clearToasts,
  dismissToast,
  getToasts,
  showToast,
  subscribe,
  toast,
} from "@/lib/toast";

describe("toast store", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    clearToasts();
  });

  afterEach(() => {
    clearToasts();
    jest.useRealTimers();
  });

  it("adds a toast and notifies subscribers", () => {
    const listener = jest.fn();
    const unsubscribe = subscribe(listener);

    const id = showToast({
      title: "Halo",
      message: "Pesan",
      variant: "warning",
      duration: 0,
    });

    expect(getToasts()).toHaveLength(1);
    expect(getToasts()[0]).toMatchObject({ id, title: "Halo", variant: "warning" });
    expect(listener).toHaveBeenCalledTimes(1);

    unsubscribe();
  });

  it("auto-dismisses after the duration", () => {
    showToast({ title: "Sementara", duration: 1000 });

    expect(getToasts()).toHaveLength(1);
    jest.advanceTimersByTime(1000);
    expect(getToasts()).toHaveLength(0);
  });

  it("keeps a toast when duration is 0", () => {
    showToast({ title: "Manual", duration: 0 });

    jest.advanceTimersByTime(60000);
    expect(getToasts()).toHaveLength(1);
  });

  it("dismisses a specific toast and clears its timer", () => {
    const first = showToast({ title: "A", duration: 5000 });
    showToast({ title: "B", duration: 5000 });

    dismissToast(first);
    expect(getToasts().map((item) => item.title)).toEqual(["B"]);

    jest.advanceTimersByTime(5000);
    expect(getToasts()).toHaveLength(0);
  });

  it("clears all toasts and stops their timers", () => {
    showToast({ title: "A", duration: 5000 });
    showToast({ title: "B", duration: 5000 });

    clearToasts();
    expect(getToasts()).toHaveLength(0);

    jest.advanceTimersByTime(5000);
    expect(getToasts()).toHaveLength(0);
  });

  it("stops notifying after unsubscribe", () => {
    const listener = jest.fn();
    const unsubscribe = subscribe(listener);
    unsubscribe();

    showToast({ title: "X", duration: 0 });

    expect(listener).not.toHaveBeenCalled();
  });

  it("exposes variant helpers on the toast object", () => {
    toast.warning("Judul", "Isi");

    expect(getToasts()[0]).toMatchObject({
      title: "Judul",
      message: "Isi",
      variant: "warning",
    });
  });
});

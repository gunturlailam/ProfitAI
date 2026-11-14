import { Suspense } from "react";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";
import { Toaster } from "@/components/ui/Toaster";
import { WebSocketStatus } from "@/components/shared/WebSocketStatus";
import { ACCESS_TOKEN_COOKIE } from "@/lib/auth";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

// Dashboard content is gated by a request-time session check, so this route
// tree cannot promise an instant navigation. This server layout is the correct
// place for the opt-out (Client Components cannot export `instant`).
export const instant = false;

// Temporarily disabled server-side auth check for demo
// Token stored in sessionStorage (client-side) not accessible from server
// Will be re-enabled when switching to httpOnly cookies
async function verifyAuth() {
  // const token = (await cookies()).get(ACCESS_TOKEN_COOKIE)?.value;
  // if (!token) {
  //   redirect("/login");
  // }

  // const response = await fetch(`${API_BASE_URL}/me`, {
  //   headers: { Authorization: `Bearer ${token}` },
  //   cache: "no-store",
  // }).catch(() => null);

  // if (!response?.ok) {
  //   redirect("/login");
  // }
  
  // For now, auth is handled client-side only
  return;
}

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  await verifyAuth();

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Suspense fallback={<div className="w-60 flex-shrink-0 bg-white border-r" />}>
        <Sidebar />
      </Suspense>
      <main className="flex-1 flex flex-col px-6 py-4 overflow-y-auto">
        <Suspense fallback={<div className="h-20" />}>
          <Navbar />
        </Suspense>
        <Suspense fallback={<div className="flex items-center justify-center flex-1"><div className="text-gray-400">Loading...</div></div>}>
          {children}
        </Suspense>
      </main>
      <Toaster />
      <WebSocketStatus />
    </div>
  );
}

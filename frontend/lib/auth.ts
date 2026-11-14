const ACCESS_TOKEN_KEY = "profitai_access_token";
export const ACCESS_TOKEN_COOKIE = ACCESS_TOKEN_KEY;

function readCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }

  const prefix = `${name}=`;
  for (const part of document.cookie.split(";")) {
    const value = part.trim();
    if (value.startsWith(prefix)) {
      return decodeURIComponent(value.slice(prefix.length));
    }
  }
  return null;
}

function writeCookie(name: string, value: string, maxAgeSeconds?: number): void {
  if (typeof document === "undefined") {
    return;
  }

  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  const maxAge =
    maxAgeSeconds !== undefined ? `; Max-Age=${maxAgeSeconds}` : "";
  document.cookie = `${name}=${encodeURIComponent(value)}; Path=/; SameSite=Lax${maxAge}${secure}`;
}

function deleteCookie(name: string): void {
  if (typeof document === "undefined") {
    return;
  }
  document.cookie = `${name}=; Path=/; Max-Age=0; SameSite=Lax`;
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return (
    window.localStorage.getItem(ACCESS_TOKEN_KEY) ??
    window.sessionStorage.getItem(ACCESS_TOKEN_KEY) ??
    readCookie(ACCESS_TOKEN_COOKIE)
  );
}

export function saveAccessToken(token: string, remember: boolean): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  (remember ? window.localStorage : window.sessionStorage).setItem(
    ACCESS_TOKEN_KEY,
    token,
  );
  writeCookie(
    ACCESS_TOKEN_COOKIE,
    token,
    remember ? 60 * 60 * 24 * 30 : undefined,
  );
}

export function clearAccessToken(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  deleteCookie(ACCESS_TOKEN_COOKIE);
}

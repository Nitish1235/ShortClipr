import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Proxy POST /api/payments/checkout → FastAPI POST /payments/checkout
 * Forwards the user's session cookie for auth.
 */
export async function POST(req: NextRequest) {
  const body = await req.text();
  const cookie = req.headers.get("cookie") ?? "";

  const res = await fetch(`${API_BASE}/payments/checkout`, {
    method:  "POST",
    headers: {
      "Content-Type": "application/json",
      "Cookie":        cookie,
    },
    body,
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";

function CallbackHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const accessToken = searchParams.get("access_token");
    const refreshToken = searchParams.get("refresh_token");

    if (accessToken) {
      document.cookie = `access_token=${accessToken}; path=/; max-age=86400; SameSite=Lax`;
    }
    if (refreshToken) {
      document.cookie = `refresh_token=${refreshToken}; path=/; max-age=604800; SameSite=Lax`;
    }

    // Redirect to dashboard after a brief moment to ensure cookies are set
    setTimeout(() => {
      router.replace("/dashboard");
    }, 100);
  }, [router, searchParams]);

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh", background: "#E8ECEF" }}>
      <div style={{ textAlign: "center" }}>
        <div style={{ width: "40px", height: "40px", border: "4px solid #14B8A6", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 1s linear infinite", margin: "0 auto 16px" }} />
        <p style={{ fontSize: "16px", color: "#374151", fontWeight: 600 }}>Authenticating...</p>
        <style>{`
          @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        `}</style>
      </div>
    </div>
  );
}

export default function AuthCallback() {
  return (
    <Suspense fallback={<div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}><p>Loading...</p></div>}>
      <CallbackHandler />
    </Suspense>
  );
}

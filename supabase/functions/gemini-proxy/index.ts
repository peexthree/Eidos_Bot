// Supabase Edge Function: gemini-proxy
// Server-side proxy for Gemini API. The GEMINI_API_KEY never leaves the server,
// so release builds of the app do not embed a Gemini key at all.
//
// Required secrets (set via `supabase secrets set`):
//   GEMINI_API_KEY - Google AI Studio API key
// Provided automatically by the Supabase runtime:
//   SUPABASE_URL, SUPABASE_ANON_KEY
//
// Request:  POST { prompt, systemPrompt? } with Authorization: Bearer <user JWT>
// Response: { success: true, text } or { success: false, error }

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

const GEMINI_URL =
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent";

// Simple in-memory rate limiter: max N requests per minute per user.
// Per-instance only (each Edge Function isolate has its own map), which is
// enough as a lightweight abuse guard; do not rely on it for billing.
const RATE_LIMIT_MAX = 20;
const RATE_LIMIT_WINDOW_MS = 60_000;
const rateBuckets = new Map<string, { windowStart: number; count: number }>();

interface GeminiProxyRequest {
  prompt?: string;
  systemPrompt?: string | null;
}

// Gemini generateContent response (subset we care about)
interface GeminiGenerateResponse {
  candidates?: {
    content?: {
      parts?: { text?: string }[];
    };
  }[];
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}

function isRateLimited(userId: string): boolean {
  const now = Date.now();
  // Opportunistic cleanup of expired buckets so the map stays bounded.
  if (rateBuckets.size > 10_000) {
    for (const [key, bucket] of rateBuckets) {
      if (now - bucket.windowStart >= RATE_LIMIT_WINDOW_MS) rateBuckets.delete(key);
    }
  }
  const bucket = rateBuckets.get(userId);
  if (bucket === undefined || now - bucket.windowStart >= RATE_LIMIT_WINDOW_MS) {
    rateBuckets.set(userId, { windowStart: now, count: 1 });
    return false;
  }
  bucket.count += 1;
  return bucket.count > RATE_LIMIT_MAX;
}

Deno.serve(async (req: Request): Promise<Response> => {
  // CORS preflight
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: CORS_HEADERS });
  }
  if (req.method !== "POST") {
    return jsonResponse(405, { success: false, error: "Method not allowed. Use POST." });
  }

  try {
    // 1. Authenticate the caller: a valid Supabase user JWT is mandatory.
    const authHeader = req.headers.get("Authorization") ?? "";
    const userJwt = authHeader.replace(/^Bearer\s+/i, "").trim();
    if (userJwt === "") {
      return jsonResponse(401, { success: false, error: "Authorization: Bearer <user JWT> is required." });
    }
    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY");
    if (!supabaseUrl || !supabaseAnonKey) {
      return jsonResponse(503, { success: false, error: "Server is not configured (missing Supabase env)." });
    }
    const supabase = createClient(supabaseUrl, supabaseAnonKey);
    const { data: userData, error: userError } = await supabase.auth.getUser(userJwt);
    if (userError !== null || userData?.user === null || userData?.user === undefined) {
      return jsonResponse(401, { success: false, error: "Invalid or expired user token." });
    }
    const userId = userData.user.id;

    // 2. Rate limit: max 20 requests per minute per user.
    if (isRateLimited(userId)) {
      return jsonResponse(429, { success: false, error: "Too many requests. Try again later." });
    }

    // 3. Check Gemini configuration.
    const geminiApiKey = Deno.env.get("GEMINI_API_KEY");
    if (!geminiApiKey) {
      return jsonResponse(503, { success: false, error: "Server is not configured (missing GEMINI_API_KEY)." });
    }

    // 4. Parse and validate the request body.
    const body = (await req.json().catch(() => null)) as GeminiProxyRequest | null;
    const prompt = body?.prompt ?? "";
    const systemPrompt = body?.systemPrompt ?? "";
    if (prompt.trim() === "") {
      return jsonResponse(400, { success: false, error: "prompt is required." });
    }

    // 5. Forward to the Gemini API. The key is sent via the x-goog-api-key header,
    // never as a query parameter. Body mirrors the client-side generateContent request.
    const geminiPayload: Record<string, unknown> = {
      contents: [{ parts: [{ text: prompt }] }],
    };
    if (systemPrompt.trim() !== "") {
      geminiPayload.systemInstruction = { parts: [{ text: systemPrompt }] };
    }

    const geminiRes = await fetch(GEMINI_URL, {
      method: "POST",
      headers: {
        "x-goog-api-key": geminiApiKey,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(geminiPayload),
    });
    if (!geminiRes.ok) {
      // Log only the status code: never the request body (contains the prompt)
      // and never the API key.
      console.error(`gemini-proxy: Gemini API returned ${geminiRes.status}`);
      return jsonResponse(502, { success: false, error: "Gemini API request failed." });
    }
    const geminiData = (await geminiRes.json()) as GeminiGenerateResponse;
    const text = (geminiData.candidates?.[0]?.content?.parts ?? [])
      .map((p) => p.text ?? "")
      .join("")
      .trim();
    if (text === "") {
      console.error("gemini-proxy: Gemini API returned no text candidates");
      return jsonResponse(502, { success: false, error: "Gemini API returned an empty response." });
    }

    return jsonResponse(200, { success: true, text });
  } catch (e) {
    console.error("gemini-proxy: unexpected error:", (e as Error).message);
    return jsonResponse(500, { success: false, error: "Internal server error." });
  }
});

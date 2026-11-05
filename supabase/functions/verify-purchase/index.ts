// Supabase Edge Function: verify-purchase
// Server-side Google Play purchase verification + server ledger recording.
//
// Required secrets (set via `supabase secrets set`):
//   GOOGLE_SERVICE_ACCOUNT_JSON - service account JSON (as a single string) with Android Publisher access
//   ANDROID_PACKAGE_NAME        - e.g. io.eidos.zerolayer
// Provided automatically by the Supabase runtime:
//   SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
//
// Request:  POST { purchaseToken, productId, orderId? } with Authorization: Bearer <user JWT>
// Response: { success: true, biocoins_granted } or { success: false, error }

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

// IMPORTANT: product IDs and biocoin amounts here MUST match the in-app products
// configured in Google Play Console AND the products queried by the client
// (see EidosBillingManager.querySkuDetails). This catalog is the single server-side
// source of truth: the granted amount is always taken from it, never from the request body.
const PRODUCT_CATALOG: Record<string, number> = {
  biocoin_pack_1000: 1000,
};

const GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token";
const ANDROIDPUBLISHER_SCOPE = "https://www.googleapis.com/auth/androidpublisher";
const ANDROIDPUBLISHER_BASE = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications";

interface VerifyPurchaseRequest {
  purchaseToken?: string;
  productId?: string;
  orderId?: string | null;
}

interface ServiceAccountJson {
  client_email?: string;
  private_key?: string;
}

// Google Play purchases.products.get response (subset we care about)
interface PlayProductPurchase {
  purchaseState?: number; // 0 = purchased, 1 = canceled, 2 = pending
  acknowledgementState?: number; // 0 = pending, 1 = acknowledged
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}

function base64ToBytes(b64: string): Uint8Array {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}

function bytesToBase64Url(bytes: Uint8Array): string {
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function jsonToBase64Url(value: unknown): string {
  return bytesToBase64Url(new TextEncoder().encode(JSON.stringify(value)));
}

async function sha256Hex(input: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(input));
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

// Import the service account RSA private key (PKCS8 PEM) for RS256 signing.
async function importPrivateKey(pem: string): Promise<CryptoKey> {
  const b64 = pem
    .replace("-----BEGIN PRIVATE KEY-----", "")
    .replace("-----END PRIVATE KEY-----", "")
    .replace(/\s+/g, "");
  const der = base64ToBytes(b64);
  return crypto.subtle.importKey(
    "pkcs8",
    der,
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["sign"],
  );
}

// Exchange a self-signed RS256 service account JWT for a Google access token.
async function getGoogleAccessToken(serviceAccount: ServiceAccountJson): Promise<string> {
  if (!serviceAccount.client_email || !serviceAccount.private_key) {
    throw new Error("GOOGLE_SERVICE_ACCOUNT_JSON is missing client_email or private_key");
  }
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: "RS256", typ: "JWT" };
  const claims = {
    iss: serviceAccount.client_email,
    scope: ANDROIDPUBLISHER_SCOPE,
    aud: GOOGLE_TOKEN_URL,
    iat: now,
    exp: now + 3600,
  };
  const unsigned = `${jsonToBase64Url(header)}.${jsonToBase64Url(claims)}`;
  const key = await importPrivateKey(serviceAccount.private_key);
  const signature = await crypto.subtle.sign(
    "RSASSA-PKCS1-v1_5",
    key,
    new TextEncoder().encode(unsigned),
  );
  const assertion = `${unsigned}.${bytesToBase64Url(new Uint8Array(signature))}`;

  const tokenRes = await fetch(GOOGLE_TOKEN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion,
    }),
  });
  if (!tokenRes.ok) {
    const detail = await tokenRes.text();
    throw new Error(`Google OAuth token exchange failed: ${tokenRes.status} ${detail}`);
  }
  const tokenData = await tokenRes.json();
  if (typeof tokenData.access_token !== "string" || tokenData.access_token === "") {
    throw new Error("Google OAuth response has no access_token");
  }
  return tokenData.access_token;
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

    // 2. Check Google Play integration configuration.
    const serviceAccountRaw = Deno.env.get("GOOGLE_SERVICE_ACCOUNT_JSON");
    const packageName = Deno.env.get("ANDROID_PACKAGE_NAME");
    if (!serviceAccountRaw || !packageName) {
      return jsonResponse(503, {
        success: false,
        error:
          "Server is not configured for purchase verification. " +
          "Set GOOGLE_SERVICE_ACCOUNT_JSON and ANDROID_PACKAGE_NAME secrets.",
      });
    }

    // 3. Parse and validate the request body.
    const body = (await req.json().catch(() => null)) as VerifyPurchaseRequest | null;
    const purchaseToken = body?.purchaseToken?.trim() ?? "";
    const productId = body?.productId?.trim() ?? "";
    const orderId = body?.orderId?.trim() || null;
    if (purchaseToken === "" || productId === "") {
      return jsonResponse(400, { success: false, error: "purchaseToken and productId are required." });
    }
    // The granted amount always comes from the server-side catalog, never from the client.
    const biocoins = PRODUCT_CATALOG[productId];
    if (biocoins === undefined) {
      return jsonResponse(400, { success: false, error: `Unknown productId: ${productId}` });
    }

    // 4. Verify the purchase against Google Play Developer API.
    let serviceAccount: ServiceAccountJson;
    try {
      serviceAccount = JSON.parse(serviceAccountRaw) as ServiceAccountJson;
    } catch (_e) {
      return jsonResponse(503, { success: false, error: "GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON." });
    }
    let googleAccessToken: string;
    try {
      googleAccessToken = await getGoogleAccessToken(serviceAccount);
    } catch (e) {
      console.error("verify-purchase: google auth failed:", (e as Error).message);
      return jsonResponse(502, { success: false, error: "Google authentication failed." });
    }
    const playUrl =
      `${ANDROIDPUBLISHER_BASE}/${encodeURIComponent(packageName)}` +
      `/purchases/products/${encodeURIComponent(productId)}` +
      `/tokens/${encodeURIComponent(purchaseToken)}`;
    const playRes = await fetch(playUrl, {
      headers: { Authorization: `Bearer ${googleAccessToken}` },
    });
    if (!playRes.ok) {
      console.error(`verify-purchase: Play API returned ${playRes.status}`);
      return jsonResponse(400, { success: false, error: "Purchase verification with Google Play failed." });
    }
    const purchase = (await playRes.json()) as PlayProductPurchase;
    // purchaseState must be 0 (purchased); acknowledgementState 0 (pending) or 1 (acknowledged) are both accepted.
    if (purchase.purchaseState !== 0) {
      return jsonResponse(400, { success: false, error: "Purchase is not in purchased state." });
    }
    const ackState = purchase.acknowledgementState;
    if (ackState !== 0 && ackState !== 1) {
      return jsonResponse(400, { success: false, error: "Purchase acknowledgement state is invalid." });
    }

    // 5. Record the purchase in the server ledger via verify_and_record_purchase RPC.
    // The RPC is protected against replay by a unique token_hash (SHA-256 of the purchase token).
    const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
    if (!serviceRoleKey) {
      return jsonResponse(503, { success: false, error: "Server is not configured (missing service role key)." });
    }
    const tokenHash = await sha256Hex(purchaseToken);
    const rpcRes = await fetch(`${supabaseUrl}/rest/v1/rpc/verify_and_record_purchase`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${serviceRoleKey}`,
        apikey: serviceRoleKey,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        p_order_id: orderId,
        p_token_hash: tokenHash,
        p_product_id: productId,
        p_biocoins: biocoins,
        // auth.uid() is NULL under service_role, so the RPC requires the
        // explicit target player (verified server-side inside the RPC).
        p_player_id: userData.user.id,
      }),
    });
    if (!rpcRes.ok) {
      const rpcError = await rpcRes.text();
      console.error(`verify-purchase: ledger RPC failed ${rpcRes.status}: ${rpcError}`);
      return jsonResponse(502, { success: false, error: "Failed to record purchase in the ledger." });
    }
    await rpcRes.text(); // drain the response body

    return jsonResponse(200, { success: true, biocoins_granted: biocoins });
  } catch (e) {
    console.error("verify-purchase: unexpected error:", (e as Error).message);
    return jsonResponse(500, { success: false, error: "Internal server error." });
  }
});

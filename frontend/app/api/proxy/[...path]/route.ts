const BACKEND =
  process.env.API_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_BASE ||
  "http://localhost:3000";

/** Same-origin proxy: browser <-> Next.js <-> FastAPI. Passes status,
 * content-type, and bytes through untouched (JSON, multipart, video). */
async function forward(req: Request, path: string[]) {
  const target = `${BACKEND}/v1/${path.join("/")}`;
  const init: RequestInit = { method: req.method, headers: {} };
  const ctype = req.headers.get("content-type");
  if (ctype) (init.headers as Record<string, string>)["content-type"] = ctype;
  const idem = req.headers.get("idempotency-key");
  if (idem) (init.headers as Record<string, string>)["Idempotency-Key"] = idem;
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = Buffer.from(await req.arrayBuffer());
  }
  const upstream = await fetch(target, init);
  const buf = Buffer.from(await upstream.arrayBuffer());
  return new Response(buf, {
    status: upstream.status,
    headers: {
      "content-type":
        upstream.headers.get("content-type") || "application/octet-stream",
    },
  });
}

export async function GET(
  req: Request,
  { params }: { params: { path: string[] } }
) {
  return forward(req, params.path);
}

export async function POST(
  req: Request,
  { params }: { params: { path: string[] } }
) {
  return forward(req, params.path);
}

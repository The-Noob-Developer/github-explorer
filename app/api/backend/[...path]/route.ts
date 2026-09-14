/**
 * Local-development-only proxy to the FastAPI backend.
 *
 * The v0 sandbox preview only exposes the Next.js dev server's port to the
 * browser, so the backend running on localhost:8000 inside the same VM is
 * not reachable directly from client-side fetches during local testing.
 * This route forwards requests server-side (where localhost IS reachable)
 * so the UI can be exercised end-to-end before the backend is deployed.
 *
 * Once the backend is deployed (e.g. to Render), point
 * NEXT_PUBLIC_API_URL directly at that public URL and this proxy is no
 * longer used -- the frontend still never touches a Groq/GitHub credential.
 */

const BACKEND_INTERNAL_URL = process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000"

async function forward(request: Request, path: string[]) {
  const targetUrl = `${BACKEND_INTERNAL_URL}/${path.join("/")}`
  const init: RequestInit = {
    method: request.method,
    headers: { "Content-Type": "application/json" },
  }
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.text()
  }

  try {
    const response = await fetch(targetUrl, init)
    const body = await response.text()
    return new Response(body, {
      status: response.status,
      headers: { "Content-Type": response.headers.get("Content-Type") ?? "application/json" },
    })
  } catch {
    return Response.json(
      { status: "error", error: { code: "backend_unreachable", message: "The backend is not reachable." } },
      { status: 502 },
    )
  }
}

export async function GET(request: Request, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params
  return forward(request, path)
}

export async function POST(request: Request, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params
  return forward(request, path)
}

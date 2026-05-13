/**
 * gvo-skills-mcp — Cloudflare Worker exposing the gvo-skills GitHub repo as an
 * MCP server over HTTP. Designed to replace the VPS-hosted from-desktop MCP
 * that the gvo-router skill expects in claude.ai cloud sessions.
 *
 * Endpoints:
 *   GET  /         → human-readable banner
 *   GET  /health   → JSON liveness probe
 *   POST /mcp      → JSON-RPC 2.0 over HTTP (initialize, tools/list, tools/call)
 *
 * Tools (all read-only, scoped to the configured GitHub repo + ref):
 *   codebase_list_allowed_roots
 *   codebase_read_file
 *   codebase_list_directory
 *   codebase_find_files
 *   codebase_search_code
 */
import { Hono } from "hono";
import { cors } from "hono/cors";
import { handleMcpRequest } from "./mcp";
import type { AppEnv } from "./tools";

const app = new Hono<{ Bindings: AppEnv }>();

// claude.ai's MCP client calls us cross-origin from a browser context — allow it.
app.use("*", cors({ origin: "*", allowMethods: ["GET", "POST", "OPTIONS"] }));

app.get("/", (c) =>
  c.text(
    "gvo-skills-mcp — MCP server for the gvo-skills repository.\n" +
      `Repo:   ${c.env.GITHUB_OWNER}/${c.env.GITHUB_REPO} @ ${c.env.GITHUB_REF}\n` +
      "Health: GET  /health\n" +
      "MCP:    POST /mcp  (JSON-RPC 2.0)\n",
  ),
);

app.get("/health", (c) =>
  c.json({
    status: "ok",
    service: "gvo-skills-mcp",
    version: "0.1.0",
    repo: `${c.env.GITHUB_OWNER}/${c.env.GITHUB_REPO}`,
    ref: c.env.GITHUB_REF,
    rootId: c.env.ROOT_ID,
    timestamp: new Date().toISOString(),
  }),
);

// SSE framing for a single JSON-RPC response. The MCP Streamable HTTP transport spec
// (2025-03-26+) allows the server to choose application/json OR text/event-stream;
// claude.ai's MCP client requires text/event-stream in practice, so we honor the
// Accept header and frame accordingly.
function sseResponse(payload: unknown, status = 200): Response {
  const body = `event: message\ndata: ${JSON.stringify(payload)}\n\n`;
  return new Response(body, {
    status,
    headers: {
      "content-type": "text/event-stream; charset=utf-8",
      "cache-control": "no-cache, no-transform",
      "x-accel-buffering": "no",
      "connection": "keep-alive",
    },
  });
}

function wantsSse(accept: string | undefined): boolean {
  if (!accept) return false;
  return accept.toLowerCase().includes("text/event-stream");
}

app.post("/mcp", async (c) => {
  const accept = c.req.header("accept");
  const useSse = wantsSse(accept);

  let body: unknown;
  try {
    body = await c.req.json();
  } catch (err) {
    const errResponse = {
      jsonrpc: "2.0" as const,
      id: null,
      error: {
        code: -32700,
        message: "Parse error",
        data: err instanceof Error ? err.message : String(err),
      },
    };
    return useSse ? sseResponse(errResponse, 400) : c.json(errResponse, 400);
  }

  // Batch requests are valid JSON-RPC but not used by any MCP client in practice.
  if (Array.isArray(body)) {
    const errResponse = {
      jsonrpc: "2.0" as const,
      id: null,
      error: { code: -32600, message: "Batch requests are not supported" },
    };
    return useSse ? sseResponse(errResponse, 400) : c.json(errResponse, 400);
  }

  const response = await handleMcpRequest(body as Record<string, unknown>, c.env);

  // Notifications (no id) get a 202 Accepted with no body per MCP Streamable HTTP spec.
  if (response === null) {
    return new Response(null, { status: 202 });
  }

  return useSse ? sseResponse(response) : c.json(response);
});

// GET /mcp opens a server-initiated SSE channel. This server has no server-initiated
// notifications, so we respond with a minimal SSE stream (a single comment line) and
// close. Some clients refuse to talk to a server that returns 405 on GET, even though
// the spec permits it; the empty stream keeps them happy.
app.get("/mcp", (c) => {
  if (!wantsSse(c.req.header("accept"))) {
    return c.text(
      "MCP endpoint. POST JSON-RPC 2.0 messages here. GET with 'Accept: text/event-stream' to open an SSE channel (no server notifications are sent).",
      200,
    );
  }
  return new Response(": gvo-skills-mcp has no server-initiated notifications\n\n", {
    status: 200,
    headers: {
      "content-type": "text/event-stream; charset=utf-8",
      "cache-control": "no-cache, no-transform",
      "x-accel-buffering": "no",
      "connection": "keep-alive",
    },
  });
});

export default app;

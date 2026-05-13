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

app.post("/mcp", async (c) => {
  let body: unknown;
  try {
    body = await c.req.json();
  } catch (err) {
    return c.json(
      {
        jsonrpc: "2.0",
        id: null,
        error: {
          code: -32700,
          message: "Parse error",
          data: err instanceof Error ? err.message : String(err),
        },
      },
      400,
    );
  }

  // Batch requests are valid JSON-RPC but not used by any MCP client in practice.
  // We accept a single request object only; batch would be added if a client needs it.
  if (Array.isArray(body)) {
    return c.json(
      {
        jsonrpc: "2.0",
        id: null,
        error: { code: -32600, message: "Batch requests are not supported" },
      },
      400,
    );
  }

  const response = await handleMcpRequest(body as Record<string, unknown>, c.env);

  // Notifications (no id) get a 204 — JSON-RPC says notifications have no response,
  // but most MCP clients tolerate an empty 200. Returning 204 is the strict-correct path.
  if (response === null) {
    return new Response(null, { status: 204 });
  }

  return c.json(response);
});

export default app;

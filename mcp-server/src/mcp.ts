/**
 * JSON-RPC 2.0 + MCP method dispatcher.
 *
 * MCP methods implemented:
 *   initialize                 — protocol handshake; returns capabilities + serverInfo
 *   notifications/initialized  — client signals it's ready (no response)
 *   ping                       — empty ok response
 *   tools/list                 — list available tools
 *   tools/call                 — invoke a tool by name with arguments
 *
 * Anything else returns -32601 (method not found).
 */
import { listTools, callTool, type AppEnv } from "./tools";

const PROTOCOL_VERSION = "2024-11-05";

const SERVER_INFO = {
  name: "gvo-skills-mcp",
  version: "0.1.0",
} as const;

type JsonRpcSuccess = {
  jsonrpc: "2.0";
  id: number | string | null;
  result: unknown;
};

type JsonRpcError = {
  jsonrpc: "2.0";
  id: number | string | null;
  error: { code: number; message: string; data?: unknown };
};

export type JsonRpcResponse = JsonRpcSuccess | JsonRpcError;

const PARSE_ERROR = -32700;
const INVALID_REQUEST = -32600;
const METHOD_NOT_FOUND = -32601;
const INVALID_PARAMS = -32602;
const INTERNAL_ERROR = -32603;

function ok(id: number | string | null, result: unknown): JsonRpcSuccess {
  return { jsonrpc: "2.0", id, result };
}

function err(
  id: number | string | null,
  code: number,
  message: string,
  data?: unknown,
): JsonRpcError {
  const error: JsonRpcError["error"] = { code, message };
  if (data !== undefined) error.data = data;
  return { jsonrpc: "2.0", id, error };
}

/**
 * Dispatch one JSON-RPC request. Returns `null` for notifications (no response).
 */
export async function handleMcpRequest(
  req: Record<string, unknown>,
  env: AppEnv,
): Promise<JsonRpcResponse | null> {
  if (req.jsonrpc !== "2.0") {
    return err(
      (req.id as number | string | null) ?? null,
      INVALID_REQUEST,
      "Invalid Request: jsonrpc must be '2.0'",
    );
  }

  const method = typeof req.method === "string" ? req.method : "";
  const id = (req.id as number | string | null) ?? null;
  const isNotification = req.id === undefined || req.id === null;
  const params = (req.params ?? {}) as Record<string, unknown>;

  try {
    switch (method) {
      case "initialize":
        return ok(id, {
          protocolVersion: PROTOCOL_VERSION,
          capabilities: { tools: {} },
          serverInfo: SERVER_INFO,
        });

      case "notifications/initialized":
      case "initialized":
        // Notification — no response. Return null so the transport returns 204.
        return null;

      case "ping":
        return ok(id, {});

      case "tools/list":
        return ok(id, { tools: listTools() });

      case "tools/call": {
        const name = typeof params.name === "string" ? params.name : "";
        const args = (params.arguments ?? {}) as Record<string, unknown>;
        if (!name) {
          return err(id, INVALID_PARAMS, "Missing 'name' in tools/call params");
        }
        const result = await callTool(name, args, env);
        return ok(id, result);
      }

      default:
        // Notifications for unknown methods are silently dropped per JSON-RPC convention.
        if (isNotification) return null;
        return err(id, METHOD_NOT_FOUND, `Method not found: ${method}`);
    }
  } catch (e) {
    // Tool errors return as MCP tool errors (isError=true content), not JSON-RPC errors,
    // so that the model receives the error message and can react. Internal failures still
    // surface as JSON-RPC errors so a misconfigured client sees a clean failure.
    if (e instanceof ToolError) {
      return ok(id, {
        content: [{ type: "text", text: e.message }],
        isError: true,
      });
    }
    return err(
      id,
      INTERNAL_ERROR,
      "Internal error",
      e instanceof Error ? e.message : String(e),
    );
  }
}

/**
 * Throw from inside a tool to signal a user-visible error that should reach the
 * model as content (isError=true) rather than as a JSON-RPC failure.
 */
export class ToolError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ToolError";
  }
}

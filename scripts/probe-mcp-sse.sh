#!/usr/bin/env bash
URL="https://gvo-skills-mcp.lando555.workers.dev/mcp"

echo "=== POST with Accept: text/event-stream (claude.ai-style) ==="
curl -s -m 10 -X POST "$URL" \
  -H 'content-type: application/json' \
  -H 'accept: text/event-stream, application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{}}}' \
  -i | head -20
echo
echo

echo "=== POST with Accept: application/json (curl-style) ==="
curl -s -m 10 -X POST "$URL" \
  -H 'content-type: application/json' \
  -H 'accept: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  -i | head -10
echo
echo

echo "=== GET /mcp with Accept: text/event-stream ==="
curl -s -m 5 "$URL" -H 'accept: text/event-stream' -i | head -10
echo
echo

echo "=== GET /mcp without SSE header (humans) ==="
curl -s -m 5 "$URL" -i | head -8

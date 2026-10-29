#!/usr/bin/env python3
"""MCP server (stdio) cho brain, để mọi agent hỗ trợ MCP dùng được: Claude Code, Codex, Gemini CLI,
Cursor, VS Code Copilot, Windsurf... Chỉ cần Python 3.9+, không cài thêm gì.

  python3 scripts/brain.py mcp-config   # in lệnh/cấu hình cho từng agent

Tool: brain_context, brain_search, brain_read, brain_capture. Đọc chỉ phần brain đã tinh luyện
(không private/, raw/, inbox, logs). Ghi chỉ vào 00-inbox; ingest kiểm lại trước khi thành fact.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brain  # noqa: E402

PROTOCOL = "2024-11-05"

TOOLS = [
    {"name": "brain_context",
     "description": "Đọc đầu mỗi session: chủ brain là ai, cách họ muốn làm việc, INDEX các file.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "brain_search",
     "description": "Tìm trong second brain theo từ khoá (xếp hạng BM25, khớp nhất trước). Trả về path:line:text.",
     "inputSchema": {"type": "object", "properties": {
         "query": {"type": "string"}, "limit": {"type": "integer", "default": 20}},
         "required": ["query"]}},
    {"name": "brain_read",
     "description": "Đọc một file trong brain theo path tương đối, ví dụ 20-projects/agora.md.",
     "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "brain_capture",
     "description": "Gửi ghi chú (quyết định, trạng thái dự án, bài học) vào inbox của brain. "
                    "Ingest sẽ kiểm tra trước khi ghi thành fact.",
     "inputSchema": {"type": "object", "properties": {
         "title": {"type": "string"}, "body": {"type": "string"},
         "agent": {"type": "string", "description": "tên agent, ví dụ codex, gemini, cursor"}},
         "required": ["title", "body"]}},
]

def call_tool(name, args):
    t0 = time.time()
    if name == "brain_context":
        out = brain.brain_context()
        brain.qa_log("(context)", ["INDEX.md"], True, time.time() - t0, source="mcp")
        return out
    if name == "brain_search":
        hits = brain.brain_search(args["query"], int(args.get("limit") or 20))
        brain.qa_log(args["query"], [h["path"] for h in hits], bool(hits), time.time() - t0, source="mcp")
        return "\n".join(f"{h['path']}:{h['line']}: {h['text']}" for h in hits) or "không có trong brain"
    if name == "brain_read":
        try:
            out = brain.brain_read(args["path"])
        except ValueError:
            brain.qa_log(f"read {args['path']}", [], False, time.time() - t0, source="mcp")
            raise
        brain.qa_log(f"read {args['path']}", [args["path"]], True, time.time() - t0, source="mcp")
        return out
    if name == "brain_capture":
        return "đã gửi: " + brain.brain_capture(args["title"], args["body"], args.get("agent") or "agent")
    raise ValueError(f"unknown tool {name}")

def handle(msg):
    method, mid = msg.get("method"), msg.get("id")
    if method == "initialize":
        ver = (msg.get("params") or {}).get("protocolVersion") or PROTOCOL
        return {"protocolVersion": ver, "capabilities": {"tools": {}},
                "serverInfo": {"name": f"{brain.BRAIN_ID}-brain", "version": "1.0"}}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        p = msg.get("params") or {}
        try:
            text, err = call_tool(p.get("name"), p.get("arguments") or {}), False
        except Exception as e:  # lỗi tool trả về cho agent đọc, không làm chết server
            text, err = f"lỗi: {e}", True
        return {"content": [{"type": "text", "text": text}], "isError": err}
    if method == "ping":
        return {}
    if mid is None:
        return None  # notification
    raise LookupError(method)

def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        mid = msg.get("id")
        try:
            result = handle(msg)
            if mid is None:
                continue
            out = {"jsonrpc": "2.0", "id": mid, "result": result}
        except LookupError as e:
            out = {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {e}"}}
        sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()

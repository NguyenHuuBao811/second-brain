#!/usr/bin/env python3
"""Second brain CLI. Chạy trên macOS, Linux, Windows. Chỉ cần Python 3.9+, git, Claude Code.
Mọi máy đều ghi được vào brain. Mọi agent (Claude, Codex, Gemini, Cursor...) đọc được qua
AGENTS.md, các lệnh context/search/read/capture bên dưới, hoặc MCP server scripts/brain_mcp.py.

  python3 scripts/brain.py doctor
  python3 scripts/brain.py run ingest|reflect|lint|eval [--model sonnet] [--no-sync]
  python3 scripts/brain.py sync
  python3 scripts/brain.py chats [--days 30]
  python3 scripts/brain.py git <repo_path> [--since "6 months ago"]
  python3 scripts/brain.py schedule install [--jobs ingest,reflect,lint,sync] [--dry-run --os linux]
  python3 scripts/brain.py schedule uninstall | status
  python3 scripts/brain.py context | search <từ khoá> | read <path> | capture --title T --agent A
  python3 scripts/brain.py mcp-config   # cấu hình MCP cho Claude Code, Codex, Gemini CLI, Cursor
  python3 scripts/brain.py check [--backfill] | gaps [--days 7] [--write]   # kiểm tất định, khoảng trống

Trên Windows dùng `py -3` thay cho `python3`.

An toàn khi chạy nền:
- Không bypass quyền. Agent không có Bash, chỉ ghi được vào thư mục dữ liệu.
- headless/settings.json chặn sửa file điều khiển (scripts, prompts, headless, AGENTS.md, CLAUDE.md, raw, private).
- Chỉ commit dữ liệu. File điều khiển bị đổi thì ghi cảnh báo, không commit.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hibrain.brain.agentapi import brain_capture, brain_context, brain_read, brain_search, qa_log  # noqa: E402
from hibrain.brain.cli import main  # noqa: E402
from hibrain.brain.config import BRAIN_ID  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

"""Đường dẫn, máy, danh sách job: hằng số dùng chung."""
import hashlib
import os
import platform
import re
import socket
import subprocess
from hibrain import SCRIPTS_DIR

BASE = SCRIPTS_DIR.parent
LOGS = BASE / "logs"
INBOX = BASE / "00-inbox"
# Chat do collect gom về nằm ở đây: không vào git, không rời máy. Chỉ ingest trên máy này đọc.
LOCAL_INBOX = INBOX / "local"
COLLECT_ALLOW = BASE / "private" / "collect-projects.txt"  # mỗi dòng một thư mục dự án được phép gom
DATA_DIRS = ["10-daily", "20-projects", "25-areas", "30-people", "40-decisions", "50-knowledge",
             "90-reference", "archive", "eval", "indexes"]
DATA_FILES = ["INDEX.md", "LOG.md", "CRITICAL.md"]
CONTROL = ["scripts", "prompts", "headless", ".claude", "AGENTS.md", "CLAUDE.md", "GEMINI.md", "raw",
           ".gitattributes", ".gitignore", "README.md"]
OS = platform.system()  # Darwin | Linux | Windows
# Định danh brain theo tên thư mục, để nhiều brain trên một máy không đè job của nhau.
BRAIN_ID = re.sub(r"[^a-z0-9]+", "-", BASE.name.lower()).strip("-") or "brain"
LABEL = f"com.secondbrain.{BRAIN_ID}"
CRON_TAG = f"# secondbrain:{BRAIN_ID}:"
TASK_DIR = f"SecondBrain\\{BRAIN_ID}"
def _stable_host():
    """Tên máy không đổi theo mạng. macOS: LocalHostName; nơi khác: hostname."""
    if platform.system() == "Darwin":
        try:
            r = subprocess.run(["scutil", "--get", "LocalHostName"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except Exception:
            pass
    return socket.gethostname().split(".")[0]


HOST = os.environ.get("BRAIN_HOST") or _stable_host()
# Độ lệch phút riêng cho từng máy: nhiều máy cùng ghi thì không chạy job cùng một lúc.
HOST_OFFSET = int(hashlib.sha1(HOST.encode("utf-8")).hexdigest(), 16) % 60

# job: (model, schedule). schedule = ("hourly", minute) | ("daily", hour, minute) | ("weekly", weekday 0=Sun, hour, minute)
# Phiên Claude do brain tự chạy được ghi entrypoint này, để collect không nạp lại chính nó.
BRAIN_ENTRYPOINT = "brain-job"
SKIP_ENTRYPOINTS = {"sdk-py", "sdk-cli", "sdk-ts", BRAIN_ENTRYPOINT}

# Phút trong lịch là mốc gốc; mỗi máy cộng thêm HOST_OFFSET (xem job_schedule).
JOBS = {
    "ingest": ("sonnet", ("hourly", 7)),
    "reflect": ("sonnet", ("weekly", 0, 20, 3)),
    "lint": ("haiku", ("daily", 6, 13)),
    "sync": (None, ("hourly", 37)),
    "collect": (None, ("daily", 23, 47)),
    "prune": ("sonnet", ("weekly", 6, 21, 3)),
    # Kéo chat Lark trong allowlist (cần lark-cli đã login user trên máy đó): cài riêng, không có trong --jobs mặc định.
    "lark": (None, ("daily", 22, 53)),
    # Tự học mỗi giờ + DM chủ brain điều đã học (USER 2026-10-20). Cài riêng trên máy chạy bot Lark (cần lark-bot.env).
    "learn": ("sonnet", ("hourly", 27)),
    # Tổng hợp cả ngày đã học + danh sách chờ duyệt, DM chủ brain đúng 17:45 (USER 2026-10-25, giờ đổi 2026-10-28).
    # Cài cùng máy với learn.
    "learn-day": ("sonnet", ("daily", 17, 45)),
    # Kiểm mẫu fact mỗi tuần (P17): agent khác đối chiếu fact với bản gốc, trần 1 USD/lần. Model: BRAIN_VERIFY_MODEL.
    "verify": (None, ("weekly", 0, 5, 41)),
}

# Job dọn cả brain chỉ cần một máy chạy mỗi kỳ: máy khác vừa chạy thì bỏ qua.
# Job chủ brain hẹn đúng giờ: không cộng HOST_OFFSET.
FIXED_TIME_JOBS = {"learn-day"}

SHARED_JOBS = {"reflect": "6 days ago", "lint": "20 hours ago", "prune": "6 days ago"}

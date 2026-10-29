"""Làm sạch chữ: bỏ tag nhiễu, che secret, đánh dấu dữ liệu không tin cậy."""
import re

# Thẻ hệ thống Claude Code chèn vào lượt "user". Không phải lời người dùng, bỏ đi.
_NOISE_TAGS = ("task-notification", "system-reminder", "local-command-caveat", "local-command-stdout",
               "command-name", "command-message", "command-args", "ide_opened_file", "ide_selection",
               "bash-stderr", "user-prompt-submit-hook")


def _clean_user_text(text):
    """Tách lời người dùng khỏi phần hệ thống chèn vào.

    Trả về (lời_người_dùng, [đoạn_dán], lệnh_shell, output_shell).
    - <pasted_content>: người dùng dán từ nơi khác, thường là log hay lời Claude. Giữ nhưng tách riêng.
    - <bash-input>: lệnh người dùng tự gõ bằng `!`. Đây là hành động thật của người dùng.
    """
    pasted = re.findall(r"<pasted_content[^>]*>(.*?)</pasted_content[^>]*>", text, flags=re.S)
    text = re.sub(r"<pasted_content[^>]*>.*?</pasted_content[^>]*>", "", text, flags=re.S)
    bash_in = " ; ".join(x.strip() for x in re.findall(r"<bash-input>(.*?)</bash-input>", text, flags=re.S))
    bash_out = " ".join(x.strip() for x in re.findall(r"<bash-stdout>(.*?)</bash-stdout>", text, flags=re.S))
    text = re.sub(r"<(bash-input|bash-stdout)>.*?</\1>", "", text, flags=re.S)
    for tag in _NOISE_TAGS:
        text = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", text, flags=re.S)
    return text.strip(), [p.strip() for p in pasted if p.strip()], bash_in, bash_out


# Chuỗi trông như bí mật. Chat thường chứa token, mật khẩu, connection string bị dán vào.
_SECRET_PATTERNS = [
    r"sk-ant-[A-Za-z0-9_-]{20,}", r"\bsk-[A-Za-z0-9]{32,}",
    r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})",
    r"\bAKIA[0-9A-Z]{16}\b", r"\bxox[baprs]-[A-Za-z0-9-]{10,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
    r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
    r"\bshp(?:at|ss|ca|pa)_[a-fA-F0-9]{20,}", r"\bvercel_blob_rw_[A-Za-z0-9_]{20,}",
    r"\bAIza[0-9A-Za-z_-]{35}", r"\b(?:sk|rk|pk)_(?:live|test)_[A-Za-z0-9]{20,}",
    r"Bearer\s+[A-Za-z0-9._~+/-]{20,}=*",
]
_SECRET_RE = re.compile("|".join(_SECRET_PATTERNS))
_URL_CRED_RE = re.compile(r"(\b[a-z][a-z0-9+.-]*://[^\s:/@]+:)[^\s@/]+(@)", re.I)
_KV_SECRET_RE = re.compile(
    r"(?i)(\b[A-Z0-9_]*(?:PASSWORD|PASSWD|SECRET|TOKEN|API_?KEY|PRIVATE_?KEY|CREDENTIALS?)[A-Z0-9_]*\s*[:=]\s*[\"']?)"
    r"([^\s\"']{8,})")


def redact(text):
    """Che bí mật trước khi chat rời khỏi ~/.claude. Không hoàn hảo, nên chat vẫn không vào git."""
    text = _SECRET_RE.sub("[REDACTED]", text)
    text = _URL_CRED_RE.sub(r"\1[REDACTED]\2", text)
    return _KV_SECRET_RE.sub(r"\1[REDACTED]", text)


_UNTRUSTED_TAG_RE = re.compile(r"<\s*/?\s*untrusted\s*>", re.I)
_LINE_BREAK_RE = re.compile(r"\r\n?|[\u2028\u2029\x85\x0b\x0c\x1c\x1d\x1e]")

def untrusted(text):
    """Bọc dữ liệu không tin cậy. Nội dung không được tự đóng thẻ hay mở heading mới, vì ingest
    và _turns dựa vào dòng `### <người nói>` để biết ai nói: không trung hoà thì tin LARK-OTHER,
    lời CLAUDE hay ghi chú agent có thể giả làm `### USER` / `### LARK-USER`."""
    # Mọi kiểu xuống dòng (\r, \u2028, \x85...) về \n trước: LLM có thể coi chúng là dòng mới
    # dù regex ^ và _turns chỉ tách ở \n.
    t = _LINE_BREAK_RE.sub("\n", text)
    t = _UNTRUSTED_TAG_RE.sub("[tag]", t)
    t = re.sub(r"(?m)^(\s*)[#＃]", r"\1\\#", t)
    return f"<untrusted>\n{t}\n</untrusted>\n"

def one_line(text, limit=120):
    """Tên chat, tên người nói, tiêu đề: một dòng, không chứa chuỗi đóng comment HTML."""
    return " ".join(str(text).split()).replace("-->", "->")[:limit]

# Ghi chú theo hệ điều hành

Đọc phần của OS hiện tại khi cài đặt hoặc scheduler gặp lỗi.

## Cài git (khuyến nghị, không bắt buộc)

Không có git thì brain lưu bằng bản chụp `logs/snapshots/*.zip` (`init --no-git`). Cài git để quay lại từng thay đổi,
dùng nhiều máy, sao lưu lên GitHub. Cài xong mở terminal mới, `git --version` phải ra số phiên bản, rồi đặt tên một lần:
`git config --global user.name "<tên>"` và `git config --global user.email "<email>"`.
- **macOS:** `xcode-select --install` (hộp thoại "Install", vài phút). Có Homebrew thì `brew install git`.
- **Ubuntu / WSL:** `sudo apt update && sudo apt install -y git`.
- **Windows:** `winget install --id Git.Git -e`, hoặc tải ở git-scm.com (cứ bấm Next). Mở lại terminal sau khi cài.
- Máy công ty không cho cài: dùng `--no-git`, sau này có git thì `git init && git add -A && git commit -m "init"` trong brain.

## macOS

- Scheduler: launchd. Plist ghi vào `~/Library/LaunchAgents/com.secondbrain.<tên-brain>.<job>.plist`.
- launchd chạy bù lần lỡ khi máy ngủ dậy, nên không cần lo máy hay sleep.
- `claude` thường ở `~/.local/bin/claude`. launchd không đọc `.zshrc`, nhưng `brain.py` tự dò các đường dẫn phổ biến.
- Job nền thường KHÔNG đọc được đăng nhập Claude (nằm trong Keychain). Lỗi "OAuth session expired" / `401` trong log:
  chưa có `private/claude.env`, chạy `set-token`. Trên macOS nên tạo token ngay khi bật job nền.

## Ubuntu / Linux

- Scheduler: crontab của user. Dòng của brain có đuôi `# secondbrain:<tên-brain>:<job>`, các dòng cron khác được giữ nguyên.
- Cần daemon cron đang chạy: `systemctl status cron`. Trên WSL thường chưa bật: `sudo service cron start`. Muốn tự bật khi mở WSL, thêm vào `/etc/wsl.conf`:
  ```
  [boot]
  command = service cron start
  ```
- Cron có PATH rất ngắn. Nếu cài Claude Code qua nvm, `brain.py` tự dò `~/.nvm/versions/node/*/bin/claude`. Nếu vẫn không thấy, kiểm tra `which claude` trong shell thường rồi báo người dùng.
- Cron bỏ qua lần chạy khi máy tắt hoặc ngủ. Không sao: lần chạy sau sẽ bù, và file inbox quá 3 giờ chưa ai nạp thì máy khác nhận.
- Python: Ubuntu 22.04+ có sẵn `python3` đủ mới. Không cần cài gói Python nào.
- Token: cron chạy cùng user nên thường đọc được đăng nhập Claude (`~/.claude/.credentials.json`), không cần `set-token`.
  Log có `401` / `Not logged in` thì mới tạo token.

## Windows

- Scheduler: Task Scheduler, task nằm trong thư mục `SecondBrain\<tên-brain>\`. Xem bằng `schtasks /Query /TN SecondBrain\<tên-brain>\sync`.
- Dùng `py -3` thay `python3`. Nếu không có `py`, cài Python từ python.org và tick "Add to PATH".
- Task chạy bằng `pythonw.exe` nên không bật cửa sổ console mỗi giờ.
- Task chỉ chạy khi user đã đăng nhập. Máy hay tắt vẫn ổn, máy khác nạp hộ inbox quá 3 giờ.
- Git: dùng Git for Windows. Credential Manager đi kèm lưu được token HTTPS, phù hợp cho job không tương tác.
- `.gitattributes` của repo ép LF, nên không cần chỉnh `core.autocrlf`.
- Lỗi "Access is denied" khi `schedule install`: mở terminal thường (không cần admin) và chạy lại. Nếu chính sách công ty chặn Task Scheduler, báo người dùng chạy `sync` và `run ingest` bằng tay hoặc hỏi IT.
- Đường dẫn repo có dấu cách vẫn chạy được, nhưng nếu gặp lỗi lạ thì nên clone vào đường dẫn không có dấu cách, ví dụ `C:\MyBrain`.

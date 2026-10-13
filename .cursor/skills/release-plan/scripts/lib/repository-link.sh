# shellcheck shell=bash
# Resolve GitHub repository base URL from git remote.
repository_link() {
  python3 - "${1:-}" <<'PY'
import re, subprocess, sys
from typing import Optional

u = (sys.argv[1] or "").strip()

def from_remote(url: str) -> Optional[str]:
    m = re.match(r"(?:git@github\.com:|ssh://git@github\.com/)(.+?)(?:\.git)?/?$", url)
    if m:
        return f"https://github.com/{m.group(1)}"
    m = re.match(r"https?://github\.com/(.+?)(?:\.git)?/?$", url)
    if m:
        return f"https://github.com/{m.group(1)}"
    return None

if not u:
    try:
        u = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        print("")
        raise SystemExit

link = from_remote(u)
print(link or "")
PY
}

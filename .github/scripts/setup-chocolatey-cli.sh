#!/usr/bin/env bash
set -euo pipefail

if command -v choco >/dev/null 2>&1 && choco --version >/dev/null 2>&1; then
  echo "choco already available: $(choco --version)"
  exit 0
fi

if [[ "${RUNNER_OS:-}" == "Windows" ]]; then
  echo "Chocolatey CLI is expected on Windows runners; choco not found on PATH." >&2
  exit 1
fi

CHOCO_VERSION="${CHOCO_VERSION:-2.7.3}"
CHOCO_DIR="/opt/chocolatey"
CHOCO_URL="https://github.com/chocolatey/choco/releases/download/${CHOCO_VERSION}/chocolatey.v${CHOCO_VERSION}.tar.gz"

echo "Installing Chocolatey CLI ${CHOCO_VERSION} (mono) for choco pack…"
sudo apt-get update -qq
sudo apt-get install -y -qq mono-complete

sudo mkdir -p "${CHOCO_DIR}"
curl -fsSL "${CHOCO_URL}" -o /tmp/chocolatey.tar.gz
sudo tar -xzf /tmp/chocolatey.tar.gz -C "${CHOCO_DIR}"
rm -f /tmp/chocolatey.tar.gz

CHOCO_EXE="${CHOCO_DIR}/choco.exe"
if [[ ! -f "${CHOCO_EXE}" && -f "${CHOCO_DIR}/net48/choco.exe" ]]; then
  CHOCO_EXE="${CHOCO_DIR}/net48/choco.exe"
fi

if [[ ! -f "${CHOCO_EXE}" ]]; then
  echo "choco.exe not found under ${CHOCO_DIR}" >&2
  exit 1
fi

printf '#!/usr/bin/env bash\nexec mono %q "$@"\n' "${CHOCO_EXE}" | sudo tee /usr/local/bin/choco >/dev/null
sudo chmod +x /usr/local/bin/choco

if [[ -n "${GITHUB_PATH:-}" ]]; then
  echo "/usr/local/bin" >> "${GITHUB_PATH}"
fi
export PATH="/usr/local/bin:${PATH}"

if ! command -v choco >/dev/null 2>&1 || ! choco --version >/dev/null 2>&1; then
  echo "Chocolatey CLI installation failed; choco is not available." >&2
  exit 1
fi

echo "choco installed: $(choco --version)"

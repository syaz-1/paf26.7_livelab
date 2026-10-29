#!/usr/bin/env bash
# Run explicitly on the disposable Oracle Linux 9 target VM, never the PAF host.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Run with sudo on the dedicated target VM.' >&2; exit 1; }
[[ ${1:-} == --dedicated-lab-vm ]] || { echo 'Usage: sudo bash setup.sh --dedicated-lab-vm' >&2; exit 1; }
source /etc/os-release
[[ $ID == ol && $VERSION_ID == 9* ]] || { echo 'Oracle Linux 9 required.' >&2; exit 1; }
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source_dir=$(cd -- "$script_dir/.." && pwd)
[[ ! -e /etc/paf-linux-lab ]] || { echo 'Existing lab configuration found; inspect it before updating.' >&2; exit 1; }
[[ ! -e /opt/paf-linux-lab ]] || { echo 'Existing lab installation found; inspect it before updating.' >&2; exit 1; }
dnf install -y python3.11 python3.11-pip
if ! getent passwd paf-health >/dev/null; then
    useradd --system --user-group --home-dir /nonexistent --shell /sbin/nologin paf-health
fi
install -d -m 755 /opt/paf-linux-lab
install -m 644 "$source_dir/server.py" "$source_dir/collectors.py" "$source_dir/requirements.txt" /opt/paf-linux-lab/
python3.11 -m venv /opt/paf-linux-lab/venv
/opt/paf-linux-lab/venv/bin/python -m pip install -r /opt/paf-linux-lab/requirements.txt
install -d -m 750 -o root -g paf-health /etc/paf-linux-lab
python3.11 -c 'import secrets; print(secrets.token_urlsafe(48))' > /etc/paf-linux-lab/token
chown root:paf-health /etc/paf-linux-lab/token
chmod 640 /etc/paf-linux-lab/token
install -d -m 755 /var/lib/paf-linux-lab/disk
touch /etc/paf-linux-lab/dedicated-vm-marker
install -m 644 "$script_dir/paf-linux-mcp.service" "$script_dir/paf-lab-demo.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now paf-lab-demo.service
echo 'Installed. Follow README TLS/network steps before starting paf-linux-mcp.'
echo 'The token is in /etc/paf-linux-lab/token; it has not been printed.'

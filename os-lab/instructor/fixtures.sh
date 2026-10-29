#!/usr/bin/env bash
# All mutations are instructor-only; none are reachable through MCP.
set -euo pipefail
[[ $EUID -eq 0 && -f /etc/paf-linux-lab/dedicated-vm-marker ]] || {
    echo 'Requires sudo and an installed dedicated lab VM.' >&2; exit 1;
}
lab_mount=/var/lib/paf-linux-lab/disk
assert_disk() {
    [[ ! -L $lab_mount ]] || { echo 'Refusing symlink mount.' >&2; exit 1; }
    [[ $(findmnt -rn -M "$lab_mount" -o FSTYPE) == tmpfs &&
       $(findmnt -rn -M "$lab_mount" -o SOURCE) == paf-lab-disk &&
       $(findmnt -brn -M "$lab_mount" -o SIZE) == 67108864 ]] || {
        echo 'Expected the lab-owned 64 MiB tmpfs; refusing this filesystem.' >&2; exit 1;
    }
}
case ${1:-} in
    prepare)
        if ! mountpoint -q "$lab_mount"; then
            [[ -z $(find "$lab_mount" -mindepth 1 -maxdepth 1 -print -quit) ]] || {
                echo 'Refusing to hide files beneath the lab mount.' >&2; exit 1;
            }
            # A 64 MiB tmpfs needs sufficient available RAM, independent of swap.
            awk '/MemAvailable:/ {exit ($2 < 262144)}' /proc/meminfo || {
                echo 'At least 256 MiB available RAM required.' >&2; exit 1;
            }
            mount -t tmpfs -o size=64m,nr_inodes=4096,nosuid,nodev,noexec,mode=0755 paf-lab-disk "$lab_mount"
        fi
        assert_disk
        systemctl start paf-lab-demo.service
        ;;
    disk-full)
        assert_disk
        [[ ! -e $lab_mount/pressure.bin && ! -L $lab_mount/pressure.bin ]] || {
            echo 'Disk fixture exists; reset it first.' >&2; exit 1;
        }
        # Fixed allocation: cannot grow beyond this tiny dedicated filesystem.
        /usr/bin/python3.11 - <<'PY'
with open('/var/lib/paf-linux-lab/disk/pressure.bin', 'xb', buffering=0) as target:
    block = bytes(1024 * 1024)
    for _ in range(58):
        target.write(block)
PY
        ;;
    cpu-load)
        systemd-run --unit=paf-lab-cpu --collect --property=RuntimeMaxSec=120 \
            --property=CPUQuota=100% --property=MemoryMax=64M \
            --property=NoNewPrivileges=yes --property=DynamicUser=yes \
            /usr/bin/python3.11 -c 'while True: pass'
        ;;
    service-stop) systemctl stop paf-lab-demo.service ;;
    reset)
        assert_disk
        rm -f -- "$lab_mount/pressure.bin"
        if systemctl is-active --quiet paf-lab-cpu.service; then
            systemctl stop paf-lab-cpu.service
        fi
        systemctl start paf-lab-demo.service
        ;;
    unmount)
        assert_disk
        [[ ! -e $lab_mount/pressure.bin ]] || { echo 'Reset before unmounting.' >&2; exit 1; }
        umount "$lab_mount"
        ;;
    *) echo 'Usage: sudo bash fixtures.sh {prepare|disk-full|cpu-load|service-stop|reset|unmount}' >&2; exit 1 ;;
esac

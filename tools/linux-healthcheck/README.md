# linux-healthcheck

A small, read-only Linux health check that runs with the Python standard library only. It is designed for first-pass diagnostics and portfolio demonstrations, not as a replacement for monitoring or a distribution's support tools.

## What it checks

- distribution, kernel and architecture;
- uptime and load relative to CPU count;
- available memory;
- root filesystem usage;
- failed `systemd` units when `systemctl` exists;
- incomplete Debian/Ubuntu package operations when `dpkg` exists;
- DKMS entries that are not marked `installed` when `dkms` exists;
- the Debian/Ubuntu reboot-required marker.

Every operation is read-only. The tool does not call `sudo`, install packages, restart services, edit configuration or upload data.

## Quick start

Python 3.9 or newer is the only required runtime.

```bash
cd tools/linux-healthcheck
PYTHONPATH=src python3 -m linux_healthcheck
```

Run selected checks or request JSON:

```bash
PYTHONPATH=src python3 -m linux_healthcheck --check memory --check disk
PYTHONPATH=src python3 -m linux_healthcheck --json
```

## Single-file portable build

Build a `.pyz` with Python itself:

```bash
python3 scripts/build_zipapp.py
python3 dist/linux-healthcheck.pyz
```

Copy `dist/linux-healthcheck.pyz` to another Linux machine and run it with Python 3.9+. No installation is needed. The shebang also permits `./dist/linux-healthcheck.pyz` after `chmod +x` on systems where `/usr/bin/env python3` is available.

## Optional installation

For a normal command in an isolated environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install .
linux-healthcheck
```

Installing from the source package can require a current `setuptools` build backend. The `.pyz` path avoids that packaging requirement.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | No warning or critical result |
| `1` | At least one warning or critical result; review the output |
| `2` | Unsupported platform or the check could not start |

An unavailable optional command is reported as `SKIP` and does not by itself make the exit code non-zero.

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Tests use a fake host adapter. They do not inspect or change the developer machine.

## Portability limits

- Linux and Python 3.9+ are required. It intentionally refuses to run on macOS or Windows.
- `/proc` is expected for uptime and memory. Containers may expose host-limited or namespace-specific values.
- `systemctl`, `dpkg` and `dkms` are optional. Alpine, Fedora, minimal containers and non-systemd distributions will skip checks that do not apply.
- Thresholds are conservative defaults, not capacity-planning rules. Short load spikes can be harmless.
- The root filesystem is checked; other application/data mounts are not yet discovered automatically.
- A clean result cannot prove that hardware, backups, applications or network paths are healthy.
- Some service managers restrict status visibility. The tool reports that check as unavailable instead of requesting privileges.

## User setup checklist

1. Confirm `python3 --version` is 3.9 or newer.
2. Copy the `.pyz` or clone the repository.
3. Run as the normal user first; do not use `sudo` just to get more output.
4. Read every warning before taking action. This tool deliberately makes no fixes.
5. For recurring monitoring, send the JSON output to a separate monitoring system rather than modifying this tool to make automatic repairs.

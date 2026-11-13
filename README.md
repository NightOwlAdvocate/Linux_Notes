# Linux Notes 🐧

Hands-on Linux administration, debugging, system recovery, and small operational tools. The repository separates verified case studies from learning notes and future work so that portfolio claims stay evidence-based.

## Repository map

```text
Ubuntu/                    Existing Ubuntu recovery case studies (paths preserved)
docs/case-studies/         Case-study index and evidence boundaries
docs/learning/             Short, practical learning plans
docs/roadmap/              Portfolio status: completed vs planned
tools/linux-healthcheck/   Portable read-only Python health check with tests
```

The original `Ubuntu/` files remain at their existing paths to avoid breaking links.

## Ubuntu — practical case studies

| Case study | System | Outcome |
| --- | --- | --- |
| [CS8409 audio recovery on iMac18,1, Linux 7.0.0-42](Ubuntu/imac18-1-cs8409-linux-7.0.0-42-2026-11-05.md) | Ubuntu 24.04 HWE, kernel 7.0.0-42 | **Built-in speaker sound restored**, after kernel/DKMS recovery, exact Ubuntu-source build, and installing a test module |
| [Original iMac18,1 sound fix on kernel 6.17](Ubuntu/imac-audio-cs8409-fix.md) | Ubuntu 24.04, kernel 6.17.0-35 | Previously working DKMS-backed Cirrus CS8409 driver |

### Notes

- The Linux 7.0 case uses **an experimental, manually installed module**, not production-ready DKMS automation. Review its recovery and maintenance sections before repeating any commands.
- The original 6.17 instructions should **not be applied verbatim** to newer Ubuntu HWE kernels.
- Exact hardware matters: **iMac18,1 / CS8409 / subsystem 0x106b0e00**.

## Topics demonstrated

Kernel & initramfs recovery · GRUB · APT/dpkg troubleshooting · DKMS · ALSA/PipeWire · hardware IDs · Git merges · Ubuntu HWE source matching · kernel-module compilation · rollback planning.

## Tools

### [linux-healthcheck](tools/linux-healthcheck/README.md)

A Python 3.9+ CLI for read-only first-pass Linux diagnostics. It uses only the standard library at runtime, supports JSON output, skips distribution-specific checks when they do not apply, and includes a single-file `.pyz` build path and automated tests.

## Learning and portfolio planning

- [Case-study index and evidence rules](docs/case-studies/README.md)
- [Two-day Kubernetes plan for ChronoRec and MinFri (Russian)](docs/learning/kubernetes-two-day-plan.ru.md)
- [Canonical-focused portfolio status and next steps](docs/roadmap/canonical-portfolio.md)

> **Safety:** Do not run experimental kernel module installation commands on other machines without a backup and tested recovery path.

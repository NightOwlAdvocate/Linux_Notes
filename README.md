# Linux Notes 🐧

Hands-on Linux administration, debugging, system recovery, and kernel experiments.

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

> **Safety:** Do not run experimental kernel module installation commands on other machines without a backup and tested recovery path.

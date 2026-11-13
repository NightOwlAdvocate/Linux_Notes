# Linux case studies

## Verified work

| Case | Verified outcome | Important limit |
| --- | --- | --- |
| [iMac18,1 / CS8409 on Linux 7.0.0-42](../../Ubuntu/imac18-1-cs8409-linux-7.0.0-42-2026-11-05.md) | The user confirmed that built-in speaker output returned after reboot with the locally built module. | Post-reboot kernel logs, microphone/headphone tests and long-term stability were not captured. The module was not managed by DKMS. |
| [Earlier CS8409 repair on Linux 6.17.0-35](../../Ubuntu/imac-audio-cs8409-fix.md) | DKMS module installation and the working module path were recorded for the earlier kernel. | The old build/install steps must not be reused blindly on newer HWE kernels. |

The 7.0 case also documents recovery around GRUB, initramfs, incomplete package configuration and a legacy DKMS module that blocked kernel package configuration.

## Evidence rule

A portfolio case should say exactly what was observed. Compilation is not proof of runtime safety; a clean package audit is not proof that every service works; one successful boot is not a long-term stability test.

## Kernel panic positioning

The current repository contains evidence of boot/initramfs trouble and the risk of an out-of-tree module causing a hang or crash. It does **not** contain a captured panic trace that proves a specific kernel panic was diagnosed. Until a trace, journal excerpt or photo and a reproducible cause are available, describe this as a **boot and kernel-module recovery case**, not as a completed kernel-panic root-cause analysis.

If a future panic occurs, preserve:

- exact kernel and hardware identity;
- the panic text or a readable photo;
- previous-boot logs from `journalctl -k -b -1` when available;
- the last package/module change;
- the safe recovery path and rollback result.

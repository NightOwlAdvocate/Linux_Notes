# Canonical-focused portfolio status

This page deliberately separates repository evidence from intentions.

## Completed and demonstrable

- **Ubuntu/iMac recovery:** GRUB and initramfs recovery, `dpkg`/APT repair, DKMS isolation, exact Ubuntu HWE source matching, kernel-module compilation and rollback planning are documented in the existing case studies.
- **Linux healthcheck:** a read-only Python CLI now has a standard-library runtime, JSON output, portable zipapp build, tests, packaging metadata and documented limits.
- **ChronoRec Kubernetes lab:** the separate public repository contains a synthetic API, Docker image, local two-node `kind` cluster, Helm chart, CI smoke test, Prometheus/Grafana setup and reproducible failure exercises. This is verified local lab work, not production-cluster experience.
- **MinFri software prototype:** the private repository currently documents a local backend/Face UI, state machine, WebSocket flow, tests and push-to-talk using deterministic fake STT/LLM/TTS providers. Real voice providers, memory and hardware remain incomplete.

## Next, small public evidence

1. Run the healthcheck tests in GitHub Actions on multiple supported Python versions.
2. Run the `.pyz` on Ubuntu and save sanitized example text and JSON output.
3. Add one short case study showing how a warning was investigated without making automatic changes.
4. Select one bounded Ubuntu QA/CODA task: reproduce the issue, record the exact environment, submit the requested evidence or patch, and link the public result.

Do not describe the QA/CODA item as a contribution until the public report, merge request or accepted result exists.

## Later, after the MVP

- Replace MinFri's fake providers one boundary at a time and keep local tests deterministic.
- Containerize only the stable service boundary; do not put early hardware experiments behind Kubernetes.
- Try MicroK8s on an Ubuntu machine **after** the software MVP works reliably without Kubernetes.
- Compare the same synthetic ChronoRec workload on `kind` and MicroK8s, documenting operational differences rather than claiming production experience.
- Consider a multi-machine or edge deployment only when there is a real availability, update or device-management problem to solve.

## Portfolio wording

Use: “Built and verified a local Kubernetes lab with kind, Helm, CI and observability; documented failure recovery.”

Avoid: “Operated production Kubernetes” or “deployed MinFri on MicroK8s” until those statements are true and evidenced.

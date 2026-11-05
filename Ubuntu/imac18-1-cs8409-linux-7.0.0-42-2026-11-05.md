# Restoring iMac18,1 audio on Ubuntu 24.04 HWE kernel 7.0.0-42

> **Outcome (5 November 2026): Internal speaker playback restored after reboot with a locally built CS8409 module.**
>
> This is a documented, machine-specific experiment, **not** a general-purpose safe installer. An out-of-tree kernel module can hang or crash the kernel even when it compiles successfully. Back up important data and keep working recovery media before following any installation step.
>
> This guide continues the [earlier successful CS8409 fix on kernel 6.17.0-35](imac-audio-cs8409-fix.md). The goal here was to **stay on kernel 7.0**, not downgrade.

## Tested environment

| Component | Value |
|---|---|
| Computer | Apple iMac18,1 |
| Distribution | Ubuntu 24.04 LTS (Noble), HWE kernel |
| Kernel during build/install | `7.0.0-42-generic` |
| Installed kernel image package | `7.0.0-42.42~24.04.1` |
| Architecture | x86_64 |
| Audio controller | Intel HDA (PCH) |
| Codec | Cirrus Logic CS8409 |
| Codec vendor ID | `0x10138409` |
| Codec subsystem ID | `0x106b0e00` |
| Audio stack | ALSA + PipeWire / WirePlumber |
| Original module | `kernel/sound/hda/codecs/cirrus/snd-hda-codec-cs8409.ko.zst` |
| Replacement module | `updates/snd-hda-codec-cs8409.ko` |
| Secure Boot | `mokutil --sb-state` reported *This system doesn't support Secure Boot* |

**Evidence boundary:** The user confirmed that speaker sound returned after installing the replacement module and rebooting. A *post-reboot* kernel log, microphone test, headphone test, long-term stability test, and final `uname -r` capture were not provided. Do not treat those as verified.

## Symptoms and background

After a kernel update, Ubuntu had boot/initramfs trouble and `dpkg` reported four incompletely configured packages:

- `linux-image-7.0.0-28-generic`
- `linux-headers-7.0.0-28-generic`
- `linux-headers-generic-hwe-24.04`
- `linux-generic-hwe-24.04`

The missing initramfs for `7.0.0-28` had been recreated in recovery, followed by updating GRUB. The machine was **installed on its internal SSD**, not running from the USB installer:

```bash
findmnt -no SOURCE,FSTYPE /
# /dev/nvme0n1p2 ext4
```

Package configuration was blocked because the pre-existing DKMS module `snd_hda_macbookpro/0.1` attempted to build against kernel 7.0:

```text
dkms autoinstall on 7.0.0-28-generic/x86_64 failed for snd_hda_macbookpro(10)
run-parts: /etc/kernel/header_postinst.d/dkms exited with return code 11
```

The DKMS make log reported:

```text
Makefile:199: *** specified external module directory
"/var/lib/dkms/snd_hda_macbookpro/0.1/build/build/hda" does not exist.
```

The installer also could not find `/usr/src/linux-source-7.0.0.tar.bz2`, which is not normally provided as an ordinary `linux-source` package for this Ubuntu HWE kernel.

### Separating the package problem from the audio problem

To unblock `dpkg`, the previous repair deliberately restricted auto-building of this one legacy DKMS driver:

```bash
printf 'BUILD_EXCLUSIVE_KERNEL="^6[.]17[.]"\n' |
  sudo tee /etc/dkms/snd_hda_macbookpro-0.1.conf
sudo dpkg --configure -a
sudo dpkg --audit
```

**Why:** This temporary compatibility guard kept the existing DKMS installation for 6.17 and skipped unsupported 7.0 builds. It did **not** restore audio on 7.0.

Afterwards the normal APT upgrade installed `7.0.0-42-generic`, built its initramfs and updated GRUB. `dpkg --audit` was empty, and `systemctl --failed` showed 0 failed system units. The iMac booted kernel 7.0.0-42, but the built-in speakers remained silent. **Do not remove or relax that DKMS guard without redesigning the DKMS build.**

## 1. Diagnose CS8409 and confirm the hardware match

```bash
uname -r
cat /sys/class/dmi/id/product_name
grep -E '^(Codec|Vendor Id|Subsystem Id):' /proc/asound/card0/codec#0
aplay -l
wpctl status
pactl list short sources
modinfo -n snd_hda_codec_cs8409
```

Observed:

```text
iMac18,1
Codec: Cirrus Logic CS8409
Vendor Id: 0x10138409
Subsystem Id: 0x106b0e00

card 0: PCH [HDA Intel PCH], device 0: CS8409 Analog
PipeWire sink: Built-in Audio Analog Stereo
```

The standard module was selected from:

```text
/lib/modules/7.0.0-42-generic/kernel/sound/hda/codecs/cirrus/snd-hda-codec-cs8409.ko.zst
```

`pw-play /usr/share/sounds/alsa/Front_Center.wav` returned without an error, **but no sound came from the internal speakers**. This distinguishes a codec/initialisation problem from simply lacking an ALSA/PipeWire sink. Only a monitor source appeared in `pactl list short sources`; analog microphone functionality was not demonstrated.

The older kernel still had the previously working custom DKMS module:

```bash
dkms status
modinfo -k 6.17.0-35-generic -n snd_hda_codec_cs8409
# /lib/modules/6.17.0-35-generic/updates/dkms/snd-hda-codec-cs8409.ko.zst
```

The project's source contains explicit branches for `0x106b0e00`, including `cs_8409_boot_setup()` in `patch_cirrus/patch_cirrus_new84.h`. Its repository name says “macbookpro” for historical reasons; **hardware here is an iMac**.

## 2. Investigate upstream fixes without changing the installed driver

Upstream: [davidjo/snd_hda_macbookpro](https://github.com/davidjo/snd_hda_macbookpro)

Relevant *unmerged/experimental at the time* pull requests:

- [PR #200](https://github.com/davidjo/snd_hda_macbookpro/pull/200): DKMS paths, target kernel argument and Ubuntu HWE detection. **Fetched and reviewed; NOT merged in our local test branch.**
- [PR #216](https://github.com/davidjo/snd_hda_macbookpro/pull/216): Linux 7.0 / ALSA API compatibility. Used as the branch base.
- [PR #223](https://github.com/davidjo/snd_hda_macbookpro/pull/223): fetch matching Ubuntu HWE `sound/hda` sources. Merged into test branch. This PR was still draft at the time.

Keep the old DKMS source tree (`~/snd_hda_macbookpro`) untouched. Create a separate Git work area:

```bash
mkdir -p ~/kernel-audio-lab
git clone https://github.com/davidjo/snd_hda_macbookpro.git \
  ~/kernel-audio-lab/snd_hda_macbookpro
cd ~/kernel-audio-lab/snd_hda_macbookpro

git fetch origin pull/200/head:refs/remotes/origin/pr-200
git fetch origin pull/216/head:refs/remotes/origin/pr-216
git fetch origin pull/223/head:refs/remotes/origin/pr-223

git switch -c imac18-1-7.0.0-42-test origin/pr-216
git merge --no-commit --no-ff origin/pr-223
```

The merge conflicted **only in `README.md`**; the installer merged automatically. For this *specific* merge, we retained PR #216's README and committed the merged code:

```bash
git checkout --ours -- README.md
git add README.md
bash -n install.cirrus.driver.sh
bash -n prepare.ubuntu.hwe.source.sh
git diff --cached --check
git commit -m "Merge Linux 7.0 and Ubuntu HWE audio fixes"
git status --short
```

Local resulting commit: **`56d3e94`**. This was a **local Git commit**, not a commit in the public Linux_Notes repository, nor an upstream-merged PR. Git must have a name and email configured for merging.

**Note:** A clean merge and `bash -n` check do not prove that combined driver code is runtime-safe.

## 3. Obtain the exact Ubuntu HWE source tree

Running Ubuntu package: `linux-image-7.0.0-42-generic 7.0.0-42.42~24.04.1`.

Corresponding Ubuntu source tag:

```text
Ubuntu-hwe-7.0-7.0.0-42.42_24.04.1
```

We verified its existence:

```bash
git ls-remote --tags \
  https://git.launchpad.net/~ubuntu-kernel/ubuntu/+source/linux/+git/noble \
  'refs/tags/Ubuntu-hwe-7.0-7.0.0-42.42_24.04.1'
```

PR #223's helper prepared **just the matching `sound/hda` subtree** in the user's home directory, avoiding root:

```bash
cd ~/kernel-audio-lab/snd_hda_macbookpro
mkdir -p ~/kernel-audio-lab/ubuntu-source-cache

CS8409_SOURCE_DIR="$HOME/kernel-audio-lab/ubuntu-source-cache" \
CS8409_SOURCE_REPO="$HOME/kernel-audio-lab/ubuntu-kernel-git-cache" \
bash ./prepare.ubuntu.hwe.source.sh "7.0.0-42-generic"
```

Output included:

```text
Prepared Ubuntu HWE source Ubuntu-hwe-7.0-7.0.0-42.42_24.04.1 for 7.0.0-42-generic
```

Verify it:

```bash
cat ~/kernel-audio-lab/ubuntu-source-cache/.linux-source-7.0.0.ubuntu-version
tar -tjf ~/kernel-audio-lab/ubuntu-source-cache/linux-source-7.0.0.tar.bz2 |
  grep 'sound/hda/codecs/cirrus/cs8409.c'
```

Observed version: `7.0.0-42.42~24.04.1`. Using a matching distribution source is essential; **do not substitute an arbitrary mainline 7.0 tarball**.

## 4. Prepare and compile in a disposable copy (no sudo)

Make a build-only copy:

```bash
cd ~/kernel-audio-lab
cp -a snd_hda_macbookpro snd_hda_macbookpro-buildtest
cd snd_hda_macbookpro-buildtest
```

The installer originally expected `/usr/src/linux-source-7.0.0.tar.bz2` and could create a system update directory. For the **local preparation only**, we used this small Python edit in the buildtest copy:

```bash
python3 - <<'PY'
from pathlib import Path

p = Path("install.cirrus.driver.sh")
s = p.read_text()

old_source = "/usr/src/linux-source-$kernel_version.tar.bz2"
new_source = "$HOME/kernel-audio-lab/ubuntu-source-cache/linux-source-$kernel_version.tar.bz2"

assert s.count(old_source) >= 2, "Unexpected source path layout"
s = s.replace(old_source, new_source)

old_dir = "[[ ! $dkms_action == 'install' ]] && [[ ! -d $update_dir ]] && mkdir $update_dir"
assert old_dir in s, "Unexpected updates directory logic"
s = s.replace(old_dir, ': # local build: skip changes to /lib/modules')

p.write_text(s)
print("Local build script prepared successfully.")
PY
```

**Do not reuse this modified script as a privileged production installer.** The next invocation prepares files but deliberately omits DKMS installation:

```bash
bash -n install.cirrus.driver.sh
bash -n prepare.ubuntu.hwe.source.sh

CS8409_SOURCE_DIR="$HOME/kernel-audio-lab/ubuntu-source-cache" \
CS8409_SOURCE_REPO="$HOME/kernel-audio-lab/ubuntu-kernel-git-cache" \
bash ./install.cirrus.driver.sh -k 7.0.0-42-generic --dkms \
  > build-prep.log 2>&1
```

The output contained:

```text
Kernel version later than implemented version - there may be build problems
patching file codecs/cirrus/cs8409.c
patching file codecs/cirrus/cs8409.h
Hunk #1 ... fuzz 2
Hunk #4 ... fuzz 2
```

The fuzz warning means the patch matched after ignoring some context; its applicability needs review.

Check for rejected patches and compare the shared ALSA header to the Ubuntu source archive:

```bash
find build/hda -name '*.rej' -print

diff -u \
  <(tar -xOjf ~/kernel-audio-lab/ubuntu-source-cache/linux-source-7.0.0.tar.bz2 \
    linux-source-7.0.0/sound/hda/common/hda_local.h) \
  build/hda/common/hda_local.h
```

Both checks produced no output: no rejected patches, and the **local `hda_local.h` matched the archived Ubuntu version exactly**. This is a useful structural check, **not an ABI/runtime guarantee**.

In particular, Ubuntu's `struct hda_multi_out` contains `share_spdif_kctl`; PR #216's installer tests for the substring `spdif_kctl`, which also matches `share_spdif_kctl`. We did **not** manually add another struct member.

Compile:

```bash
set -o pipefail
make KERNELRELEASE="$(uname -r)" -j2 2>&1 | tee compile-7.0.0-42.log
echo "Build exit code: $?"

find build/hda -type f -name '*cs8409*.ko'
modinfo -F vermagic build/hda/codecs/cirrus/snd-hda-codec-cs8409.ko
sha256sum build/hda/codecs/cirrus/snd-hda-codec-cs8409.ko
```

Observed:

```text
Build exit code: 0
7.0.0-42-generic SMP preempt mod_unload modversions
442a40407e76da1c8fbb60c40e0ef5ad367f832383109568b62352cc0bfd7375
```

Build messages also warned about compiler naming, pahole/BTF, and missing `vmlinux` for BTF generation; they did not prevent the compiled `.ko` being created.

## 5. Install the test module alongside Ubuntu's stock module

**High-risk step — do not run automatically.** This is the *record of what was performed* on this specific iMac, not a universal safe procedure. Before such testing, have backups and a known working way to boot/rescue.

The following checks preceded installation:

```bash
lsinitramfs /boot/initrd.img-$(uname -r) |
  grep -Ei 'snd[-_]hda[-_]codec[-_]cs8409.*\.ko' || true
mokutil --sb-state
sudo find /lib/modules/7.0.0-42-generic/updates \
  -type f -iname '*cs8409*' -print 2>/dev/null
```

Observed: no CS8409 match in initramfs; Secure Boot unavailable; no replacement CS8409 found in `updates/`. The original distro module remained present at:

```text
/lib/modules/7.0.0-42-generic/kernel/sound/hda/codecs/cirrus/snd-hda-codec-cs8409.ko.zst
```

The test file was installed **without overwriting the original module**:

```bash
K="$(uname -r)"
SRC="$HOME/kernel-audio-lab/snd_hda_macbookpro-buildtest/build/hda/codecs/cirrus/snd-hda-codec-cs8409.ko"
DEST="/lib/modules/$K/updates/snd-hda-codec-cs8409.ko"

test -f "$SRC" && sha256sum "$SRC"
sudo install -D -m 0644 "$SRC" "$DEST"
sudo depmod -a "$K"

modinfo -F filename snd_hda_codec_cs8409
modprobe --show-depends snd_hda_codec_cs8409
```

`modinfo` and `modprobe --show-depends` selected:

```text
/lib/modules/7.0.0-42-generic/updates/snd-hda-codec-cs8409.ko
```

`lsmod` showed `snd_hda_codec_cs8409` already in memory, but that alone could not identify the version loaded *before* reboot. The new module would be selected on the next normal boot.

After the reboot, **the user confirmed the built-in speakers worked**. This is the successful outcome of the case study. No further stability claims are made.

## 6. Post-reboot verification / follow-up

Useful commands to run on the **working system** (not all have been supplied as post-reboot evidence):

```bash
uname -r
modinfo -F filename snd_hda_codec_cs8409
lsmod | grep '^snd_hda_codec_cs8409'
wpctl status
wpctl set-mute @DEFAULT_AUDIO_SINK@ 0
wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.15
pw-play /usr/share/sounds/alsa/Front_Center.wav

sudo journalctl -b -k --no-pager |
  grep -iE 'cs8409|cirrus|snd_hda|Oops:|BUG:|general protection fault' |
  tail -n 60
```

Next tests: headphones, internal microphone (PipeWire sources), suspend/resume, several cold boots, volume safety, and handling of the **next kernel update**.

## 7. Recovery: remove *only* the experimental 7.0 module

**If Ubuntu still boots:** remove just the test file, rebuild the module index, then reboot. This keeps kernel 7.0 installed.

```bash
sudo rm -f /lib/modules/7.0.0-42-generic/updates/snd-hda-codec-cs8409.ko
sudo depmod -a 7.0.0-42-generic
modinfo -F filename snd_hda_codec_cs8409
# Expected: .../kernel/sound/hda/codecs/cirrus/snd-hda-codec-cs8409.ko.zst
sudo reboot
```

**If the new module hangs during boot:** in GRUB, edit the **7.0.0-42** entry (press `e`), append `module_blacklist=snd_hda_codec_cs8409` to its `linux` command line and boot with `Ctrl+X`. If that enables a shell, remove the replacement as above; the parameter is only for that boot. If this fails, use a Live USB and remove the replacement file on the mounted system. Blacklisting the entire CS8409 module temporarily disables audio; it does **not** switch to the stock module in the same boot.

Keep `6.17.0-35` installed as a fallback package, but **no downgrade was needed for this successful 7.0 repair**.

## 8. Important maintenance caveat

**The 7.0.0-42 test module was installed manually, not registered through DKMS.** A subsequent kernel update will not automatically copy/rebuild it for the new kernel. Moreover, `/etc/dkms/snd_hda_macbookpro-0.1.conf` still contains:

```text
BUILD_EXCLUSIVE_KERNEL="^6[.]17[.]"
```

Therefore:

- Do **not** assume internal audio will persist after a future kernel change.
- Do **not** blindly run `git pull` or `sudo dkms install` using the older 6.17 guide for kernel 7.x.
- Do **not** copy this compiled `.ko` to a different kernel version.
- Re-evaluate upstream PRs, obtain the exact matching Ubuntu HWE sources, compile/test again and keep a boot recovery plan.
- Never delete the original stock module from `kernel/sound/`.
- The experimental code has not undergone a full kernel ABI safety audit.

## References

- [Earlier working 6.17 repair on the same iMac](imac-audio-cs8409-fix.md)
- [Upstream CS8409 project](https://github.com/davidjo/snd_hda_macbookpro)
- [PR #200 — DKMS/HWE fixes](https://github.com/davidjo/snd_hda_macbookpro/pull/200)
- [PR #216 — Linux 7.0 ALSA changes](https://github.com/davidjo/snd_hda_macbookpro/pull/216)
- [PR #223 — exact Ubuntu HWE source](https://github.com/davidjo/snd_hda_macbookpro/pull/223)
- [Issue #201 — iMac18.x hard lockup warning](https://github.com/davidjo/snd_hda_macbookpro/issues/201)
- [Issue #205 — 7.0 HWE crash debugging](https://github.com/davidjo/snd_hda_macbookpro/issues/205)
- [Issue #222 — iMac 2017 kernel 7.0 audio difficulties](https://github.com/davidjo/snd_hda_macbookpro/issues/222)

---

**Takeaway:** The key engineering work was separating DKMS package failures from missing hardware initialisation, sourcing the **exact Ubuntu HWE `sound/hda` tree**, integrating 7.0 API fixes, validating the built module, preserving the stock driver, and testing on an actual `iMac18,1`. The user confirmed that the speakers work after reboot.

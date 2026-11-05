# Fixing No Sound on Ubuntu 24.04.4 LTS on iMac18,1 with Cirrus CS8409

> **Update — 5 November 2026:** This guide records the earlier successful repair on **kernel 6.17.0-35**. For Ubuntu 24.04 HWE **7.0.0-42**, do **not** blindly repeat the `git pull` / `dkms install` steps below: the older driver failed to build and blocked APT kernel configuration. See the [new, experimentally verified iMac18,1 Linux 7.0.0-42 repair](imac18-1-cs8409-linux-7.0.0-42-2026-11-05.md), which uses matching Ubuntu HWE source and an isolated build. The 7.0 module was installed manually and is **not automatically maintained by DKMS**.


## System

```text
Model: iMac18,1
Ubuntu: 24.04.4 LTS noble
Kernel: 6.17.0-35-generic
Architecture: x86_64
Audio device: Intel Sunrise Point-LP HD Audio
Codec: Cirrus Logic CS8409
Audio server: PulseAudio on PipeWire
```

## Problem

After installing Ubuntu on an older iMac, audio did not work anywhere in the system.

## Initial diagnostics

Checking Ubuntu version:

```bash
lsb_release -a
```

Checking kernel:

```bash
uname -a
```

Checking Mac/iMac model:

```bash
cat /sys/devices/virtual/dmi/id/product_name 2>/dev/null
cat /sys/devices/virtual/dmi/id/product_version 2>/dev/null
```

Checking audio devices:

```bash
lspci -nnk | grep -A4 -Ei "audio|multimedia|sound"
```

Output:

```text
00:1f.3 Audio device: Intel Corporation Sunrise Point-LP HD Audio
Kernel driver in use: snd_hda_intel
Kernel modules: snd_soc_avs, snd_sof_pci_intel_skl, snd_hda_intel
```

Checked ALSA playback devices:

```bash
aplay -l
```

According to output, the sound card was detected:

```text
card 0: PCH [HDA Intel PCH], device 0: CS8409 Analog [CS8409 Analog]
```

Checked PipeWire/PulseAudio:

```bash
pactl info
pactl list short sinks
systemctl --user --no-pager status pipewire pipewire-pulse wireplumber
```

PipeWire was active and the analog stereo sink existed:

```text
Default Sink: alsa_output.pci-0000_00_1f.3.analog-stereo
```

This meant that Ubuntu could see the audio device, but the standard kernel driver was not enough for the Apple/Cirrus CS8409 audio setup.

## Installed tools

```bash
sudo apt update
sudo apt install -y git build-essential dkms linux-headers-$(uname -r)
```

## Downloaded the patched driver

```bash
cd ~
git clone https://github.com/davidjo/snd_hda_macbookpro.git
cd snd_hda_macbookpro
```

## Tried installing the driver

```bash
sudo ./install.cirrus.driver.sh -i
```

After reboot, DKMS status was checked:

```bash
dkms status | grep -i hda
```

At first it showed:

```text
snd_hda_macbookpro/0.1: added
```

So, DKMS module was registered, but not built or installed.

`modinfo` still showed the standard kernel module:

```bash
modinfo snd_hda_codec_cs8409 | grep -E "filename|version|description"
```

Output:

```text
filename: /lib/modules/6.17.0-35-generic/kernel/sound/hda/codecs/cirrus/snd-hda-codec-cs8409.ko.zst
```

## Secure Boot check

```bash
mokutil --sb-state
```

Output:

```text
This system doesn't support Secure Boot
```

So Secure Boot was not blocking the custom module.

## DKMS build problem

Manual build:

```bash
sudo dkms build snd_hda_macbookpro/0.1 -k $(uname -r)
```

The build failed because the kernel source was missing:

```text
Ubuntu linux kernel source not found in /usr/src:
/usr/src/linux-source-6.17.0.tar.bz2
please install the linux kernel source package:
sudo apt install linux-source-6.17.0
```

The system only had source for kernel 6.8.0:

```bash
ls -lh /usr/src | grep linux-source
```

Output:

```text
linux-source-6.8.0
linux-source-6.8.0.tar.bz2 -> linux-source-6.8.0/linux-source-6.8.0.tar.bz2
```

But the running kernel was:

```text
6.17.0-35-generic
```

So the available 6.8.0 source did not match the running 6.17 kernel.

`apt` could not find the required package:

```bash
apt-cache policy linux-source-6.17.0
```

Output:

```text
Unable to locate package linux-source-6.17.0
```

## Installed the matching kernel source manually

Downloaded the matching source package for the current kernel:

```bash
cd ~/Downloads
wget http://archive.ubuntu.com/ubuntu/pool/main/l/linux/linux-source-6.17.0_6.17.0-35.35_all.deb
```

Installed it:

```bash
sudo apt install ./linux-source-6.17.0_6.17.0-35.35_all.deb
```

Checked that the source appeared:

```bash
ls -lh /usr/src | grep linux-source-6.17
```

## Built and installed the DKMS module

```bash
cd ~/snd_hda_macbookpro
sudo dkms build snd_hda_macbookpro/0.1 -k $(uname -r)
sudo dkms install snd_hda_macbookpro/0.1 -k $(uname -r)
sudo depmod -a
sudo reboot
```

After reboot, DKMS status showed:

```bash
dkms status | grep -i hda
```

Output:

```text
snd_hda_macbookpro/0.1, 6.17.0-35-generic, x86_64: installed
```

The loaded module path was checked again:

```bash
modinfo snd_hda_codec_cs8409 | grep -E "filename|version|description"
```

Expected successful output:

```text
filename: /lib/modules/6.17.0-35-generic/updates/dkms/snd-hda-codec-cs8409.ko.zst
description: Cirrus Logic HDA bridge
```

This confirmed that the DKMS-patched module was installed and used instead of the default kernel module.

## Useful verification commands

Check DKMS status:

```bash
dkms status | grep -i hda
```

Check which CS8409 module is used:

```bash
modinfo snd_hda_codec_cs8409 | grep -E "filename|version|description"
```

Check audio devices:

```bash
aplay -l
```

Check PipeWire/PulseAudio sinks:

```bash
pactl list short sinks
```

Restart audio services:

```bash
systemctl --user restart pipewire pipewire-pulse wireplumber
```

Test sound:

```bash
paplay /usr/share/sounds/alsa/Front_Center.wav
```

or:

```bash
speaker-test -c2 -t wav
```

Stop `speaker-test` with:

```text
Ctrl + C
```

## Notes for future kernel updates

After a kernel update, audio may stop working again if the DKMS module is not automatically rebuilt.

Check:

```bash
dkms status | grep -i hda
```

If the module is not installed for the new kernel, rebuild/install it:

```bash
cd ~/snd_hda_macbookpro
git pull
sudo dkms build snd_hda_macbookpro/0.1 -k $(uname -r)
sudo dkms install snd_hda_macbookpro/0.1 -k $(uname -r)
sudo depmod -a
sudo reboot
```

If the build fails because kernel source is missing, install the matching `linux-source` package for the running kernel.

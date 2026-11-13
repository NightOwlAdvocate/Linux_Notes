import subprocess
import unittest
from collections import namedtuple

from linux_healthcheck.checks import check_disk, check_dkms, check_memory, check_packages


Uname = namedtuple("Uname", "system node release version machine processor")
DiskUsage = namedtuple("DiskUsage", "total used free")


class FakeHost:
    def __init__(self, files=None, commands=None, executables=None, disk=None):
        self.files = files or {}
        self.commands = commands or {}
        self.executables = executables or {}
        self.disk = disk or DiskUsage(100, 50, 50)

    def read_text(self, path):
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def exists(self, path):
        return path in self.files

    def which(self, command):
        return self.executables.get(command)

    def run(self, command, timeout=5):
        return self.commands[command[0]]

    def disk_usage(self, path):
        return self.disk

    def uname(self):
        return Uname("Linux", "host", "6.8.0", "", "x86_64", "")

    def load_average(self):
        return (0.5, 0.3, 0.2)

    def cpu_count(self):
        return 4


class MemoryTests(unittest.TestCase):
    def test_memory_is_ok_above_warning_threshold(self):
        host = FakeHost(files={"/proc/meminfo": "MemTotal: 1000 kB\nMemAvailable: 500 kB\n"})
        result = check_memory(host)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.metrics["available_percent"], 50.0)

    def test_memory_is_critical_at_five_percent(self):
        host = FakeHost(files={"/proc/meminfo": "MemTotal: 1000 kB\nMemAvailable: 50 kB\n"})
        self.assertEqual(check_memory(host).status, "critical")


class DiskTests(unittest.TestCase):
    def test_disk_warns_at_ninety_percent(self):
        host = FakeHost(disk=DiskUsage(100, 90, 10))
        self.assertEqual(check_disk(host).status, "warning")

    def test_disk_is_critical_at_ninety_seven_percent(self):
        host = FakeHost(disk=DiskUsage(100, 97, 3))
        self.assertEqual(check_disk(host).status, "critical")


class OptionalCommandTests(unittest.TestCase):
    def test_missing_dpkg_is_skipped(self):
        self.assertEqual(check_packages(FakeHost()).status, "skip")

    def test_dpkg_audit_output_warns(self):
        completed = subprocess.CompletedProcess([], 0, "package-a is unpacked\n", "")
        host = FakeHost(commands={"/usr/bin/dpkg": completed}, executables={"dpkg": "/usr/bin/dpkg"})
        self.assertEqual(check_packages(host).status, "warning")

    def test_installed_dkms_entries_are_ok(self):
        completed = subprocess.CompletedProcess([], 0, "example/1.0, 6.8.0, x86_64: installed\n", "")
        host = FakeHost(commands={"/usr/sbin/dkms": completed}, executables={"dkms": "/usr/sbin/dkms"})
        self.assertEqual(check_dkms(host).status, "ok")

    def test_non_installed_dkms_entries_warn(self):
        completed = subprocess.CompletedProcess([], 0, "example/1.0: added\n", "")
        host = FakeHost(commands={"/usr/sbin/dkms": completed}, executables={"dkms": "/usr/sbin/dkms"})
        self.assertEqual(check_dkms(host).status, "warning")


if __name__ == "__main__":
    unittest.main()

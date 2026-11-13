import io
import json
import unittest
from unittest import mock

from linux_healthcheck.cli import main
from linux_healthcheck.models import CheckResult


class CliTests(unittest.TestCase):
    @mock.patch("linux_healthcheck.cli.platform.system", return_value="Darwin")
    def test_non_linux_returns_usage_error(self, _system):
        with mock.patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(main([]), 2)

    @mock.patch("linux_healthcheck.cli.collect_checks")
    @mock.patch("linux_healthcheck.cli.platform.system", return_value="Linux")
    def test_json_output_and_warning_exit_code(self, _system, collect):
        collect.return_value = [CheckResult("disk", "Disk", "warning", "90% used")]
        output = io.StringIO()
        with mock.patch("sys.stdout", output):
            exit_code = main(["--json", "--check", "disk"])
        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["overall_status"], "warning")
        self.assertEqual(payload["checks"][0]["check_id"], "disk")

    @mock.patch("linux_healthcheck.cli.collect_checks")
    @mock.patch("linux_healthcheck.cli.platform.system", return_value="Linux")
    def test_all_clear_returns_zero(self, _system, collect):
        collect.return_value = [CheckResult("memory", "Memory", "ok", "healthy")]
        with mock.patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(main([]), 0)


if __name__ == "__main__":
    unittest.main()

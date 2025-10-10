import contextlib
import importlib
import io
import types
import unittest
import warnings
from unittest import mock


def load_module():
    """Import the CLI module fresh for each test."""
    module = importlib.import_module("main")
    return importlib.reload(module)


class TestCliArguments(unittest.TestCase):
    def test_parse_args_supports_verbose_and_json(self):
        """--verbose should coexist with positional URL and --json flag."""
        main = load_module()

        parse_args = getattr(main, "parse_args", None)
        self.assertIsInstance(
            parse_args,
            types.FunctionType,
            msg="Expected main.parse_args to be a function handling CLI arguments.",
        )

        args = parse_args(["https://youtu.be/dQw4w9WgXcQ", "--json", "--verbose"])
        self.assertEqual(args.url, "https://youtu.be/dQw4w9WgXcQ")
        self.assertTrue(args.json)
        self.assertTrue(args.verbose)

        # Ordering should not matter for flags.
        args = parse_args(["--verbose", "https://youtu.be/dQw4w9WgXcQ"])
        self.assertEqual(args.url, "https://youtu.be/dQw4w9WgXcQ")
        self.assertFalse(args.json)
        self.assertTrue(args.verbose)

    def test_parse_args_requires_url(self):
        """Missing positional URL should exit with an error."""
        main = load_module()
        parse_args = main.parse_args

        with self.assertRaises(SystemExit):
            parse_args([])

    def test_parse_args_rejects_unknown_flag(self):
        """Unknown flags should trigger argparse error (SystemExit)."""
        main = load_module()
        parse_args = main.parse_args

        with self.assertRaises(SystemExit):
            parse_args(["https://youtu.be/dQw4w9WgXcQ", "--bogus"])


class TestWarningBehavior(unittest.TestCase):
    url = "https://youtu.be/dQw4w9WgXcQ"

    def _run_main(self, *, verbose: bool, want_json: bool = False):
        main = load_module()
        fake_args = types.SimpleNamespace(url=self.url, json=want_json, verbose=verbose)

        def manual_fail(_video_id: str):
            warnings.warn("manual warning")
            raise RuntimeError("No manual captions.")

        def dlp_success(_url: str, lang: str = "en", info=None):
            warnings.warn("dlp warning")
            return [{"start": 0, "text": "hello world"}]

        stdout = io.StringIO()
        stderr = io.StringIO()

        with warnings.catch_warnings():
            warnings.simplefilter("always")
            with mock.patch.object(main, "parse_args", return_value=fake_args), mock.patch.object(
                main, "get_meta_and_info", return_value=({"title": "", "channel": ""}, {})
            ), mock.patch.object(
                main, "scrape_manual", side_effect=manual_fail
            ), mock.patch.object(
                main, "dlp_captions", side_effect=dlp_success
            ), mock.patch.object(
                main, "api_captions", side_effect=AssertionError("API fallback should not run")
            ) as api_mock, contextlib.redirect_stdout(
                stdout
            ), contextlib.redirect_stderr(
                stderr
            ):
                main.main()
        return stdout.getvalue(), stderr.getvalue(), api_mock

    def test_warnings_suppressed_without_verbose(self):
        """Default runs should not emit warnings to stderr."""
        out, err, api_mock = self._run_main(verbose=False)
        self.assertIn("[00:00]", out)
        self.assertEqual(
            "",
            err.strip(),
            "Warnings should be suppressed when --verbose is not provided.",
        )
        self.assertEqual(0, api_mock.call_count)

    def test_warnings_visible_with_verbose(self):
        """Verbose runs surface warnings."""
        out, err, api_mock = self._run_main(verbose=True)
        self.assertIn("[00:00]", out)
        self.assertIn("manual warning", err)
        self.assertIn("dlp warning", err)
        self.assertEqual(0, api_mock.call_count)

    def test_json_output_not_polluted_by_warnings(self):
        """When requesting JSON, warnings should still go to stderr."""
        out, err, api_mock = self._run_main(verbose=True, want_json=True)
        self.assertTrue(out.strip().startswith("{"))
        self.assertIn("manual warning", err)
        self.assertEqual(0, api_mock.call_count)


if __name__ == "__main__":
    unittest.main()


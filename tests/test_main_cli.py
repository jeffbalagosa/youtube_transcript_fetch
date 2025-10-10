import contextlib
import importlib
import io
import sys
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

        def dlp_success(_url: str, lang: str = "en", info=None, verbose: bool = False):
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


class TestYtDlpLogger(unittest.TestCase):
    url = "https://youtu.be/dQw4w9WgXcQ"

    @staticmethod
    def _fake_ydl_factory(log_messages):
        class FakeYDL:
            def __init__(self, params):
                self.params = params
                log_messages.append(params)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def extract_info(self, url, download=False):
                logger = self.params.get("logger")
                if logger:
                    logger.warning("fake yt_dlp warning")
                else:
                    print("fake yt_dlp warning", file=sys.stderr)
                return {
                    "title": "Fake Title",
                    "channel": "Fake Channel",
                    "subtitles": {},
                    "automatic_captions": {},
                }

        return FakeYDL

    def test_get_meta_and_info_suppresses_yt_dlp_warning_without_verbose(self):
        main = load_module()
        captured_params = []
        FakeYDL = self._fake_ydl_factory(captured_params)

        with mock.patch.object(main, "YoutubeDL", FakeYDL):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                main.configure_runtime(verbose=False)
                meta, info = main.get_meta_and_info(self.url, verbose=False)

        self.assertEqual("", stderr.getvalue().strip())
        self.assertEqual("Fake Title", meta["title"])
        params = captured_params[-1]
        self.assertTrue(params.get("quiet"))
        self.assertTrue(params.get("no_warnings"))
        self.assertIsNotNone(params.get("logger"))

    def test_get_meta_and_info_emits_yt_dlp_warning_with_verbose(self):
        main = load_module()
        captured_params = []
        FakeYDL = self._fake_ydl_factory(captured_params)

        with mock.patch.object(main, "YoutubeDL", FakeYDL):
            with self.assertLogs("yt_dlp", level="WARNING") as log_ctx:
                main.configure_runtime(verbose=True)
                meta, info = main.get_meta_and_info(self.url, verbose=True)

        self.assertTrue(
            any("fake yt_dlp warning" in entry for entry in log_ctx.output),
            "Expected yt_dlp warning to be logged in verbose mode.",
        )
        self.assertEqual("Fake Title", meta["title"])
        params = captured_params[-1]
        self.assertFalse(params.get("quiet"))
        self.assertFalse(params.get("no_warnings"))
        self.assertIsNotNone(params.get("logger"))


if __name__ == "__main__":
    unittest.main()


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
            msg=(
                "Expected main.parse_args to be a function handling CLI "
                "arguments."
            ),
        )

        args = parse_args(
            ["https://youtu.be/dQw4w9WgXcQ", "--json", "--verbose"]
        )
        self.assertEqual(args.url, "https://youtu.be/dQw4w9WgXcQ")
        self.assertTrue(args.json)
        self.assertTrue(args.verbose)
        # --summarize is opt-in and should be False by default
        self.assertFalse(getattr(args, "summarize", False))

        # Ordering should not matter for flags.
        args = parse_args(["--verbose", "https://youtu.be/dQw4w9WgXcQ"])
        self.assertEqual(args.url, "https://youtu.be/dQw4w9WgXcQ")
        self.assertFalse(args.json)
        self.assertTrue(args.verbose)
        self.assertFalse(getattr(args, "summarize", False))

        # When explicitly supplied, --summarize should be True
        args = parse_args([
            "https://youtu.be/dQw4w9WgXcQ",
            "--json",
            "--verbose",
            "--summarize",
        ])
        self.assertTrue(args.summarize)

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

    def _run_main(self, *, verbose: bool, want_json: bool = False, summarize: bool = False):
        main = load_module()
        fake_args = types.SimpleNamespace(
            url=self.url, json=want_json, verbose=verbose, summarize=summarize
        )

        def manual_fail(_request):
            warnings.warn("manual warning")
            raise RuntimeError("No manual captions.")

        def dlp_success(_request):
            warnings.warn("dlp warning")
            return [{"start": 0, "text": "hello world"}]

        stdout = io.StringIO()
        stderr = io.StringIO()

        with warnings.catch_warnings():
            warnings.simplefilter("always")
            with mock.patch.object(
                main, "parse_args", return_value=fake_args
            ), mock.patch.object(
                main,
                "get_meta_and_info",
                return_value=({"title": "", "channel": ""}, {}),
            ), mock.patch.object(
                main, "scrape_manual", side_effect=manual_fail
            ), mock.patch.object(
                main, "dlp_captions", side_effect=dlp_success
            ), mock.patch.object(
                main,
                "api_captions",
                side_effect=AssertionError("API fallback should not run"),
            ) as api_mock:
                with contextlib.redirect_stdout(stdout), \
                        contextlib.redirect_stderr(stderr):
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

    def test_summarize_prepends_prompt_text(self):
        """When --summarize is supplied, the prompt should appear before text output."""
        main = load_module()
        out, err, api_mock = self._run_main(verbose=False, want_json=False, summarize=True)
        # Prompt should precede transcript and be followed by a blank line
        self.assertTrue(out.startswith(main.SUMMARIZE_PROMPT + "\n\n"))
        self.assertIn("[00:00]", out)
        self.assertEqual(0, api_mock.call_count)

    def test_summarize_prepends_prompt_json(self):
        """When --json and --summarize are supplied, the prompt should precede JSON payload."""
        main = load_module()
        out, err, api_mock = self._run_main(verbose=False, want_json=True, summarize=True)
        self.assertTrue(out.startswith(main.SUMMARIZE_PROMPT + "\n\n"))
        # JSON follows the prompt
        after_prompt = out[len(main.SUMMARIZE_PROMPT) + 2 :].strip()
        self.assertTrue(after_prompt.startswith("{"))
        self.assertEqual(0, api_mock.call_count)


class TestFetchRequest(unittest.TestCase):
    def test_fetch_request_construction_and_lang_default(self):
        """FetchRequest carries all source inputs; lang defaults to 'en'."""
        main = load_module()
        req = main.FetchRequest(
            url="https://youtu.be/dQw4w9WgXcQ",
            video_id="dQw4w9WgXcQ",
            info={"title": "Test"},
            verbose=False,
        )
        self.assertEqual(req.url, "https://youtu.be/dQw4w9WgXcQ")
        self.assertEqual(req.video_id, "dQw4w9WgXcQ")
        self.assertEqual(req.info, {"title": "Test"})
        self.assertFalse(req.verbose)
        self.assertEqual(req.lang, "en")

    def test_fetch_request_lang_override(self):
        """FetchRequest accepts an explicit lang value."""
        main = load_module()
        req = main.FetchRequest(
            url="https://youtu.be/dQw4w9WgXcQ",
            video_id="dQw4w9WgXcQ",
            info={},
            verbose=True,
            lang="fr",
        )
        self.assertEqual(req.lang, "fr")

    def test_scrape_manual_accepts_fetch_request(self):
        """scrape_manual reads video_id and lang from FetchRequest."""
        main = load_module()
        req = main.FetchRequest(
            url="https://youtu.be/dQw4w9WgXcQ",
            video_id="dQw4w9WgXcQ",
            info={},
            verbose=False,
            lang="fr",
        )
        captured = {}

        def fake_get(url, timeout=10):
            captured["url"] = url
            raise RuntimeError("network stub")

        with mock.patch.object(main.requests, "get", side_effect=fake_get):
            with self.assertRaises(RuntimeError):
                main.scrape_manual(req)

        self.assertEqual(
            captured["url"],
            "https://video.google.com/timedtext?lang=fr&v=dQw4w9WgXcQ",
        )

    def test_dlp_captions_accepts_fetch_request(self):
        """dlp_captions reads info and lang from FetchRequest; uses matching track."""
        main = load_module()
        info = {
            "subtitles": {
                "en": [{"ext": "vtt", "url": "http://fake/en.vtt"}]
            },
            "automatic_captions": {},
        }
        req = main.FetchRequest(
            url="https://youtu.be/dQw4w9WgXcQ",
            video_id="dQw4w9WgXcQ",
            info=info,
            verbose=False,
        )
        fake_segments = [{"start": 0, "text": "hello"}]

        with mock.patch.object(
            main, "_parse_caption_url", return_value=fake_segments
        ) as mock_parse:
            result = main.dlp_captions(req)

        self.assertEqual(result, fake_segments)
        mock_parse.assert_called_once_with("http://fake/en.vtt", "vtt")

    def test_api_captions_accepts_fetch_request(self):
        """api_captions reads video_id from FetchRequest."""
        main = load_module()
        req = main.FetchRequest(
            url="https://youtu.be/dQw4w9WgXcQ",
            video_id="dQw4w9WgXcQ",
            info={},
            verbose=False,
        )
        fake_segments = [{"start": 0, "text": "hi"}]

        with mock.patch.object(
            main.YouTubeTranscriptApi,
            "get_transcript",
            return_value=fake_segments,
        ) as mock_api:
            result = main.api_captions(req)

        self.assertEqual(result, fake_segments)
        args, kwargs = mock_api.call_args
        self.assertEqual(args[0], "dQw4w9WgXcQ")


class TestFallbackSequencing(unittest.TestCase):
    url = "https://youtu.be/dQw4w9WgXcQ"

    def test_manual_fails_dlp_succeeds_api_never_called(self):
        """scrape_manual raises → dlp_captions gets same FetchRequest → api skipped."""
        main = load_module()
        received_requests = []

        def manual_fail(req):
            received_requests.append(("manual", req))
            raise RuntimeError("No manual captions.")

        fake_segments = [{"start": 0, "text": "hello"}]

        def dlp_success(req):
            received_requests.append(("dlp", req))
            return fake_segments

        fake_args = types.SimpleNamespace(
            url=self.url, json=False, verbose=False, summarize=False
        )
        stdout = io.StringIO()

        with mock.patch.object(main, "parse_args", return_value=fake_args), \
             mock.patch.object(
                 main, "get_meta_and_info",
                 return_value=({"title": "", "channel": ""}, {}),
             ), \
             mock.patch.object(main, "scrape_manual", side_effect=manual_fail), \
             mock.patch.object(main, "dlp_captions", side_effect=dlp_success), \
             mock.patch.object(
                 main, "api_captions",
                 side_effect=AssertionError("api_captions must not be called"),
             ), \
             contextlib.redirect_stdout(stdout):
            main.main()

        self.assertEqual(len(received_requests), 2)
        self.assertEqual(received_requests[0][0], "manual")
        self.assertEqual(received_requests[1][0], "dlp")

        req_manual = received_requests[0][1]
        req_dlp = received_requests[1][1]
        self.assertIsInstance(req_manual, main.FetchRequest)
        self.assertIsInstance(req_dlp, main.FetchRequest)
        self.assertEqual(req_manual.video_id, "dQw4w9WgXcQ")
        self.assertEqual(req_dlp.video_id, "dQw4w9WgXcQ")
        self.assertEqual(req_manual.url, self.url)
        self.assertEqual(req_dlp.url, self.url)


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
        self.assertTrue(params.get("ignore_no_formats_error"))

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
        self.assertTrue(params.get("ignore_no_formats_error"))

    def test_yt_dlp_options_ignore_unavailable_media_formats(self):
        main = load_module()

        opts = main.yt_dlp_options(verbose=False)

        self.assertTrue(opts["skip_download"])
        self.assertTrue(
            opts.get("ignore_no_formats_error"),
            "Caption extraction should not fail because yt-dlp cannot select "
            "a playable video/audio format.",
        )


if __name__ == "__main__":
    unittest.main()

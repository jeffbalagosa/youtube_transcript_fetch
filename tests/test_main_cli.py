import importlib
import types
import unittest


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


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from scripts import oss_thanks


class OssThanksTest(unittest.TestCase):
    def test_extract_repos_from_common_github_forms(self):
        text = """
        git clone https://github.com/pallets/flask.git.
        gh repo clone psf/requests.
        installed skill from git@github.com:openai/skills.git
        https://github.com/features/actions
        """
        self.assertEqual(
            oss_thanks.extract_repos(text),
            ["openai/skills", "pallets/flask", "psf/requests"],
        )

    def test_plain_search_result_link_is_not_actual_use(self):
        text = """
        Search results:
        https://github.com/pallets/flask
        Also mentioned https://github.com/psf/requests in a web page.
        """
        self.assertEqual(oss_thanks.extract_repos(text), [])

    def test_explicit_opened_and_referenced_repo_counts_as_use(self):
        text = "Opened https://github.com/openai/skills and referenced its README."
        self.assertEqual(oss_thanks.extract_repos(text), ["openai/skills"])

    def test_record_review_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            oss_thanks.record_repositories(
                home,
                ["pallets/flask"],
                source="test",
                reason="unit test",
                mode="review",
            )
            state = oss_thanks.load_state(home)
            pending = oss_thanks.pending_repos(state)
            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0]["repo"], "pallets/flask")

    def test_hook_payload_scans_nested_strings(self):
        payload = '{"tool_input":{"command":"git clone https://github.com/pytest-dev/pytest.git"}}'
        text = oss_thanks.extract_text_from_hook_payload(payload)
        self.assertEqual(oss_thanks.extract_repos(text), ["pytest-dev/pytest"])

    def test_setup_saves_auto_star_preference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            exit_code = oss_thanks.main(
                ["setup", "--home", str(home), "--mode", "auto-star", "--dry-run"]
            )
            self.assertEqual(exit_code, 0)
            config = oss_thanks.load_config(home)
            self.assertEqual(config["mode"], "auto-star")
            self.assertTrue(config["auto_star_consent"])
            self.assertTrue(config["configured"])


if __name__ == "__main__":
    unittest.main()

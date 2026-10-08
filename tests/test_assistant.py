import tempfile
import unittest
from pathlib import Path

from assistant_core import CommandProcessor, music_search_url, website_url
from assistant_store import AssistantStore


class CommandProcessorTests(unittest.TestCase):
    def setUp(self):
        self.processor = CommandProcessor()

    def test_known_site_opens_directly(self):
        result = self.processor.process("open Spotify")
        self.assertEqual(result.url, "https://open.spotify.com")
        self.assertIn("Opening Spotify", result.response)

    def test_custom_domain_opens_directly(self):
        result = self.processor.process("go to example.com/docs")
        self.assertEqual(result.url, "https://example.com/docs")

    def test_unknown_site_name_is_searched(self):
        self.assertEqual(
            website_url("a site with spaces"),
            "https://www.google.com/search?q=a+site+with+spaces",
        )

    def test_unsafe_scheme_is_not_opened(self):
        self.assertTrue(website_url("javascript:alert(1)").startswith(
            "https://www.google.com/search?"
        ))

    def test_music_search_can_choose_provider_and_encodes_query(self):
        result = self.processor.process("play hello & goodbye on Spotify")
        self.assertEqual(
            result.url, "https://open.spotify.com/search/hello+%26+goodbye"
        )

    def test_music_homepage(self):
        self.assertEqual(
            music_search_url("play music"), "https://music.youtube.com"
        )

    def test_search_encodes_query(self):
        result = self.processor.process("search cats & dogs")
        self.assertEqual(
            result.url, "https://www.google.com/search?q=cats+%26+dogs"
        )

    def test_exit_is_a_clear_action(self):
        result = self.processor.process("goodbye")
        self.assertTrue(result.should_exit)


class AssistantStoreTests(unittest.TestCase):
    def test_history_is_saved_newest_first(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AssistantStore(Path(directory) / "test.sqlite3")
            try:
                store.add("open Spotify", "Opening Spotify.", "https://open.spotify.com")
                store.add("time", "It is 10 AM.", None)
                entries = store.recent()
            finally:
                store.close()

        self.assertEqual([entry.command for entry in entries], ["time", "open Spotify"])
        self.assertEqual(entries[1].url, "https://open.spotify.com")


if __name__ == "__main__":
    unittest.main()

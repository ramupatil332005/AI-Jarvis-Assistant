"""Command parsing and routing for the Jarvis desktop assistant."""

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote_plus, urlencode, urlparse


WEBSITE_URLS = {
    "amazon": "https://www.amazon.com",
    "apple music": "https://music.apple.com",
    "facebook": "https://www.facebook.com",
    "github": "https://github.com",
    "google": "https://www.google.com",
    "instagram": "https://www.instagram.com",
    "netflix": "https://www.netflix.com",
    "reddit": "https://www.reddit.com",
    "soundcloud": "https://soundcloud.com",
    "spotify": "https://open.spotify.com",
    "wikipedia": "https://www.wikipedia.org",
    "x": "https://x.com",
    "youtube": "https://www.youtube.com",
    "youtube music": "https://music.youtube.com",
}

MUSIC_SEARCH_URLS = {
    "apple music": "https://music.apple.com/us/search?term={}",
    "soundcloud": "https://soundcloud.com/search?q={}",
    "spotify": "https://open.spotify.com/search/{}",
    "youtube music": "https://music.youtube.com/search?q={}",
}


@dataclass(frozen=True)
class CommandResult:
    """The user-facing result and optional browser action for a command."""

    response: str
    url: str | None = None
    should_exit: bool = False


def website_url(site: str) -> str:
    """Resolve a known site, a safe HTTP(S) URL, or a Google search."""
    site = site.strip().rstrip(" .!?")
    normalized_site = site.casefold()
    if normalized_site.startswith("the "):
        site = site[4:]
        normalized_site = site.casefold()

    if normalized_site in WEBSITE_URLS:
        return WEBSITE_URLS[normalized_site]

    candidate = site if "://" in site else "https://" + site
    parsed_url = urlparse(candidate)
    if (
        parsed_url.scheme in ("http", "https")
        and parsed_url.hostname
        and "." in parsed_url.hostname
        and not any(character.isspace() for character in site)
    ):
        return candidate

    return "https://www.google.com/search?" + urlencode({"q": site})


def music_search_url(command: str) -> str:
    """Build a music search URL, optionally targeting a named service."""
    query = command.strip()[len("play"):].strip()
    if query.casefold() in ("music", "some music"):
        return WEBSITE_URLS["youtube music"]

    service = "youtube music"
    for music_service in MUSIC_SEARCH_URLS:
        suffix = " on " + music_service
        if query.casefold().endswith(suffix):
            query = query[:-len(suffix)].strip()
            service = music_service
            break

    return MUSIC_SEARCH_URLS[service].format(quote_plus(query))


class CommandProcessor:
    """Translate typed or recognized speech into assistant responses."""

    def process(self, command: str) -> CommandResult:
        raw_command = command.strip()
        command = raw_command.casefold()
        if not command:
            return CommandResult("Type or say a command to get started.")

        if command in ("exit", "quit", "close assistant", "goodbye", "bye"):
            return CommandResult("Goodbye! Jarvis is closing.", should_exit=True)

        if command in ("help", "commands", "what can you do"):
            return CommandResult(
                "Try: open Spotify, open example.com, search for a topic, "
                "play a song on Spotify, time, or date."
            )

        if command in ("time", "what time is it", "tell me the time"):
            return CommandResult(
                "The current time is " + datetime.now().strftime("%I:%M %p") + "."
            )

        if command in ("date", "what is the date", "what's the date"):
            return CommandResult(
                "Today is " + datetime.now().strftime("%A, %B %d, %Y") + "."
            )

        for prefix in ("open ", "go to ", "visit "):
            if command.startswith(prefix):
                site = raw_command[len(prefix):].strip()
                if not site:
                    return CommandResult("Tell me which website you want to open.")
                return CommandResult(f"Opening {site}.", url=website_url(site))

        if command.startswith("play "):
            query = raw_command[len("play"):].strip()
            if not query:
                return CommandResult("Tell me what music you want to search for.")
            return CommandResult(
                f"Searching for {query}.", url=music_search_url(raw_command)
            )

        if command in WEBSITE_URLS:
            return CommandResult(
                f"Opening {command.title()}.", url=WEBSITE_URLS[command]
            )

        search_query = raw_command
        for prefix in ("search for ", "search "):
            if command.startswith(prefix):
                search_query = raw_command[len(prefix):].strip()
                break
        else:
            search_query = ""

        if search_query:
            return CommandResult(
                f"Searching Google for {search_query}.",
                url="https://www.google.com/search?"
                + urlencode({"q": search_query}),
            )
        if command.startswith(("search ", "search for ")):
            return CommandResult("Tell me what you want to search for.")

        return CommandResult(
            "I don't know that command yet. Try Help to see what I can do."
        )

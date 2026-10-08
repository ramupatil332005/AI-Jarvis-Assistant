# Jarvis Desktop Assistant

Jarvis is a Python desktop assistant with a graphical interface, typed and
voice commands, music and website search, and a local conversation history.

For a project walkthrough and viva preparation, see the
[Jarvis Viva and Project Study Guide](docs/JARVIS_VIVA_GUIDE.md).

## Features

- Open popular sites or any HTTP(S) domain from a quick shortcut or command.
- Search Google and music catalogs (YouTube Music by default; Spotify,
  SoundCloud, and Apple Music can be selected with `on <service>`).
- Use voice input with a microphone, or type commands if a microphone is not
  available.
- Ask for the current time or date, view recent activity, and get in-app help.
- Keep conversation history in a local SQLite database at
  `~/.jarvis_assistant/history.sqlite3`.
- Keep the Tkinter interface responsive while speech recognition and
  text-to-speech run in background work.

## Setup

Requires Python 3.10 or newer.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

On Windows, if PyAudio cannot be installed through pip, install a compatible
PyAudio wheel for your Python version and architecture before using voice input.
Typed commands do not require a microphone. Voice recognition uses
SpeechRecognition's Google service and therefore needs an internet connection.

## Example commands

- `open Spotify`
- `open example.com`
- `search Python desktop apps`
- `play Dreams on Spotify`
- `play jazz`
- `time`
- `date`
- `help`
- `goodbye`

Music commands open search results in the selected service; they do not start
playback automatically. An unrecognized site name is searched on Google rather
than treated as a URL.

## Run tests

```powershell
python -m unittest discover -s tests -v
```

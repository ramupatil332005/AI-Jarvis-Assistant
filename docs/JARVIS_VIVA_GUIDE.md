# Jarvis Desktop Assistant — Viva and Project Study Guide

This guide explains the project as it is currently implemented. It is intended
for project revision, a classroom presentation, and viva preparation.

## Project at a glance

**Project title:** Jarvis Desktop Assistant
**Type:** Python desktop application
**Interface:** Tkinter
**Voice input:** SpeechRecognition with Google's online speech-recognition
service
**Voice output:** pyttsx3
**Local storage:** SQLite
**Purpose:** Accept typed or spoken commands to open websites, search Google or
music services, tell the date or time, and retain a short local activity
history.

> **Be accurate in the viva:** This version is a rule-based assistant, not a
> generative AI chatbot. Music requests open search results; the program does
> not control the music player or start playback itself.

## Short presentation script

> Good morning. My project is Jarvis Desktop Assistant, a Python desktop
> application built with Tkinter. It accepts commands either as typed text or
> speech. I can ask it to open a supported website, search Google, search for
> music on services such as Spotify, or tell me the current date and time. The
> command-processing logic is separated from the graphical interface, and
> recent commands and responses are stored locally in SQLite. Speech and
> command work run outside the main GUI event loop so that slower tasks are
> less likely to freeze the interface. The project also includes unit tests for
> command handling, URL construction, and history storage.

## How a command travels through the application

1. `main.py` calls `app.launch()`, which creates the Tkinter root window and
   starts the GUI event loop.
2. You type a command and press **Send**, click a quick-open button, or click
   **Listen** and speak.
3. For voice input, `app.py` records a short microphone clip and asks
   `recognize_google` to convert it to text. Typed commands do not require a
   microphone or speech recognition.
4. The GUI sends the text to a worker through a thread-safe command queue.
5. `CommandProcessor.process()` in `assistant_core.py` normalizes the text and
   matches it against known command patterns. It returns a `CommandResult`
   containing the spoken/display response, an optional URL, and an optional
   exit flag.
6. If there is a URL, the worker asks Python's `webbrowser` module to open it
   in the system's default browser.
7. The response is sent to `pyttsx3` for speech output. The worker saves the
   command, response, URL, and timestamp using `AssistantStore` in
   `assistant_store.py`.
8. Worker results and errors are put on an event queue. Tkinter's `after()`
   callback checks that queue and updates the conversation, status, and recent
   activity display on the GUI thread.

## File and component map

| File | Responsibility |
|---|---|
| `main.py` | Program entry point; starts the desktop app. |
| `app.py` | Tkinter window, typed commands, microphone capture, worker thread, browser launch, text-to-speech, and screen updates. |
| `assistant_core.py` | Website and music URL helpers, `CommandResult`, and rule-based `CommandProcessor`. |
| `assistant_store.py` | SQLite connection, history table creation, and history reads/writes. |
| `tests/test_assistant.py` | Unit tests for core command behavior and SQLite history. |
| `requirements.txt` | Third-party Python packages used by the application. |
| `README.md` | Setup, usage, and testing instructions. |

## Viva questions and answers

### A. Project and requirements

**1. What is the title of your project?**
Jarvis Desktop Assistant.

**2. What does the project do?**
It accepts typed or spoken commands to open websites, perform web or music
searches, tell the date or time, and save recent activity locally.

**3. What problem does it address?**
It brings a few frequently used desktop actions into one interface and lets a
user request them by typing or speaking.

**4. Who could use this application?**
Someone who wants a simple desktop interface for launching websites and
searches, with optional voice commands.

**5. Why did you choose this project?**
It combines desktop UI programming, command processing, speech recognition,
text-to-speech, URL handling, concurrency, persistence, and testing in one
small application.

**6. What are the main features?**
Quick-open buttons, typed commands, one-shot voice input, web and music
searches, date/time responses, spoken output, local SQLite history, and
in-app help.

**7. Is this really an artificial-intelligence chatbot?**
Not in its current implementation. It is a rule-based voice and desktop
assistant. It recognizes predefined command forms; it does not use a language
model to reason or generate open-ended answers.

**8. What is outside the project's current scope?**
It does not continuously listen for a wake word, control music playback,
perform general conversation, or synchronize history to a cloud service.

### B. Languages, libraries, and design

**9. Which programming language did you use?**
Python.

**10. Which library creates the desktop interface?**
Tkinter, including themed widgets from `tkinter.ttk`.

**11. Which library handles speech recognition?**
The `SpeechRecognition` package captures audio and calls its Google
recognition integration to get recognized text.

**12. Does voice recognition work offline?**
No. The current `recognize_google` call uses an online service, so voice
recognition needs an internet connection. Typed commands can still be used
without it.

**13. Which library speaks the response?**
`pyttsx3`, a text-to-speech package that uses the speech engines available on
the computer.

**14. How does the application open a web page?**
It calls Python's standard-library `webbrowser.open()` with the URL produced
by command processing.

**15. Which database did you use, and why?**
SQLite. It is a lightweight, file-based database available through Python's
standard library, so this project does not need a separate database server.

**16. Which design pattern or architecture does it use?**
It separates the GUI (`app.py`), command rules (`assistant_core.py`), and
history persistence (`assistant_store.py`). This modular structure keeps
command logic testable without launching the full GUI.

**17. Is this a client-server application?**
The main desktop app and SQLite history are local. The voice-recognition
request uses an external online recognition service; opening websites also
requires the user's browser and, for online pages, an internet connection.

### C. Program flow and command processing

**18. What is the program's entry point?**
`main.py`. When run as the main script, it calls `launch()` from `app.py`.

**19. What happens after the user enters a command?**
The GUI displays it, queues it for the worker, and the worker passes it to
`CommandProcessor.process()`. The result may open a URL, speak a response,
save history, and then be returned to the GUI for display.

**20. What does `CommandProcessor` do?**
It normalizes the command, recognizes supported command patterns, and returns
a `CommandResult`. It does not itself draw the UI or access the database.

**21. What is a `CommandResult`?**
A frozen data class with a user-facing `response`, an optional `url`, and a
`should_exit` boolean. It communicates the core command outcome to the GUI.

**22. Why normalize commands with `casefold()`?**
It makes command matching case-insensitive, including more Unicode-aware
case handling than a simple lowercase conversion.

**23. Which command prefixes open a website?**
`open`, `go to`, and `visit`. Known names map to predefined URLs. A
domain-like value with HTTP or HTTPS is opened directly; an unrecognized
phrase is searched on Google.

**24. Which websites have built-in shortcuts?**
The mapping includes Amazon, Apple Music, Facebook, GitHub, Google, Instagram,
Netflix, Reddit, SoundCloud, Spotify, Wikipedia, X, YouTube, and YouTube
Music.

**25. What happens when the user says `open example.com`?**
The website helper adds `https://` if needed, checks that the parsed scheme is
HTTP or HTTPS and that a hostname is present, and returns the URL for the
browser.

**26. What happens if the user says `open a site with spaces`?**
That phrase is not treated as a direct domain. The helper makes a Google
search URL for it.

**27. Which music services can be selected?**
The implemented search URL mapping includes YouTube Music, Spotify,
SoundCloud, and Apple Music. YouTube Music is the default when no provider is
specified.

**28. Does `play jazz` play music?**
No. It opens YouTube Music search results for “jazz.” A command such as
`play Dreams on Spotify` searches Spotify. Playback is not controlled by this
application.

**29. How are Google search queries constructed?**
The code uses `urllib.parse.urlencode()` to encode the query as a URL
parameter.

**30. Why encode URL query text?**
Characters such as spaces and `&` have special meanings in URLs. Encoding
keeps the user's phrase together as a search term instead of letting those
characters alter the URL structure.

**31. What date and time commands are supported?**
The exact commands include `time`, `what time is it`, `tell me the time`,
`date`, `what is the date`, and `what's the date`.

**32. What commands exit the application?**
`exit`, `quit`, `close assistant`, `goodbye`, and `bye` return an exit flag.
The GUI waits for the response event and then closes the window.

**33. What happens for an unknown command?**
The assistant replies that it does not know the command yet and suggests
using Help.

**34. Is arbitrary conversational input sent to a chatbot?**
No. The current core only handles its implemented command patterns. It does
not submit general text to a chatbot or language model.

### D. Voice, GUI, and concurrency

**35. How does the user provide voice input?**
The user clicks **Listen**. The app opens the microphone, adjusts for ambient
noise, records a short phrase, and sends that recording for recognition.

**36. Is the microphone always active?**
No. Voice input is one-shot and starts when the user clicks **Listen**.

**37. What is a thread?**
A thread is an execution path within a process. This application uses
background threads for potentially slow voice capture and command work.

**38. Why are background threads used?**
Microphone recording, network recognition, speech output, and browser actions
can take time. Doing this work outside the Tkinter event loop helps the window
remain responsive.

**39. Why use queues between threads?**
The `queue.Queue` objects provide a thread-safe way to hand commands to the
worker and send results or errors back to the GUI.

**40. Why does the GUI use `root.after()`?**
The GUI periodically checks for worker events using Tkinter's event loop.
This lets widget updates happen on the GUI thread rather than having a
background worker directly update Tkinter widgets.

**41. What is the purpose of the status label?**
It tells the user whether Jarvis is ready, listening, or processing a
command.

**42. What does the conversation panel show?**
It displays the user's command and Jarvis's response. Recent activity is also
shown separately in a table.

**43. How does text-to-speech work in this project?**
The worker passes the assistant's response string to `pyttsx3`, which queues
and plays the spoken response through the system speech engine.

### E. Database and history

**44. Where is the history database stored?**
By default, `AssistantStore` creates
`~/.jarvis_assistant/history.sqlite3` under the user's home directory.

**45. What information is stored?**
Each history row contains an ID, the original command, the assistant response,
an optional URL, and a timestamp.

**46. How is history displayed?**
At startup and after commands, the GUI loads up to the eight newest history
entries and displays their time and command.

**47. Is history sent to GitHub or a cloud database?**
No. The app stores history in its local SQLite file. The project repository
does not contain the user's local database; `.gitignore` excludes SQLite
database files.

**48. Why is a lock used around SQLite operations?**
The connection is configured with `check_same_thread=False` because the
worker accesses it from a background thread. A `threading.Lock` serializes
database operations to avoid simultaneous access through that connection.

**49. What is a parameterized SQL query?**
It passes values separately from SQL text using placeholders such as `?`.
`AssistantStore` uses parameterized statements for inserts and the history
limit query rather than concatenating those values into the SQL statement.

**50. How does the application handle database errors?**
The worker catches SQLite errors around saving and reading recent entries and
sends a notice event so the GUI can inform the user.

### F. Errors, safety, and limitations

**51. What happens if no speech is detected?**
SpeechRecognition raises a wait-timeout error, which the app converts into a
notice asking the user to try listening again.

**52. What if speech is unclear?**
The app catches the unknown-value error and asks the user to try again.

**53. What if the recognition service cannot be reached?**
The app catches the request error and displays a message to check the
internet connection.

**54. What if the microphone is unavailable?**
The app catches microphone-related `OSError` and `AttributeError` exceptions
and shows an error notice. Typed commands remain an alternative.

**55. What is URL validation in this project intended to prevent?**
The helper only returns a direct candidate URL when its parsed scheme is
HTTP or HTTPS and basic hostname and whitespace checks pass. A value with
another scheme, such as `javascript:`, is turned into a Google search instead
of being opened as that scheme.

**56. Is the URL validation production-grade?**
No. It is a basic guard for this small project, not a comprehensive security
validator. A production app should use a well-tested URL validation policy,
consider internationalized domains and edge cases, and clearly confirm
external navigation when appropriate.

**57. What is the biggest privacy consideration?**
Voice audio is sent to Google's online recognition service. The app's command
history is stored locally, but users should still be informed about the
external voice service and avoid speaking sensitive information.

**58. What happens if the browser cannot open a page?**
The code handles an `OSError` or a false result from `webbrowser.open()` and
creates an explanatory response.

**59. What are the main limitations of the current version?**
Voice recognition requires the internet and a working microphone; commands
are predefined; there is no wake word; music search does not start playback;
and the website URL checks are intentionally simple.

**60. What would you improve next?**
I would add stronger and configurable URL validation, user-selectable
speech-recognition providers, configurable quick links, more command tests,
and optional media-control integrations. I would add any online AI feature
only with clear privacy and API-key handling.

### G. Testing, setup, and delivery

**61. What testing framework does the project use?**
Python's built-in `unittest` framework.

**62. What do the current tests cover?**
They cover known-site and custom-domain routing, unknown site searches,
rejection of a non-HTTP scheme as a direct URL, music and Google query
encoding, the music homepage route, the exit flag, and newest-first local
history.

**63. How do you run the tests?**
From the project folder, run:

```powershell
python -m unittest discover -s tests -v
```

**64. How do you run the program?**
Install the requirements, then run `python main.py` from the project
directory. Setup details are in `README.md`.

**65. Why might PyAudio installation be difficult on Windows?**
PyAudio includes platform-specific native audio components. A compatible
wheel may be needed for the installed Python version and architecture.

**66. Does the app require an API key?**
The current project does not define or ask the user for a project API key.
Its Google speech-recognition call uses the library's Google integration.

**67. Where can someone find the source code?**
The repository is
[github.com/ramupatil332005/AI-Jarvis-Assistant](https://github.com/ramupatil332005/AI-Jarvis-Assistant).

### H. Personal contribution and reflection

**68. What is the most important design decision?**
Separating command processing from the GUI and storage. This makes command
logic easier to test and the modules easier to maintain.

**69. What was technically challenging?**
Coordinating Tkinter with slower speech and browser work. The project uses
queues and background threads so the GUI event loop is not responsible for
waiting on every operation.

**70. What did you learn from this project?**
I learned how to connect a desktop interface to voice libraries, how to
separate concerns into modules, how to construct encoded URLs, how to persist
data in SQLite, and how to write focused unit tests.

**71. How would you explain the project's test strategy?**
I test the command processor and storage separately, using deterministic
inputs and a temporary database for the storage test. That avoids needing a
live microphone or launching a real desktop window for these unit tests.

**72. What did you personally contribute?**
Answer honestly based on your own work. A suitable template, if accurate, is:
“I designed and implemented the Tkinter interface, command routing, voice
input/output integration, SQLite history, and unit tests.”

## Suggested live demonstration

1. Start the app and point out the conversation area, quick-open buttons,
   **Listen** button, status, and recent activity.
2. Type `help` and show the command guidance.
3. Type `open Spotify` and show the browser opening the Spotify home page.
4. Type `search cats & dogs` and point out that the punctuation is encoded in
   the Google query.
5. Type `play Dreams on Spotify` and explain that this opens search results,
   not automatic playback.
6. Type `time` or `date`.
7. If a microphone and internet connection are available, click **Listen** and
   speak a simple command. Otherwise, explain that the typed interface is the
   offline alternative for command entry.
8. Point to the recent activity row and explain that it comes from local
   SQLite history.
9. If asked about implementation, open `assistant_core.py` for command rules,
   `assistant_store.py` for persistence, or `tests/test_assistant.py` for
   examples that are automatically checked.

## Quick revision sheet

- **Entry point:** `main.py`
- **GUI:** Tkinter in `app.py`
- **Speech-to-text:** SpeechRecognition `recognize_google()`; internet
  required
- **Text-to-speech:** `pyttsx3`
- **Command logic:** `CommandProcessor` in `assistant_core.py`
- **Result structure:** `CommandResult(response, url, should_exit)`
- **Browser:** Python `webbrowser`
- **Database:** SQLite through Python's `sqlite3`
- **History location:** `~/.jarvis_assistant/history.sqlite3`
- **Concurrency:** worker thread and thread-safe queues; UI events processed
  using Tkinter `after()`
- **Tests:** `unittest`
- **Important limitation:** music opens search results; it does not play
  tracks automatically
- **Important privacy fact:** microphone audio is sent to an online Google
  recognition service

## Short resume description

> Built a Python desktop assistant with a Tkinter interface, typed and
> speech-based commands, website and music search, background task handling,
> local SQLite activity history, and unit tests.

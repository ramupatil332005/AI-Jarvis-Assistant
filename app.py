"""Tkinter desktop interface for Jarvis."""

import queue
import sqlite3
import threading
import tkinter as tk
import webbrowser
from tkinter import ttk

import pyttsx3
import speech_recognition as sr

from assistant_core import CommandProcessor, CommandResult
from assistant_store import AssistantStore, HistoryEntry


class AssistantApp:
    """Desktop UI with typed commands, one-shot voice input, and history."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Jarvis | Desktop Assistant")
        self.root.geometry("1120x720")
        self.root.minsize(850, 600)
        self.processor = CommandProcessor()
        self.store = AssistantStore()
        self._commands: queue.Queue[tuple[str, str] | None] = queue.Queue()
        self._events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._listening = False
        self._tts_engine: pyttsx3.Engine | None = None
        self._worker = threading.Thread(target=self._work, daemon=True)
        self._worker.start()

        self._build_ui()
        self._load_history()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(100, self._drain_events)
        self._append_message(
            "Jarvis",
            "Welcome! I can open websites, search the web, find music, and tell "
            "you the time or date. Type a command or use Listen.",
            "assistant",
        )

    def _build_ui(self) -> None:
        self.root.configure(background="#101722")
        style = ttk.Style(self.root)
        style.configure("TFrame", background="#101722")
        style.configure("Panel.TFrame", background="#182333")
        style.configure("TLabel", background="#101722", foreground="#e7edf5")
        style.configure(
            "Subtle.TLabel", background="#101722", foreground="#9aabc1"
        )
        style.configure(
            "Panel.TLabel", background="#182333", foreground="#e7edf5"
        )
        style.configure(
            "Title.TLabel", background="#101722", foreground="#f2f6fc",
            font=("Segoe UI", 20, "bold"),
        )
        style.configure(
            "Accent.TButton", padding=(12, 9), background="#2a78dc",
            foreground="#ffffff",
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#3989ed"), ("disabled", "#46576b")],
        )
        style.configure("TButton", padding=(10, 7))
        style.configure(
            "Treeview", background="#182333", fieldbackground="#182333",
            foreground="#e7edf5", rowheight=28, borderwidth=0,
        )
        style.configure(
            "Treeview.Heading", background="#223146", foreground="#e7edf5",
            font=("Segoe UI", 9, "bold"),
        )

        header = ttk.Frame(self.root, padding=(24, 18, 24, 12))
        header.pack(fill="x")
        ttk.Label(header, text="JARVIS", style="Title.TLabel").pack(side="left")
        ttk.Label(
            header, text="Your desktop voice and web assistant",
            style="Subtle.TLabel",
        ).pack(side="left", padx=(14, 0), pady=(8, 0))
        self.status = tk.StringVar(value="Ready")
        ttk.Label(header, textvariable=self.status, style="Subtle.TLabel").pack(
            side="right", pady=(8, 0)
        )

        body = ttk.Frame(self.root, padding=(18, 0, 18, 18))
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(body, style="Panel.TFrame", padding=16)
        sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        ttk.Label(
            sidebar, text="QUICK OPEN", style="Panel.TLabel",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 10))
        for site in ("Google", "YouTube", "Spotify", "GitHub", "Wikipedia"):
            ttk.Button(
                sidebar, text=site, command=lambda name=site: self._submit(
                    f"open {name}"
                ),
            ).pack(fill="x", pady=3)
        ttk.Separator(sidebar).pack(fill="x", pady=14)
        ttk.Button(sidebar, text="Help", command=lambda: self._submit("help")).pack(
            fill="x", pady=3
        )
        ttk.Label(
            sidebar,
            text="Voice recognition uses Google's online speech service. "
            "Typed commands work without a microphone.",
            style="Panel.TLabel", wraplength=175, justify="left",
        ).pack(anchor="w", side="bottom", pady=(16, 0))

        center = ttk.Frame(body)
        center.grid(row=0, column=1, sticky="nsew")
        center.rowconfigure(1, weight=1)
        center.columnconfigure(0, weight=1)
        ttk.Label(
            center, text="Assistant", font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, sticky="w", pady=(2, 10))
        conversation_panel = ttk.Frame(center, style="Panel.TFrame", padding=12)
        conversation_panel.grid(row=1, column=0, sticky="nsew")
        conversation_panel.rowconfigure(0, weight=1)
        conversation_panel.columnconfigure(0, weight=1)
        self.conversation = tk.Text(
            conversation_panel, wrap="word", state="disabled",
            background="#182333", foreground="#e7edf5",
            insertbackground="#e7edf5", relief="flat", padx=10, pady=8,
            font=("Segoe UI", 10), spacing1=3, spacing3=10,
        )
        self.conversation.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(
            conversation_panel, orient="vertical",
            command=self.conversation.yview,
        )
        scroll.grid(row=0, column=1, sticky="ns")
        self.conversation.configure(yscrollcommand=scroll.set)
        self.conversation.tag_configure(
            "user", foreground="#72b4ff", font=("Segoe UI", 10, "bold")
        )
        self.conversation.tag_configure(
            "assistant", foreground="#e7edf5", font=("Segoe UI", 10)
        )
        self.conversation.tag_configure(
            "error", foreground="#ff8d8d", font=("Segoe UI", 10)
        )

        input_row = ttk.Frame(center)
        input_row.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        input_row.columnconfigure(0, weight=1)
        self.input = ttk.Entry(input_row, font=("Segoe UI", 11))
        self.input.grid(row=0, column=0, sticky="ew", ipady=7)
        self.input.bind("<Return>", self._send_typed)
        ttk.Button(
            input_row, text="Send", style="Accent.TButton",
            command=self._send_typed,
        ).grid(row=0, column=1, padx=(8, 0))
        self.listen_button = ttk.Button(
            input_row, text="Listen", command=self._listen_once
        )
        self.listen_button.grid(row=0, column=2, padx=(8, 0))

        recent_panel = ttk.Frame(body, style="Panel.TFrame", padding=12)
        recent_panel.grid(row=0, column=2, sticky="ns", padx=(12, 0))
        ttk.Label(
            recent_panel, text="RECENT ACTIVITY", style="Panel.TLabel",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 10))
        self.history = ttk.Treeview(
            recent_panel, columns=("when", "command"), show="headings",
            height=18,
        )
        self.history.heading("when", text="TIME")
        self.history.heading("command", text="COMMAND")
        self.history.column("when", width=92, stretch=False)
        self.history.column("command", width=175, stretch=True)
        self.history.pack(fill="both", expand=True)
        ttk.Label(
            recent_panel, text="History stays on this device.",
            style="Panel.TLabel",
        ).pack(anchor="w", pady=(10, 0))

    def _append_message(self, speaker: str, text: str, tag: str) -> None:
        self.conversation.configure(state="normal")
        self.conversation.insert("end", f"{speaker}\n", tag)
        self.conversation.insert("end", text + "\n\n", tag)
        self.conversation.configure(state="disabled")
        self.conversation.see("end")

    def _send_typed(self, event: tk.Event | None = None) -> str | None:
        command = self.input.get().strip()
        self.input.delete(0, "end")
        if command:
            self._submit(command)
        return "break" if event is not None else None

    def _submit(self, command: str) -> None:
        self._append_message("You", command, "user")
        self.status.set("Working...")
        self._commands.put(("command", command))

    def _listen_once(self) -> None:
        if self._listening:
            return
        self._listening = True
        self.listen_button.configure(state="disabled")
        self.status.set("Listening...")
        threading.Thread(target=self._capture_speech, daemon=True).start()

    def _capture_speech(self) -> None:
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
            command = recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            self._events.put(("error", "No speech detected. Try Listen again."))
        except sr.UnknownValueError:
            self._events.put(("error", "I couldn't understand that. Please try again."))
        except sr.RequestError:
            self._events.put(
                ("error", "Speech recognition is unavailable. Check your internet.")
            )
        except (OSError, AttributeError) as error:
            self._events.put(("error", f"Microphone is unavailable: {error}"))
        else:
            self._events.put(("recognized", command))

    def _speak(self, text: str) -> None:
        try:
            if self._tts_engine is None:
                self._tts_engine = pyttsx3.init()
            self._tts_engine.say(text)
            self._tts_engine.runAndWait()
        except (RuntimeError, OSError) as error:
            self._events.put(("error", f"Text-to-speech is unavailable: {error}"))
            self._tts_engine = None

    def _work(self) -> None:
        while True:
            task = self._commands.get()
            if task is None:
                self.store.close()
                return
            _, command = task
            result = self.processor.process(command)
            if result.url:
                try:
                    opened = webbrowser.open(result.url)
                except OSError as error:
                    result = CommandResult(
                        f"I couldn't open that page: {error}", url=result.url
                    )
                else:
                    if not opened:
                        result = CommandResult(
                            "I couldn't open a browser. Check your system's "
                            "default browser.", url=result.url
                        )
            try:
                self.store.add(command, result.response, result.url)
                history = self.store.recent()
            except sqlite3.Error as error:
                self._events.put(
                    ("error", f"Could not save conversation history: {error}")
                )
                history = []
            self._speak(result.response)
            self._events.put(("result", (result, history)))

    def _load_history(self) -> None:
        try:
            self._show_history(self.store.recent())
        except sqlite3.Error as error:
            self._append_message(
                "Jarvis", f"Could not load saved history: {error}", "error"
            )

    def _show_history(self, entries: list[HistoryEntry]) -> None:
        for item in self.history.get_children():
            self.history.delete(item)
        for entry in entries:
            self.history.insert(
                "", "end", values=(entry.created_at[-5:], entry.command[:40])
            )

    def _drain_events(self) -> None:
        try:
            while True:
                event, payload = self._events.get_nowait()
                if event == "recognized":
                    self._listening = False
                    self.listen_button.configure(state="normal")
                    self._submit(str(payload))
                elif event == "error":
                    self._listening = False
                    self.listen_button.configure(state="normal")
                    self.status.set("Ready")
                    self._append_message("Notice", str(payload), "error")
                elif event == "result":
                    result, history = payload
                    self._append_message("Jarvis", result.response, "assistant")
                    self._show_history(history)
                    self.status.set("Ready")
                    if result.should_exit:
                        self.root.after(700, self._close)
        except queue.Empty:
            pass
        if self.root.winfo_exists():
            self.root.after(100, self._drain_events)

    def _close(self) -> None:
        self._commands.put(None)
        self.root.destroy()


def launch() -> None:
    root = tk.Tk()
    AssistantApp(root)
    root.mainloop()

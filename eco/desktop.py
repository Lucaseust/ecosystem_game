"""Interface de bureau ECOSYSTEM, avec Tkinter et la bibliothèque standard."""

import json
import os
from pathlib import Path
import queue
import secrets
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from dataclasses import asdict, dataclass

from . import i18n, store

ROOT = Path(__file__).resolve().parent.parent
PREFERENCES = ROOT / ".interface.json"
MODES = (
    "Réseau local (Wi-Fi commun)",
    "Adresse publique (tunnel)",
    "Ce PC uniquement (répétition)",
)
LANGUAGE = "fr"


def _t(text):
    return i18n.translate(text, LANGUAGE)


def configure_windows_dpi():
    if os.name == "nt":
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()


@dataclass
class Settings:
    language: str = "fr"
    mode: str = MODES[0]
    teams: str = "Automatique"
    port: str = "8000"
    key: str = ""
    data: str = "donnees-repetition"
    ip: str = ""

    def data_path(self):
        path = Path(self.data.strip()).expanduser()
        return (path if path.is_absolute() else ROOT / path).resolve()

    def validate(self):
        if self.language not in i18n.LOCALES:
            raise ValueError("Choose French or English / Choisissez français ou anglais.")
        if self.mode not in MODES:
            raise ValueError("Choisissez un mode de connexion.")
        if not str(self.port).isdigit() or not 1 <= int(self.port) <= 65535:
            raise ValueError("Le port doit être un nombre compris entre 1 et 65535.")
        if self.teams not in ("Automatique", "2", "3", "4", "5", "6"):
            raise ValueError("Choisissez entre 2 et 6 écosystèmes, ou Automatique.")
        if not self.data.strip():
            raise ValueError("Choisissez un dossier de sauvegarde.")
        if self.data_path().exists() and not self.data_path().is_dir():
            raise ValueError("Le chemin des sauvegardes désigne un fichier, pas un dossier.")
        if self.ip.strip():
            try:
                socket.inet_pton(socket.AF_INET, self.ip.strip())
            except OSError:
                raise ValueError(
                    "L’adresse locale doit être une adresse IPv4, par exemple 192.168.1.42."
                ) from None

    def command(self, key, new=False):
        self.validate()
        args = [
            sys.executable,
            "-u",
            str(ROOT / "serveur.py"),
            "--desktop",
            "--lang",
            self.language,
            "--port",
            str(int(self.port)),
            "--cle",
            key,
            "--donnees",
            str(self.data_path()),
        ]
        args += ["--host", "127.0.0.1" if self.mode == MODES[2] else "0.0.0.0"]
        if self.teams != "Automatique":
            args += ["--equipes", self.teams]
        if self.mode == MODES[1]:
            args += ["--tunnel"]
        if self.mode == MODES[2]:
            args += ["--ip", "127.0.0.1"]
        elif self.ip.strip():
            args += ["--ip", self.ip.strip()]
        if new:
            args += ["--nouvelle"]
        return args


def load_settings(path=PREFERENCES):
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return Settings()
        return Settings(
            **{
                k: v
                for k, v in raw.items()
                if k in Settings.__dataclass_fields__ and isinstance(v, str)
            }
        )
    except (OSError, ValueError, TypeError):
        return Settings()


def save_settings(settings, path=PREFERENCES):
    path = Path(path)
    tmp = path.with_suffix(".tmp")
    preferences = asdict(settings)
    preferences["key"] = ""  # Credentials belong in saves, never launcher preferences.
    tmp.write_text(json.dumps(preferences, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


class ServerController:
    """Possède uniquement le processus lancé ici ; ne touche pas aux autres serveurs."""

    def __init__(self):
        self.events = queue.Queue()
        self.process = None
        self.port = None
        self.key = None

    @property
    def running(self):
        return self.process is not None and self.process.poll() is None

    def start(self, settings, new=False):
        if self.running:
            raise ValueError("Le serveur de cette fenêtre est déjà en cours d’exécution.")
        settings.validate()
        # Refuse un conflit avant tout lancement ou écriture de sauvegarde.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(
                    ("127.0.0.1" if settings.mode == MODES[2] else "0.0.0.0", int(settings.port))
                )
            except OSError:
                raise ValueError(
                    "Le port %s est indisponible. Un serveur est peut-être déjà lancé ; choisissez un autre port ou arrêtez-le dans sa fenêtre."
                    % settings.port
                ) from None
        latest = None if new else store.latest(str(settings.data_path()))
        previous = store.load(latest) if latest else None
        previous_key = previous.get("host_key") if isinstance(previous, dict) else None
        if not isinstance(previous_key, str):
            previous_key = ""
        self.key = settings.key.strip() or previous_key or secrets.token_urlsafe(12)
        self.port = int(settings.port)
        self.process = subprocess.Popen(
            settings.command(self.key, new),
            cwd=str(ROOT),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        threading.Thread(target=self._read, args=(self.process,), daemon=True).start()

    def _read(self, process):
        try:
            for line in process.stdout:
                if line.startswith("ECOSYSTEM_READY "):
                    try:
                        self.events.put(("ready", json.loads(line.split(" ", 1)[1])))
                    except ValueError:
                        self.events.put(
                            ("log", "Annonce de démarrage illisible. Consultez le journal.\n")
                        )
                else:
                    self.events.put(("log", line))
        finally:
            process.stdout.close()
            self.events.put(("exit", process.wait()))

    def stop(self, timeout=20):
        process = self.process
        if not process or process.poll() is not None:
            return
        request = urllib.request.Request(
            "http://127.0.0.1:%d/api/host/action" % self.port,
            data=json.dumps({"cle": self.key, "action": "shutdown"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        deadline = time.monotonic() + timeout
        sent = False
        while process.poll() is None and time.monotonic() < deadline:
            if not sent:
                try:
                    with opener.open(request, timeout=2) as response:
                        sent = response.status == 200
                except urllib.error.HTTPError as exc:
                    raise RuntimeError("Le serveur a refusé l’arrêt (HTTP %d)." % exc.code) from exc
                except (OSError, urllib.error.URLError):
                    pass
            try:
                process.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                continue
        if process.poll() is None:
            raise RuntimeError(
                "L’arrêt n’a pas abouti. Réessayez ; le journal indique si le serveur répond encore."
            )


class DesktopApp:
    def __init__(self, root, preferences=PREFERENCES, settings=None):
        global LANGUAGE
        import tkinter as tk
        from tkinter import font, ttk

        self.tk, self.ttk = tk, ttk
        self.root, self.preferences = root, preferences
        available_fonts = set(font.families(root))
        self.font = next(
            (
                f
                for f in ("Calibri", "Segoe UI Variable", "Segoe UI", "Arial")
                if f in available_fonts
            ),
            "TkDefaultFont",
        )
        self.display_font = "Bahnschrift" if "Bahnschrift" in available_fonts else self.font
        font.nametofont("TkDefaultFont").configure(family=self.font, size=11)
        self.controller = ServerController()
        self.busy = False
        self.closing = False
        self.ready = None
        self.controls = []
        self.settings = settings or load_settings(preferences)
        LANGUAGE = self.settings.language
        self.vars = {k: tk.StringVar(value=v) for k, v in asdict(self.settings).items()}
        self.new_game = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value=_t("Serveur arrêté"))
        self.detail = tk.StringVar(value=_t("Réglez votre séance, puis cliquez sur Démarrer."))
        self.host_url = tk.StringVar(value=_t("Le lien enseignant apparaîtra au démarrage."))
        self.join_url = tk.StringVar(value=_t("Le lien étudiant apparaîtra au démarrage."))
        self.code = tk.StringVar(value="— — — —")
        root.title(_t("ecosystem · Votre séance"))
        scale = max(1, root.winfo_fpixels("1i") / 96)
        left, top, right, bottom = 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            area = wintypes.RECT()
            if ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(area), 0):
                left, top, right, bottom = area.left, area.top, area.right, area.bottom
        width = min(round(1010 * scale), right - left - 80)
        height = min(round(780 * scale), bottom - top - 120)
        x = left + (right - left - width) // 2
        y = top + max(10, (bottom - top - height - 50) // 2)
        root.geometry("%dx%d+%d+%d" % (width, height, x, y))
        root.minsize(min(round(880 * scale), width), min(round(680 * scale), height))
        root.configure(bg="#101920")
        root.protocol("WM_DELETE_WINDOW", self.close)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background="#101920")
        style.configure("Footer.TFrame", background="#18262f")
        style.configure("TLabel", background="#101920", foreground="#edf3f4", font=(self.font, 11))
        style.configure("Muted.TLabel", foreground="#afc0c9", font=(self.font, 10))
        style.configure("Heading.TLabel", foreground="#edf3f4", font=(self.display_font, 29))
        style.configure("Title.TLabel", font=(self.display_font, 12))
        style.configure("Code.TLabel", foreground="#d8edaa", font=(self.display_font, 34))
        style.configure(
            "TButton",
            padding=(15, 10),
            font=(self.font, 11),
            background="#21323e",
            foreground="#edf3f4",
            bordercolor="#415663",
            lightcolor="#21323e",
            darkcolor="#21323e",
            relief="flat",
            borderwidth=1,
        )
        style.map(
            "TButton",
            background=[("disabled", "#18262f"), ("active", "#2a3f4c"), ("pressed", "#344c5b")],
            foreground=[("disabled", "#8197a4")],
            bordercolor=[("disabled", "#293d49"), ("focus", "#a5d3eb"), ("active", "#8199a7")],
        )
        style.configure(
            "Primary.TButton",
            background="#d8edaa",
            foreground="#1b291b",
            bordercolor="#d8edaa",
            lightcolor="#d8edaa",
            darkcolor="#d8edaa",
        )
        style.map(
            "Primary.TButton",
            background=[("disabled", "#21323e"), ("active", "#e5f5c5"), ("pressed", "#c9dfa0")],
            foreground=[("disabled", "#8197a4")],
            bordercolor=[("disabled", "#344751"), ("active", "#e5f5c5")],
        )
        style.configure(
            "TRadiobutton",
            background="#101920",
            foreground="#edf3f4",
            font=(self.font, 11),
            indicatorbackground="#21323e",
            indicatorforeground="#d8edaa",
        )
        style.map(
            "TRadiobutton",
            background=[("active", "#101920")],
            foreground=[("disabled", "#8197a4")],
            indicatorbackground=[("selected", "#d8edaa"), ("disabled", "#21323e")],
            indicatorforeground=[("selected", "#1b291b")],
        )
        for name in ("TEntry", "TCombobox"):
            style.configure(
                name,
                padding=8,
                font=(self.font, 11),
                fieldbackground="#182a36",
                background="#182a36",
                foreground="#edf3f4",
                bordercolor="#415663",
                lightcolor="#182a36",
                darkcolor="#182a36",
                arrowcolor="#a5d3eb",
                insertcolor="#d8edaa",
                selectbackground="#a5d3eb",
                selectforeground="#101920",
            )
            style.map(
                name,
                fieldbackground=[("disabled", "#14222c"), ("readonly", "#182a36")],
                foreground=[("disabled", "#8197a4"), ("readonly", "#edf3f4")],
                bordercolor=[("focus", "#a5d3eb"), ("disabled", "#293d49")],
                background=[("active", "#263f4e")],
            )
        style.configure("TSeparator", background="#344751")
        style.configure(
            "Vertical.TScrollbar",
            background="#344751",
            troughcolor="#101920",
            bordercolor="#101920",
            arrowcolor="#afc0c9",
            lightcolor="#344751",
            darkcolor="#344751",
            arrowsize=12,
        )
        style.map("Vertical.TScrollbar", background=[("active", "#597483")])
        root.option_add("*TCombobox*Listbox.background", "#18262f")
        root.option_add("*TCombobox*Listbox.foreground", "#edf3f4")
        root.option_add("*TCombobox*Listbox.selectBackground", "#d8edaa")
        root.option_add("*TCombobox*Listbox.selectForeground", "#101920")
        root.option_add("*TCombobox*Listbox.font", (self.font, 11))
        self.icon = tk.PhotoImage(width=32, height=32)
        self.icon.put("#21323e", to=(0, 0, 32, 32))
        for rect in ((8, 8, 11, 25), (11, 8, 23, 11), (11, 15, 21, 18), (11, 22, 23, 25)):
            self.icon.put("#a5d3eb", to=rect)
        self.icon.put("#d8edaa", to=(24, 5, 29, 10))
        root.iconphoto(True, self.icon)
        if os.name == "nt":

            def dark_titlebar():
                try:
                    import ctypes

                    enabled = ctypes.c_int(1)
                    handle = ctypes.windll.user32.GetParent(root.winfo_id())
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        handle, 20, ctypes.byref(enabled), ctypes.sizeof(enabled)
                    )
                except (AttributeError, OSError):
                    pass

            root.after_idle(dark_titlebar)
        outer = ttk.Frame(root, padding=(24, 18))
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="ecosystem.", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(
            outer, text=_t("Un espace pour préparer, connecter et jouer."), style="Muted.TLabel"
        ).pack(anchor="w", pady=(4, 22))
        footer = ttk.Frame(outer, style="Footer.TFrame", padding=10)
        footer.pack(side="bottom", fill="x", pady=(12, 0))
        scrollframe = ttk.Frame(outer)
        scrollframe.pack(fill="both", expand=True)
        canvas = tk.Canvas(scrollframe, bg="#101920", highlightthickness=0)
        page_scrollbar = ttk.Scrollbar(scrollframe, orient="vertical", command=canvas.yview)
        page_scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=page_scrollbar.set)
        content = ttk.Frame(canvas)
        page = canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(page, width=event.width))
        content.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))

        def scroll_page(event):
            if not isinstance(event.widget, (tk.Text, ttk.Combobox)):
                canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

        root.bind("<MouseWheel>", scroll_page)
        columns = ttk.Frame(content)
        columns.pack(fill="both", expand=True)
        columns.columnconfigure(0, weight=1, uniform="column")
        columns.columnconfigure(1, weight=1, uniform="column")
        columns.rowconfigure(0, weight=1)
        left = ttk.Frame(columns, padding=(0, 0, 24, 0))
        left.grid(row=0, column=0, sticky="nsew")
        right = ttk.Frame(columns, padding=(22, 0, 0, 0))
        right.grid(row=0, column=1, sticky="nsew")
        ttk.Separator(columns, orient="vertical").grid(row=0, column=0, sticky="nse")
        ttk.Label(left, text=_t("Préparer la séance"), style="Title.TLabel").pack(
            anchor="w", pady=(0, 16)
        )
        self.field(left, _t("Langue de la séance"), "language", ("fr", "en"))
        self.controls[-1].configure(values=("Français", "English"))
        self.vars["language"].set("English" if LANGUAGE == "en" else "Français")
        self.controls[-1].bind("<<ComboboxSelected>>", self.change_language)
        self.field(left, _t("Connexion des étudiants"), "mode", MODES)
        pair = ttk.Frame(left)
        pair.pack(fill="x")
        for i, (label, key, choices) in enumerate(
            (
                (_t("Nombre d’écosystèmes"), "teams", (_t("Automatique"), "2", "3", "4", "5", "6")),
                (_t("Port du serveur"), "port", None),
            )
        ):
            cell = ttk.Frame(pair)
            cell.pack(side="left", fill="x", expand=True, padx=(0 if i == 0 else 8, 0))
            self.field(cell, label, key, choices)
        self.field(left, _t("Clé enseignant (vide = automatique)"), "key")
        ttk.Label(left, text=_t("Dossier des sauvegardes")).pack(anchor="w", pady=(7, 3))
        folder = ttk.Frame(left)
        folder.pack(fill="x")
        entry = ttk.Entry(folder, textvariable=self.vars["data"])
        entry.pack(side="left", fill="x", expand=True)
        browse = ttk.Button(folder, text=_t("Parcourir…"), command=self.browse)
        browse.pack(side="left", padx=(6, 0))
        self.controls += [entry, browse]
        ttk.Label(
            left,
            text=_t("Un chemin relatif se trouve dans le dossier du jeu."),
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(3, 0))
        self.field(left, _t("Adresse IPv4 locale (facultatif)"), "ip")
        ttk.Label(left, text=_t("Au démarrage"), style="Title.TLabel").pack(
            anchor="w", pady=(14, 6)
        )
        for label, value in (
            (_t("Reprendre la dernière partie sauvegardée"), False),
            (_t("Créer une nouvelle partie"), True),
        ):
            radio = ttk.Radiobutton(left, text=label, variable=self.new_game, value=value)
            radio.pack(anchor="w", pady=2)
            self.controls.append(radio)
        ttk.Label(
            left,
            text=_t(
                "Nouvelle partie : nouveau code, anciennes sauvegardes conservées.\nLes paramètres sont mémorisés au lancement."
            ),
            style="Muted.TLabel",
            wraplength=390,
        ).pack(anchor="w", pady=(8, 12))
        actions = ttk.Frame(footer, style="Footer.TFrame")
        actions.pack(fill="x", pady=(4, 0))
        self.start_button = ttk.Button(
            actions, text=_t("Démarrer le serveur"), style="Primary.TButton", command=self.start
        )
        self.start_button.pack(side="left", fill="x", expand=True)
        self.stop_button = ttk.Button(
            actions, text=_t("Arrêter et sauvegarder"), command=self.stop, state="disabled"
        )
        self.stop_button.pack(side="left", padx=(8, 0))
        ttk.Label(right, text=_t("Votre espace de jeu"), style="Title.TLabel").pack(
            anchor="w", pady=(0, 16)
        )
        ttk.Label(right, textvariable=self.status, style="Title.TLabel").pack(anchor="w")
        ttk.Label(right, textvariable=self.detail, wraplength=410, style="Muted.TLabel").pack(
            anchor="w", pady=(5, 14)
        )
        ttk.Label(right, text=_t("Code de la partie"), style="Muted.TLabel").pack(anchor="w")
        ttk.Label(right, textvariable=self.code, style="Code.TLabel").pack(anchor="w", pady=(0, 14))
        self.link_row(right, _t("Tableau enseignant"), self.host_url)
        self.open_host = ttk.Button(
            right,
            text=_t("Ouvrir le tableau de bord"),
            command=lambda: self.open_link("host_url"),
            state="disabled",
        )
        self.open_host.pack(fill="x", pady=(6, 12))
        self.link_row(right, _t("Connexion des étudiants"), self.join_url)
        share = ttk.Frame(right)
        share.pack(fill="x", pady=(6, 16))
        self.copy_join = ttk.Button(
            share, text=_t("Copier le lien étudiant"), command=self.copy_link, state="disabled"
        )
        self.copy_join.pack(side="left", fill="x", expand=True)
        self.open_player = ttk.Button(
            share, text=_t("Tester"), command=lambda: self.open_link("join_url"), state="disabled"
        )
        self.open_player.pack(side="left", padx=(6, 0))
        ttk.Button(
            right, text=_t("Ouvrir le dossier des sauvegardes"), command=self.open_data
        ).pack(fill="x", pady=(0, 8))
        ttk.Button(right, text=_t("Ouvrir la notice d’utilisation"), command=self.open_readme).pack(
            fill="x"
        )
        ttk.Label(
            right,
            text=_t(
                "Le tableau de bord conserve les commandes de jeu :\nphases, chronomètre, étudiants et classements.\nGardez cette fenêtre ouverte pendant la séance."
            ),
            wraplength=410,
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(12, 10))
        self.details_button = ttk.Button(
            content, text=_t("Détails de connexion"), command=self.toggle_details
        )
        self.details_button.pack(anchor="w", pady=(16, 8))
        self.log_frame = logframe = ttk.Frame(content)
        self.log = tk.Text(
            logframe,
            height=5,
            wrap="word",
            bg="#18262f",
            fg="#afc0c9",
            font=(self.font, 9),
            relief="flat",
            state="disabled",
            padx=12,
            pady=10,
            selectbackground="#a5d3eb",
            selectforeground="#101920",
        )
        self.log.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        scrollbar.pack(side="right", fill="y")
        self.log.configure(yscrollcommand=scrollbar.set)
        self.poll_id = root.after(100, self.poll)

    def field(self, parent, label, key, choices=None):
        self.ttk.Label(parent, text=_t(label)).pack(anchor="w", pady=(7, 3))
        if choices:
            self.vars[key].set(_t(self.vars[key].get()))
        widget = (
            self.ttk.Combobox(
                parent,
                textvariable=self.vars[key],
                values=tuple(_t(c) for c in choices),
                state="readonly",
            )
            if choices
            else self.ttk.Entry(parent, textvariable=self.vars[key])
        )
        widget.pack(fill="x")
        self.controls.append(widget)

    def link_row(self, parent, label, variable):
        self.ttk.Label(parent, text=_t(label), style="Muted.TLabel").pack(anchor="w")
        self.ttk.Entry(parent, textvariable=variable, state="readonly", font=(self.font, 10)).pack(
            fill="x", pady=(3, 0)
        )

    def toggle_details(self):
        if self.log_frame.winfo_manager():
            self.log_frame.pack_forget()
            self.details_button.configure(text=_t("Détails de connexion"))
        else:
            self.log_frame.pack(fill="both", expand=False)
            self.details_button.configure(text=_t("Masquer les détails"))

    def current_settings(self):
        values = {k: v.get() for k, v in self.vars.items()}
        values["language"] = "en" if values["language"] == "English" else "fr"
        for key, choices in (("mode", MODES), ("teams", ("Automatique", "2", "3", "4", "5", "6"))):
            values[key] = next(
                (choice for choice in choices if values[key] in (choice, _t(choice))), values[key]
            )
        return Settings(**values)

    def change_language(self, event=None):
        if self.controller.running or self.busy:
            return
        settings = self.current_settings()
        new_game = self.new_game.get()
        self.root.after_cancel(self.poll_id)
        for widget in self.root.winfo_children():
            widget.destroy()
        app = DesktopApp(self.root, self.preferences, settings=settings)
        app.new_game.set(new_game)

    def browse(self):
        from tkinter import filedialog

        folder = filedialog.askdirectory(
            parent=self.root, title=_t("Dossier des sauvegardes"), initialdir=str(ROOT)
        )
        if folder:
            self.vars["data"].set(folder)

    def set_running(self, running):
        for widget in self.controls:
            widget.configure(
                state="disabled"
                if running
                else "readonly"
                if isinstance(widget, self.ttk.Combobox)
                else "normal"
            )
        self.start_button.configure(state="disabled" if running else "normal")
        self.stop_button.configure(state="normal" if running else "disabled")

    def append_log(self, line):
        self.log.configure(state="normal")
        self.log.insert("end", line)
        if int(self.log.index("end-1c").split(".")[0]) > 600:
            self.log.delete("1.0", "100.0")
        self.log.see("end")
        self.log.configure(state="disabled")

    def start(self):
        from tkinter import messagebox

        if self.busy or self.controller.running:
            return
        settings = self.current_settings()
        try:
            settings.validate()
            self.controller.start(settings, self.new_game.get())
        except (ValueError, OSError) as exc:
            messagebox.showerror(_t("Démarrage impossible"), _t(str(exc)), parent=self.root)
            return
        self.settings = settings
        self.ready = None
        self.set_running(True)
        self.status.set(_t("Démarrage en cours…"))
        self.detail.set(
            _t("Ouverture du tunnel ; cela peut prendre une minute.")
            if settings.mode == MODES[1]
            else _t("Préparation de la partie…")
        )
        self.code.set("— — — —")
        self.host_url.set(_t("Connexion en cours…"))
        self.join_url.set(_t("Connexion en cours…"))
        self.append_log(_t("\n── Démarrage d’une séance ──\n"))
        try:
            save_settings(settings, self.preferences)
        except OSError as exc:
            self.append_log(_t("Paramètres non mémorisés : %s\n") % exc)

    def stop(self):
        if self.busy or not self.controller.running:
            return
        self.busy = True
        self.stop_button.configure(state="disabled")
        self.status.set(_t("Arrêt et sauvegarde…"))
        self.detail.set(_t("Le serveur termine les échanges et écrit la sauvegarde."))
        for button in (self.open_host, self.open_player, self.copy_join):
            button.configure(state="disabled")

        def worker():
            try:
                self.controller.stop()
            except (OSError, RuntimeError) as exc:
                self.controller.events.put(("stop_error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        from tkinter import messagebox

        for _ in range(150):
            try:
                kind, value = self.controller.events.get_nowait()
            except queue.Empty:
                break
            if kind == "log":
                self.append_log(value)
            elif kind == "ready":
                self.ready = value
                self.host_url.set(value["host_url"])
                self.join_url.set(value["join_url"])
                self.code.set(value["code"])
                if not self.busy:
                    self.status.set(_t("Serveur en cours d’exécution"))
                    detail = _t(
                        "Projetez le tableau de bord ; son QR permet de rejoindre la partie."
                    )
                    if self.settings.mode == MODES[1] and not value.get("public"):
                        detail = _t(
                            "Le tunnel n’a pas abouti : connexion locale uniquement. Consultez le journal."
                        )
                    self.detail.set(detail)
                    for button in (self.open_host, self.open_player, self.copy_join):
                        button.configure(state="normal")
            elif kind == "exit":
                self.busy = False
                self.set_running(False)
                self.status.set(
                    _t("Serveur arrêté")
                    if value == 0
                    else _t("Le serveur s’est arrêté avec une erreur")
                )
                self.detail.set(
                    _t("La partie est sauvegardée. Vous pouvez la reprendre.")
                    if value == 0
                    else _t("Consultez le journal pour corriger le problème avant de relancer.")
                )
                self.new_game.set(False)
                if value != 0 and not self.log_frame.winfo_manager():
                    self.toggle_details()
                for button in (self.open_host, self.open_player, self.copy_join):
                    button.configure(state="disabled")
                if self.closing:
                    self.root.destroy()
                    return
            elif kind == "stop_error":
                self.busy = False
                self.closing = False
                self.status.set(_t("Serveur toujours en cours d’exécution"))
                self.detail.set(_t(value))
                self.stop_button.configure(state="normal")
                if self.ready:
                    for button in (self.open_host, self.open_player, self.copy_join):
                        button.configure(state="normal")
                messagebox.showerror(_t("Arrêt non terminé"), _t(value), parent=self.root)
        self.poll_id = self.root.after(100, self.poll)

    def open_link(self, key):
        if self.ready:
            webbrowser.open(self.ready[key])

    def copy_link(self):
        if self.ready:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.ready["join_url"])
            self.detail.set(_t("Lien étudiant copié dans le presse-papiers."))

    def open_data(self):
        from tkinter import messagebox

        path = (self.settings if self.controller.running else self.current_settings()).data_path()
        if not path.is_dir():
            messagebox.showinfo(
                _t("Dossier des sauvegardes"),
                _t("Le dossier sera créé au premier démarrage du serveur."),
                parent=self.root,
            )
            return
        self.open_file(path)

    def open_readme(self):
        self.open_file(ROOT / ("NOTICE.html" if LANGUAGE == "en" else "NOTICE.fr.html"))

    def open_file(self, path):
        from tkinter import messagebox

        try:
            if os.name == "nt":
                os.startfile(str(path))
            else:
                subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(path)])
        except OSError as exc:
            messagebox.showerror(_t("Ouverture impossible"), str(exc), parent=self.root)

    def close(self):
        from tkinter import messagebox

        if self.busy:
            self.closing = True
            return
        if self.controller.running:
            if not messagebox.askyesno(
                _t("Fermer ECOSYSTEM"),
                _t("Arrêter le serveur, sauvegarder la partie et fermer cette fenêtre ?"),
                parent=self.root,
            ):
                return
            self.closing = True
            self.stop()
        else:
            self.root.destroy()


def main():
    import tkinter as tk

    configure_windows_dpi()
    root = tk.Tk()
    DesktopApp(root)
    root.mainloop()

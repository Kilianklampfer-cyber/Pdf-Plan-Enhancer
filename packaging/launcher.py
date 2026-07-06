from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path
from tkinter import Button, Label, Tk, messagebox

import uvicorn


APP_NAME = "pdf-plan-enhancer"


def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[1] / "pdf-plan-enhancer-local-download"


def writable_workspace() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / APP_NAME
    workspace = root / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def log_path() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / APP_NAME
    root.mkdir(parents=True, exist_ok=True)
    return root / "launcher.log"


def log(message: str) -> None:
    try:
        with log_path().open("a", encoding="utf-8") as handle:
            handle.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")
    except OSError:
        pass


def find_free_port(start: int = 8765) -> int:
    port = start
    while port < start + 200:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1
    raise RuntimeError("Kein freier lokaler Port gefunden.")


def configure_environment(app_root: Path) -> Path:
    backend = app_root / "app" / "backend"
    sys.path.insert(0, str(backend))
    os.environ["PDF_PLAN_ENHANCER_WORKSPACE"] = str(writable_workspace())

    bundled_poppler = app_root / "poppler" / "Library" / "bin"
    installed_poppler = Path(r"C:\Program Files\poppler\Library\bin")
    if bundled_poppler.exists():
        os.environ["POPPLER_PATH"] = str(bundled_poppler)
    elif installed_poppler.exists():
        os.environ["POPPLER_PATH"] = str(installed_poppler)

    return backend


class LauncherWindow:
    def __init__(self) -> None:
        self.app_root = base_dir()
        self.backend = configure_environment(self.app_root)
        self.port = find_free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        self.server: uvicorn.Server | None = None
        self.thread: threading.Thread | None = None

        self.root = Tk()
        self.root.title("pdf-plan-enhancer")
        self.root.geometry("390x180")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.stop)

        self.status = Label(self.root, text="Starte lokale App...", padx=18, pady=18, anchor="w", justify="left")
        self.status.pack(fill="x")
        self.open_button = Button(self.root, text="App im Browser oeffnen", command=self.open_browser, state="disabled")
        self.open_button.pack(fill="x", padx=18, pady=6)
        self.stop_button = Button(self.root, text="Beenden", command=self.stop)
        self.stop_button.pack(fill="x", padx=18, pady=6)

    def start_server(self) -> None:
        try:
            os.chdir(self.backend)
            log(f"Starting server from {self.backend} on {self.url}")
            from main import app

            config = uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="warning", log_config=None)
            self.server = uvicorn.Server(config)
            self.server.run()
        except Exception as exc:  # pragma: no cover - visible launcher error path
            log(f"ERROR {exc!r}")
            self.root.after(0, lambda: self.show_error(exc))

    def show_error(self, exc: Exception) -> None:
        self.status.config(text="Start fehlgeschlagen.")
        messagebox.showerror("pdf-plan-enhancer", f"Die lokale App konnte nicht gestartet werden:\n\n{exc}")

    def wait_until_ready(self) -> None:
        for _ in range(80):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex(("127.0.0.1", self.port)) == 0:
                    self.root.after(0, self.ready)
                    return
            time.sleep(0.1)
        self.root.after(0, lambda: self.show_error(RuntimeError("Server hat nicht rechtzeitig geantwortet.")))

    def ready(self) -> None:
        self.status.config(text=f"pdf-plan-enhancer laeuft lokal:\n{self.url}")
        self.open_button.config(state="normal")
        self.open_browser()

    def open_browser(self) -> None:
        webbrowser.open(self.url)

    def run(self) -> None:
        self.thread = threading.Thread(target=self.start_server, daemon=True)
        self.thread.start()
        threading.Thread(target=self.wait_until_ready, daemon=True).start()
        self.root.mainloop()

    def stop(self) -> None:
        if self.server:
            self.server.should_exit = True
        self.root.destroy()


if __name__ == "__main__":
    LauncherWindow().run()

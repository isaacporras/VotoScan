from __future__ import annotations

from pathlib import Path
from queue import Empty, Queue
from threading import Thread
import os
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from processor import ProcessArtifacts, process_voting_screenshot


class VotoScanApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("VotoScan")
        self.root.geometry("1120x760")
        self.root.minsize(960, 640)

        self.screenshot_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value=str(_default_downloads_dir()))
        self.session_name_var = tk.StringVar(value="mocion123")
        self.status_var = tk.StringVar(value="Select a screenshot to begin.")

        self.result_queue: Queue[tuple[str, object]] = Queue()
        self.preview_image: ImageTk.PhotoImage | None = None
        self.generated_pdf_path: Path | None = None

        self._build_layout()

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        controls = ttk.Frame(self.root, padding=16)
        controls.grid(row=0, column=0, sticky="ew")
        controls.columnconfigure(1, weight=1)

        ttk.Label(controls, text="Screenshot").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=6)
        ttk.Entry(controls, textvariable=self.screenshot_var).grid(row=0, column=1, sticky="ew", pady=6)
        ttk.Button(controls, text="Browse", command=self._choose_screenshot).grid(row=0, column=2, padx=(8, 0), pady=6)

        ttk.Label(controls, text="Output folder").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=6)
        ttk.Entry(controls, textvariable=self.output_dir_var).grid(row=1, column=1, sticky="ew", pady=6)
        ttk.Button(controls, text="Browse", command=self._choose_output_dir).grid(row=1, column=2, padx=(8, 0), pady=6)

        ttk.Label(controls, text="Session name").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=6)
        ttk.Entry(controls, textvariable=self.session_name_var).grid(row=2, column=1, sticky="ew", pady=6)

        actions = ttk.Frame(controls)
        actions.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        actions.columnconfigure(2, weight=1)

        self.process_button = ttk.Button(actions, text="Process", command=self._start_processing)
        self.process_button.grid(row=0, column=0, sticky="w")

        self.open_pdf_button = ttk.Button(actions, text="Open PDF", command=self._open_pdf, state="disabled")
        self.open_pdf_button.grid(row=0, column=1, sticky="w", padx=(8, 0))

        self.progress = ttk.Progressbar(actions, mode="indeterminate", length=220)
        self.progress.grid(row=0, column=3, sticky="e")

        status = ttk.Label(self.root, textvariable=self.status_var, padding=(16, 0, 16, 12))
        status.grid(row=2, column=0, sticky="ew")

        preview_frame = ttk.LabelFrame(self.root, text="PDF Preview", padding=16)
        preview_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.preview_label = ttk.Label(
            preview_frame,
            text="The generated PDF preview will appear here.",
            anchor="center",
            justify="center",
        )
        self.preview_label.grid(row=0, column=0, sticky="nsew")

    def _choose_screenshot(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select voting screenshot",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
                ("All files", "*.*"),
            ],
        )
        if selected:
            self.screenshot_var.set(selected)

    def _choose_output_dir(self) -> None:
        selected = filedialog.askdirectory(
            title="Select output folder",
            initialdir=self.output_dir_var.get() or str(_default_downloads_dir()),
        )
        if selected:
            self.output_dir_var.set(selected)

    def _start_processing(self) -> None:
        screenshot = Path(self.screenshot_var.get().strip())
        output_dir = Path(self.output_dir_var.get().strip() or _default_downloads_dir())
        session_name = self.session_name_var.get().strip() or screenshot.stem or "voting_session"

        if not screenshot.exists():
            messagebox.showerror("Missing screenshot", "Please select a valid screenshot file.")
            return

        self.process_button.config(state="disabled")
        self.open_pdf_button.config(state="disabled")
        self.generated_pdf_path = None
        self.status_var.set("Processing screenshot. This may take a few seconds...")
        self.progress.start(12)
        self._set_preview_message("Generating report...")

        worker = Thread(
            target=self._process_in_background,
            args=(screenshot, output_dir, session_name),
            daemon=True,
        )
        worker.start()
        self.root.after(150, self._poll_result_queue)

    def _process_in_background(self, screenshot: Path, output_dir: Path, session_name: str) -> None:
        try:
            artifacts = process_voting_screenshot(
                screenshot_path=screenshot,
                output_dir=output_dir,
                session_name=session_name,
            )
        except Exception as exc:
            self.result_queue.put(("error", exc))
            return

        self.result_queue.put(("success", artifacts))

    def _poll_result_queue(self) -> None:
        try:
            result_type, payload = self.result_queue.get_nowait()
        except Empty:
            self.root.after(150, self._poll_result_queue)
            return

        self.progress.stop()
        self.process_button.config(state="normal")

        if result_type == "error":
            self.status_var.set("Processing failed.")
            self._set_preview_message("The report could not be generated.")
            messagebox.showerror("Processing failed", str(payload))
            return

        artifacts = payload
        if not isinstance(artifacts, ProcessArtifacts):
            self.status_var.set("Processing failed.")
            self._set_preview_message("Unexpected processing result.")
            return

        self.generated_pdf_path = artifacts.pdf_path
        self.open_pdf_button.config(state="normal")
        self.status_var.set(f"Done. PDF saved to: {artifacts.pdf_path}")
        self._show_preview(artifacts.preview_image_path)

    def _show_preview(self, image_path: Path) -> None:
        with Image.open(image_path) as image:
            image.thumbnail((920, 560))
            preview = ImageTk.PhotoImage(image.copy())

        self.preview_image = preview
        self.preview_label.configure(image=self.preview_image, text="")

    def _set_preview_message(self, message: str) -> None:
        self.preview_image = None
        self.preview_label.configure(image="", text=message)

    def _open_pdf(self) -> None:
        if self.generated_pdf_path is None:
            return
        webbrowser.open(self.generated_pdf_path.resolve().as_uri())


def _default_downloads_dir() -> Path:
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Downloads"


def run_app() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    app = VotoScanApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()

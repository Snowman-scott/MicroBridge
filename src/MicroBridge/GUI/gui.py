import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from MicroBridge.Core.core import convert_ndpa_to_lmd_core, derive_output_filename


COLOR_GREEN = "#4CAF50"
COLOR_RED = "#F44336"
COLOR_ORANGE = "#FF9800"
COLOR_GREY = "#888888"
PAD = 10


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MicroBridge")
        self.geometry("1050x650")
        self.minsize(850, 450)

        self.input_files: list[str] = []
        self.output_dir: str | None = None
        self._converting = False

        self._setup_ui()
        self._log("Ready — select files to begin", COLOR_GREY)

    # ── UI Setup ──────────────────────────────────────────────────────

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=2, uniform="col")
        self.grid_columnconfigure(1, weight=3, uniform="col")
        self.grid_rowconfigure(0, weight=1)

        self._build_left()
        self._build_right()

    def _build_left(self):
        left = ctk.CTkFrame(self, corner_radius=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(PAD, 5), pady=PAD)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(
            left,
            text="MicroBridge",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=PAD, pady=(14, 4), sticky="w")

        ctk.CTkLabel(
            left,
            text="NDPA → LMD XML Converter",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_GREY,
        ).grid(row=1, column=0, padx=PAD, pady=(0, 10), sticky="w")

        # ── Type selector ──
        ctk.CTkLabel(left, text="Conversion Type:", anchor="w").grid(
            row=2, column=0, padx=PAD, pady=(0, 2), sticky="ew"
        )
        self.type_var = ctk.StringVar(value="NDPA")
        ctk.CTkComboBox(
            left,
            values=["Auto", "NDPA", "CSV"],
            variable=self.type_var,
            state="readonly",
            corner_radius=6,
        ).grid(row=3, column=0, padx=PAD, pady=(0, 12), sticky="ew")

        # ── File action buttons ──
        btn_frame = ctk.CTkFrame(left, fg_color="transparent")
        btn_frame.grid(row=4, column=0, padx=PAD, pady=(0, 4), sticky="ew")
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            btn_frame, text="Select Files", command=self._select_files
        ).grid(row=0, column=0, padx=2, sticky="ew")

        ctk.CTkButton(
            btn_frame, text="Select Folder", command=self._select_folder
        ).grid(row=0, column=1, padx=2, sticky="ew")

        ctk.CTkButton(
            btn_frame, text="Output Folder", command=self._select_output
        ).grid(row=0, column=2, padx=2, sticky="ew")

        # ── Selected files ──
        self.files_label = ctk.CTkLabel(
            left, text="Selected Files: (none)", anchor="w"
        )
        self.files_label.grid(row=5, column=0, padx=PAD, pady=(8, 2), sticky="ew")

        self.files_text = ctk.CTkTextbox(left, state="disabled", corner_radius=6)
        self.files_text.grid(row=6, column=0, padx=PAD, pady=(0, 6), sticky="nsew")

        # ── Output indicator ──
        self.output_label = ctk.CTkLabel(
            left,
            text="Output: (same directory as input)",
            anchor="w",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_GREY,
        )
        self.output_label.grid(row=7, column=0, padx=PAD, pady=(0, 8), sticky="ew")

        # ── Convert button ──
        self.convert_btn = ctk.CTkButton(
            left,
            text="Convert",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._convert,
            corner_radius=8,
            fg_color="#2B7A4B",
            hover_color="#1E5F3A",
            text_color="#FFFFFF",
        )
        self.convert_btn.grid(row=8, column=0, padx=PAD, pady=(0, 14), sticky="ew")

    def _build_right(self):
        right = ctk.CTkFrame(self, corner_radius=10)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, PAD), pady=PAD)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        # ── Header row ──
        hdr = ctk.CTkFrame(right, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=PAD, pady=(14, 6), sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr,
            text="Conversion Log",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            hdr,
            text="Clear",
            width=60,
            height=26,
            font=ctk.CTkFont(size=11),
            command=self._clear_log,
            corner_radius=4,
            fg_color="#3A3A3A",
            hover_color="#555555",
        ).grid(row=0, column=1)

        # ── Log area ──
        self.log_text = ctk.CTkTextbox(right, state="disabled", corner_radius=6)
        self.log_text.grid(row=1, column=0, padx=PAD, pady=(0, PAD), sticky="nsew")

        self.log_text.tag_config("green", foreground=COLOR_GREEN)
        self.log_text.tag_config("red", foreground=COLOR_RED)
        self.log_text.tag_config("orange", foreground=COLOR_ORANGE)
        self.log_text.tag_config("grey", foreground=COLOR_GREY)
        self.log_text.tag_config("bold", font=ctk.CTkFont(weight="bold"))

    # ── Logging ───────────────────────────────────────────────────────

    def _log(self, msg: str, tag: str | None = None):
        self.log_text.configure(state="normal")
        if tag:
            self.log_text.insert("end", msg + "\n", tag)
        else:
            self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    # ── File selection ────────────────────────────────────────────────

    def _select_files(self):
        files = filedialog.askopenfilenames(
            title="Select NDPA files",
            filetypes=[("NDPA files", "*.ndpa"), ("All files", "*.*")],
        )
        if files:
            self.input_files = list(files)
            self._update_files_display()

    def _select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with NDPA files")
        if folder:
            self.input_files = sorted(
                str(f) for f in Path(folder).iterdir() if f.suffix == ".ndpa"
            )
            self._update_files_display()

    def _select_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_dir = folder
            short = f"...{folder[-50:]}" if len(folder) > 53 else folder
            self.output_label.configure(
                text=f"Output: {short}", text_color=COLOR_ORANGE
            )

    def _update_files_display(self):
        self.files_text.configure(state="normal")
        self.files_text.delete("1.0", "end")
        for f in self.input_files:
            self.files_text.insert("end", f + "\n")
        self.files_text.configure(state="disabled")

        count = len(self.input_files)
        self.files_label.configure(text=f"Selected Files: ({count})")
        self._log(f"{count} file(s) selected", "green" if count else None)

    # ── Conversion ────────────────────────────────────────────────────

    def _convert(self):
        if self._converting:
            return
        if not self.input_files:
            self._log("Nothing to convert — select files first", "red")
            return
        self._converting = True
        self.convert_btn.configure(
            state="disabled",
            text="Converting...",
            fg_color="#555555",
            hover_color="#555555",
        )
        threading.Thread(target=self._convert_worker, daemon=True).start()

    def _convert_finished(self):
        self._converting = False
        self.convert_btn.configure(
            state="normal",
            text="Convert",
            fg_color="#2B7A4B",
            hover_color="#1E5F3A",
        )

    def _convert_worker(self):
        files = self.input_files[:]
        out_dir = self.output_dir
        total = len(files)
        ok = 0
        fails: list[tuple[str, str | Exception]] = []

        for i, file in enumerate(files):
            self.after(0, self._log, f"[{i+1}/{total}] {Path(file).name} ...", "grey")

            if Path(file).suffix != ".ndpa":
                msg = f"Expected a '.ndpa' file, got a '{Path(file).suffix}' file Instead"
                fails.append((file, msg))
                self.after(0, self._log, f"  {msg}", "red")
                continue

            output = derive_output_filename(file)
            if out_dir:
                output = str(Path(out_dir) / Path(output).name)

            try:
                convert_ndpa_to_lmd_core(file, output)
                ok += 1
                self.after(
                    0, self._log,
                    f"  Successfully converted ndpa into LMD xml :3", "green",
                )
            except (ValueError, FileNotFoundError, IsADirectoryError) as e:
                fails.append((file, e))
                self.after(
                    0, self._log,
                    f"  Converting the ndpa to an LMD xml failed: {e}", "red",
                )

        self.after(0, self._log, "")
        self.after(0, self._log, "=" * 47, "bold")
        if ok == total:
            self.after(
                0, self._log,
                f"{ok}/{total} files converted. \nAll files converted fine :3", "green",
            )
        else:
            self.after(0, self._log, f"{len(fails)}/{total} failed to convert 3:", "red")
            self.after(0, self._log, "The files that failed to convert were:", "bold")
            for fname, err in fails:
                self.after(
                    0, self._log, f"  {Path(fname).name} errored with: {err}", "red",
                )

        self.after(0, self._convert_finished)


def run():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()

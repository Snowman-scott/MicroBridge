import sys
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from MicroBridge.Core.core import convert_ndpa_to_lmd_core, derive_output_filename


PAD = 12


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MicroBridge")
        self.geometry("1050x650")
        self.minsize(850, 450)

        self._set_window_icon()

        self.input_files: list[str] = []
        self.output_dir: str | None = None
        self._converting = False

        self._setup_ui()
        self._log("ready — pick some files")

    def _set_window_icon(self):
        if sys.platform != "win32":
            return
        base = getattr(sys, "_MEIPASS", None)
        if not base:
            return
        icon = Path(base) / "MicroBridge_Icon.ico"
        if icon.exists():
            self.iconbitmap(str(icon))

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=2, uniform="col")
        self.grid_columnconfigure(1, weight=3, uniform="col")
        self.grid_rowconfigure(0, weight=1)

        self._build_left()
        self._build_right()

    def _build_left(self):
        left = ctk.CTkFrame(self, corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(PAD, 6), pady=PAD)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(
            left,
            text="MicroBridge",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, padx=PAD, pady=(16, 2), sticky="w")

        sep = ctk.CTkFrame(left, height=1)
        sep.grid(row=1, column=0, padx=PAD, pady=(4, 12), sticky="ew")

        ctk.CTkLabel(left, text="Conversion type", anchor="w", font=ctk.CTkFont(size=11)).grid(
            row=2, column=0, padx=PAD, pady=(0, 4), sticky="ew"
        )
        self.type_var = ctk.StringVar(value="NDPA")
        ctk.CTkComboBox(
            left,
            values=["Auto", "NDPA", "CSV"],
            variable=self.type_var,
            state="readonly",
            corner_radius=6,
        ).grid(row=3, column=0, padx=PAD, pady=(0, 14), sticky="ew")

        btn_frame = ctk.CTkFrame(left, fg_color="transparent")
        btn_frame.grid(row=4, column=0, padx=PAD, pady=(0, 2), sticky="ew")
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            btn_frame, text="Select input files", command=self._select_files, corner_radius=6,
            fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("#d0d0d0", "#333333"),
            border_width=1,
        ).grid(row=0, column=0, padx=2, sticky="ew")

        ctk.CTkButton(
            btn_frame, text="Scan a folder", command=self._select_folder, corner_radius=6,
            fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("#d0d0d0", "#333333"),
            border_width=1,
        ).grid(row=0, column=1, padx=2, sticky="ew")

        ctk.CTkButton(
            btn_frame, text="Pick output folder", command=self._select_output, corner_radius=6,
            fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("#d0d0d0", "#333333"),
            border_width=1,
        ).grid(row=0, column=2, padx=2, sticky="ew")

        self.files_label = ctk.CTkLabel(
            left, text="Selected files: (none)", anchor="w", font=ctk.CTkFont(size=11),
        )
        self.files_label.grid(row=5, column=0, padx=PAD, pady=(10, 2), sticky="ew")

        self.files_text = ctk.CTkTextbox(left, state="disabled", corner_radius=6)
        self.files_text.grid(row=6, column=0, padx=PAD, pady=(0, 6), sticky="nsew")

        self.output_label = ctk.CTkLabel(
            left,
            text="Output: (same dir as input)",
            anchor="w",
            font=ctk.CTkFont(size=11),
        )
        self.output_label.grid(row=7, column=0, padx=PAD, pady=(0, 8), sticky="ew")

        self.convert_btn = ctk.CTkButton(
            left,
            text="Convert",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._convert,
            corner_radius=8,
        )
        self.convert_btn.grid(row=8, column=0, padx=PAD, pady=(4, 16), sticky="ew")

    def _build_right(self):
        right = ctk.CTkFrame(self, corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, PAD), pady=PAD)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(right, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=PAD, pady=(14, 6), sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr,
            text="Log",
            font=ctk.CTkFont(size=16),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            hdr,
            text="Clear",
            width=56,
            height=24,
            font=ctk.CTkFont(size=11),
            command=self._clear_log,
            corner_radius=4,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("#d0d0d0", "#333333"),
            border_width=1,
        ).grid(row=0, column=1)

        self.log_text = ctk.CTkTextbox(right, state="disabled", corner_radius=6)
        self.log_text.grid(row=1, column=0, padx=PAD, pady=(0, PAD), sticky="nsew")

        self.log_text.tag_config("ok", foreground="#2b8a5e")
        self.log_text.tag_config("err", foreground="#c0392b")
        self.log_text.tag_config("warn", foreground="#b45309")
        self.log_text.tag_config("muted", foreground="#6b7280")

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

    def _select_files(self):
        files = filedialog.askopenfilenames(
            title="Select input files",
            filetypes=[("NDPA files", "*.ndpa"), ("All files", "*.*")],
        )
        if files:
            self.input_files = list(files)
            self._update_files_display()

    def _select_folder(self):
        folder = filedialog.askdirectory(title="Select a folder")
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
            self.output_label.configure(text=f"Output: {short}")

    def _update_files_display(self):
        self.files_text.configure(state="normal")
        self.files_text.delete("1.0", "end")
        for f in self.input_files:
            self.files_text.insert("end", f + "\n")
        self.files_text.configure(state="disabled")

        count = len(self.input_files)
        self.files_label.configure(text=f"Selected files: ({count})")
        self._log(f"{count} file(s) selected", "ok" if count else None)

    def _convert(self):
        if self._converting:
            return
        if not self.input_files:
            self._log("nothing to convert — pick files first", "err")
            return
        self._converting = True
        self.convert_btn.configure(
            state="disabled",
            text="Converting...",
        )
        threading.Thread(target=self._convert_worker, daemon=True).start()

    def _convert_finished(self):
        self._converting = False
        self.convert_btn.configure(
            state="normal",
            text="Convert",
        )

    def _convert_worker(self):
        files = self.input_files[:]
        out_dir = self.output_dir
        total = len(files)
        ok = 0
        fails: list[tuple[str, str | Exception]] = []

        for i, file in enumerate(files):
            self.after(0, self._log, f"[{i+1}/{total}] {Path(file).name} ...", "muted")

            if Path(file).suffix != ".ndpa":
                msg = f"expected '.ndpa', got '{Path(file).suffix}'"
                fails.append((file, msg))
                self.after(0, self._log, f"  {msg}", "err")
                continue

            output = derive_output_filename(file)
            if out_dir:
                output = str(Path(out_dir) / Path(output).name)

            try:
                convert_ndpa_to_lmd_core(file, output)
                ok += 1
                self.after(0, self._log, f"  done", "ok")
            except (ValueError, FileNotFoundError, IsADirectoryError) as e:
                fails.append((file, e))
                self.after(0, self._log, f"  failed: {e}", "err")

        self.after(0, self._log, "")
        self.after(0, self._log, "─" * 40, "muted")
        if ok == total:
            self.after(0, self._log, f"{ok}/{total} converted", "ok")
        else:
            self.after(0, self._log, f"{len(fails)}/{total} failed", "err")
            self.after(0, self._log, "failed files:", "warn")
            for fname, err in fails:
                self.after(0, self._log, f"  {Path(fname).name} — {err}", "err")

        self.after(0, self._convert_finished)


def run():
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()

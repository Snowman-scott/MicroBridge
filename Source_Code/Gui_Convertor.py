#!/usr/bin/env python3
"""
MicroBridge - Gui_Convertor.py

Thread-safe GUI for converting Hamamatsu NDP (.ndpa) and CSV annotations into a
simplified LMD-compatible XML. This file is a cleaned implementation that:

- Uses a background worker thread for conversions.
- Uses a queue.Queue for thread-safe log/progress messages.
- Safely extracts text from minidom elements (avoids AttributeError).
- Writes outputs to a selected output folder or the input file's folder.
- Fixes a progress/idx bug and ensures the convert button is re-enabled on the main thread.
"""

import csv
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from xml.dom import minidom

# Configuration
WINDOW_TITLE = "MicroBridge - NDP/CSV to LMD Converter"
DEFAULT_OUTPUT_EXT = ".xml"
QUEUE_POLL_MS = 100


class MicroBridgeConverterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # State
        self.input_files = []  # absolute paths
        self.input_format = tk.StringVar(value="auto")  # 'auto', 'ndpa', 'csv'
        self.output_extension = ".xml"
        self.output_folder = tk.StringVar(value="")  # empty => use input file folder

        # Thread-safe queue for log/progress updates
        self.queue = queue.Queue()

        # Build UI
        self._build_ui()

        # Start polling queue for log/progress updates
        self.root.after(QUEUE_POLL_MS, self._process_queue)

    # ---------------- UI ----------------
    def _build_ui(self):
        # Top frame: controls
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=8)

        # Input format radios
        format_frame = tk.LabelFrame(top_frame, text="Input Format", padx=8, pady=6)
        format_frame.pack(side=tk.LEFT, padx=(0, 8))
        tk.Radiobutton(
            format_frame, text="Auto", variable=self.input_format, value="auto"
        ).pack(side=tk.LEFT)
        tk.Radiobutton(
            format_frame, text="NDPA (.ndpa)", variable=self.input_format, value="ndpa"
        ).pack(side=tk.LEFT, padx=6)
        tk.Radiobutton(
            format_frame, text="CSV (.csv)", variable=self.input_format, value="csv"
        ).pack(side=tk.LEFT)

        # File selection buttons
        btn_frame = tk.Frame(top_frame)
        btn_frame.pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(btn_frame, text="Select Files", command=self.select_files).pack(
            side=tk.LEFT
        )
        tk.Button(btn_frame, text="Select Folder", command=self.select_folder).pack(
            side=tk.LEFT, padx=6
        )
        tk.Button(btn_frame, text="Clear List", command=self.clear_files).pack(
            side=tk.LEFT
        )

        # Output folder selection
        out_folder_frame = tk.Frame(top_frame)
        out_folder_frame.pack(side=tk.RIGHT, fill=tk.X)
        tk.Button(
            out_folder_frame,
            text="Select Output Folder",
            command=self.select_output_folder,
        ).pack(side=tk.RIGHT)
        self.output_folder_label = tk.Label(
            out_folder_frame, text="(default: input file folder)", anchor="e"
        )
        self.output_folder_label.pack(side=tk.RIGHT, padx=(0, 10))

        # Middle: file list and log/progress
        middle_frame = tk.Frame(self.root)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        # Left: file list
        left = tk.Frame(middle_frame)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        tk.Label(left, text="Selected Files:").pack(anchor="w")
        self.file_listbox = tk.Listbox(left, height=18, selectmode=tk.EXTENDED)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        # scrollbar for listbox
        lb_scroll = tk.Scrollbar(
            self.file_listbox, orient=tk.VERTICAL, command=self.file_listbox.yview
        )
        self.file_listbox.config(yscrollcommand=lb_scroll.set)
        lb_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Right: log and progress
        right = tk.Frame(middle_frame, width=420)
        right.pack(side=tk.RIGHT, fill=tk.BOTH)

        tk.Label(right, text="Realtime Log:").pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(right, height=18, state=tk.NORMAL)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        prog_frame = tk.Frame(right)
        prog_frame.pack(fill=tk.X, pady=(8, 0))
        self.progress_label = tk.Label(prog_frame, text="Ready")
        self.progress_label.pack(anchor="w")
        self.progress_bar = ttk.Progressbar(prog_frame, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=(6, 0))

        # Bottom: convert button
        bottom = tk.Frame(self.root)
        bottom.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.convert_btn = tk.Button(
            bottom,
            text="Start Conversion",
            command=self.start_conversion,
            bg="#10b981",
            fg="white",
            font=("Segoe UI", 11, "bold"),
        )
        self.convert_btn.pack(fill=tk.X)

    # ---------------- file selection ----------------
    def get_file_filter(self):
        fmt = self.input_format.get()
        if fmt == "ndpa":
            return [("NDPA files", "*.ndpa"), ("All files", "*.*")]
        if fmt == "csv":
            return [("CSV files", "*.csv"), ("All files", "*.*")]
        return [("Supported files", "*.ndpa *.csv"), ("All files", "*.*")]

    def get_extensions(self):
        fmt = self.input_format.get()
        if fmt == "ndpa":
            return [".ndpa"]
        if fmt == "csv":
            return [".csv"]
        return [".ndpa", ".csv"]

    def select_files(self):
        ftypes = self.get_file_filter()
        selection = filedialog.askopenfilenames(title="Select files", filetypes=ftypes)
        if selection:
            added = 0
            for p in selection:
                if p not in self.input_files:
                    self.input_files.append(p)
                    added += 1
            self._refresh_file_list()
            self._enqueue_log(f"✓ Added {added} file(s)")

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select folder")
        if not folder:
            return
        exts = self.get_extensions()
        found = []
        for entry in os.listdir(folder):
            if any(entry.lower().endswith(ext) for ext in exts):
                found.append(os.path.join(folder, entry))
        if not found:
            messagebox.showwarning(
                "No files", "No {} files found in folder".format(", ".join(exts))
            )
            return
        added = 0
        for p in found:
            if p not in self.input_files:
                self.input_files.append(p)
                added += 1
        self._refresh_file_list()
        self._enqueue_log("✓ Added {} file(s) from folder".format(added))

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_folder.set(folder)
            self.output_folder_label.config(text=folder)
            self._enqueue_log("✓ Output folder set to: {}".format(folder))

    def clear_files(self):
        self.input_files.clear()
        self._refresh_file_list()
        self._enqueue_log("🗑️ Cleared file list")

    def _refresh_file_list(self):
        self.file_listbox.delete(0, tk.END)
        for p in self.input_files:
            self.file_listbox.insert(tk.END, os.path.basename(p))

    # ---------------- queue/log helpers ----------------
    def _enqueue_log(self, message: str):
        self.queue.put(("log", message))

    def _enqueue_progress(self, value: int):
        self.queue.put(("progress", value))

    def _enqueue_progress_text(self, text: str):
        self.queue.put(("progress_text", text))

    def _enqueue_done(self, successful: int, total: int):
        self.queue.put(("done", successful, total))

    def _enqueue_enable_button(self):
        # This kind of item instructs the main thread to enable UI elements
        self.queue.put(("enable_button",))

    def _process_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                if not item:
                    continue
                kind = item[0]
                if kind == "log":
                    _, message = item
                    self.log_text.insert(tk.END, message + "\n")
                    self.log_text.see(tk.END)
                elif kind == "progress":
                    _, val = item
                    try:
                        self.progress_bar["value"] = val
                    except Exception:
                        pass
                elif kind == "progress_text":
                    _, txt = item
                    try:
                        self.progress_label.config(text=txt)
                    except Exception:
                        pass
                elif kind == "done":
                    _, successful, total = item
                    messagebox.showinfo(
                        "Complete",
                        "Successfully converted {} out of {} files".format(
                            successful, total
                        ),
                    )
                elif kind == "enable_button":
                    try:
                        self.convert_btn.config(state=tk.NORMAL)
                    except Exception:
                        pass
        except queue.Empty:
            # no more items
            pass
        except Exception:
            # don't crash mainloop for queue errors
            pass
        finally:
            self.root.after(QUEUE_POLL_MS, self._process_queue)

    # ---------------- conversion control ----------------
    def start_conversion(self):
        if not self.input_files:
            messagebox.showwarning("No Files", "Please select files to convert")
            return
        # disable button
        self.convert_btn.config(state=tk.DISABLED)
        self.progress_bar["maximum"] = len(self.input_files)
        self.progress_bar["value"] = 0
        self.progress_label.config(text="Starting...")
        thread = threading.Thread(target=self._worker_convert_files, daemon=True)
        thread.start()

    def _worker_convert_files(self):
        total = len(self.input_files)
        successful = 0
        self._enqueue_log("\n" + "=" * 60)
        self._enqueue_log("🚀 Starting batch conversion...")
        self._enqueue_log("=" * 60)

        # iterate over a shallow copy so modifications to self.input_files won't break loop
        for idx, path in enumerate(list(self.input_files)):
            base = os.path.basename(path)
            self._enqueue_progress_text(
                "Converting {}/{}: {}".format(idx + 1, total, base)
            )
            self._enqueue_log("\n[{} / {}] Processing: {}".format(idx + 1, total, base))

            try:
                fmt = self.input_format.get()
                lower = path.lower()
                if fmt == "ndpa" or (fmt == "auto" and lower.endswith(".ndpa")):
                    ok = self.convert_ndpa_file(path)
                elif fmt == "csv" or (fmt == "auto" and lower.endswith(".csv")):
                    ok = self.convert_csv_file(path)
                else:
                    # unknown extension
                    self._enqueue_log("  ✗ Unknown file type — skipping")
                    ok = False
            except Exception as e:
                ok = False
                self._enqueue_log("  ✗ ERROR (exception): {}".format(e))

            if ok:
                successful += 1

            # update progress (main thread will apply it)
            self._enqueue_progress(idx + 1)

        # summary
        self._enqueue_log("\n" + "=" * 60)
        self._enqueue_log(
            "✓ Conversion complete: {}/{} files successful".format(successful, total)
        )
        self._enqueue_log("=" * 60)
        self._enqueue_done(successful, total)

        # re-enable button on main thread
        try:
            self.root.after(0, lambda: self.convert_btn.config(state=tk.NORMAL))
        except Exception:
            # fallback: instruct mainloop to enable button
            self._enqueue_enable_button()

    # ---------------- XML helpers and conversion implementations ----------------
    def _get_element_text(self, elem):
        """Safely return text from a minidom element or '0'."""
        if elem is None:
            return "0"
        fc = getattr(elem, "firstChild", None)
        if fc is None:
            return "0"
        data = getattr(fc, "data", None)
        if data is None:
            return "0"
        return str(data).strip()

    def convert_ndpa_file(self, input_path: str) -> bool:
        """
        Parse NDPA XML and write simplified LMD-compatible XML.
        - First 3 regions -> calibration points (from circle annotations).
        - Remaining regions -> shapes with points converted from nm -> um.
        """
        try:
            base = os.path.splitext(os.path.basename(input_path))[0]
            out_dir = self.output_folder.get() or os.path.dirname(input_path)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(
                out_dir, "{}_LMD{}".format(base, self.output_extension)
            )

            with open(input_path, "r", encoding="utf-8") as fh:
                dom = minidom.parse(fh)

            regions = dom.getElementsByTagName("ndpviewstate")
            self._enqueue_log("  Found {} regions".format(len(regions)))

            if len(regions) < 3:
                self._enqueue_log(
                    "  ✗ ERROR: Need at least 3 regions for calibration points!"
                )
                return False

            self._enqueue_log("  DEBUG: Processing calibration points from regions 0-2")

            with open(out_path, "w", encoding="utf-8") as out:
                out.write('<?xml version="1.0" encoding="utf-8"?>\n')
                out.write("<ImageData>\n")
                out.write("  <GlobalCoordinates>1</GlobalCoordinates>\n")

                # calibration points - extract from circle annotations
                for i in range(3):
                    region = regions[i]
                    # Get title for debugging
                    title_elem = region.getElementsByTagName("title")
                    title = (
                        self._get_element_text(title_elem[0])
                        if title_elem
                        else "Region_{}".format(i)
                    )

                    # Look for annotation element (circles for reference points)
                    annotations = region.getElementsByTagName("annotation")
                    if not annotations:
                        self._enqueue_log(
                            "  ⚠️ Calibration point {} ({}) has no annotation!".format(
                                i + 1, title
                            )
                        )
                        # write zeros if missing
                        out.write(
                            "  <X_CalibrationPoint_{}>0</X_CalibrationPoint_{}>\n".format(
                                i + 1, i + 1
                            )
                        )
                        out.write(
                            "  <Y_CalibrationPoint_{}>0</Y_CalibrationPoint_{}>\n".format(
                                i + 1, i + 1
                            )
                        )
                        continue

                    annotation = annotations[0]
                    # For circle annotations, x and y are direct children
                    x_elems = annotation.getElementsByTagName("x")
                    y_elems = annotation.getElementsByTagName("y")

                    if not x_elems or not y_elems:
                        self._enqueue_log(
                            "  ⚠️ Calibration point {} ({}) missing x/y coordinates!".format(
                                i + 1, title
                            )
                        )
                        x_um = 0
                        y_um = 0
                    else:
                        x_nm = float(self._get_element_text(x_elems[0]))
                        y_nm = float(self._get_element_text(y_elems[0]))
                        x_um = int(round(x_nm / 1000.0))
                        y_um = int(round(y_nm / 1000.0))

                    self._enqueue_log(
                        "  Calibration {} ({}): X={}, Y={} (from circle annotation)".format(
                            i + 1, title, x_um, y_um
                        )
                    )

                    out.write(
                        "  <X_CalibrationPoint_{}>{}</X_CalibrationPoint_{}>\n".format(
                            i + 1, x_um, i + 1
                        )
                    )
                    out.write(
                        "  <Y_CalibrationPoint_{}>{}</Y_CalibrationPoint_{}>\n".format(
                            i + 1, y_um, i + 1
                        )
                    )

                num_shapes = max(0, len(regions) - 3)
                out.write("  <ShapeCount>{}</ShapeCount>\n".format(num_shapes))
                self._enqueue_log(
                    "  DEBUG: Processing {} shapes from regions 3-{}".format(
                        num_shapes, len(regions) - 1
                    )
                )

                # shapes - these use pointlists
                for si in range(3, len(regions)):
                    region = regions[si]
                    shape_num = si - 2

                    title_elem = region.getElementsByTagName("title")
                    title = (
                        self._get_element_text(title_elem[0])
                        if title_elem
                        else "Shape_{}".format(shape_num)
                    )

                    # For freehand shapes, look for pointlist > point
                    pointlists = region.getElementsByTagName("pointlist")
                    if not pointlists:
                        self._enqueue_log(
                            "  ⚠️ Shape {} ({}) has no pointlist - skipping".format(
                                shape_num, title
                            )
                        )
                        continue

                    pts = pointlists[0].getElementsByTagName("point")
                    if not pts:
                        self._enqueue_log(
                            "  ⚠️ Shape {} ({}) has no points - skipping".format(
                                shape_num, title
                            )
                        )
                        continue

                    out.write("  <Shape_{}>\n".format(shape_num))
                    out.write("    <PointCount>{}</PointCount>\n".format(len(pts)))

                    # DEBUG: Log first point of each shape
                    if len(pts) > 0:
                        first_pt = pts[0]
                        x_elems = first_pt.getElementsByTagName("x")
                        y_elems = first_pt.getElementsByTagName("y")
                        first_x_nm = float(
                            self._get_element_text(x_elems[0] if x_elems else None)
                        )
                        first_y_nm = float(
                            self._get_element_text(y_elems[0] if y_elems else None)
                        )
                        first_x = int(round(first_x_nm / 1000.0))
                        first_y = int(round(first_y_nm / 1000.0))
                        self._enqueue_log(
                            "  Shape {} ({}) : {} points, first=({}, {})".format(
                                shape_num, title, len(pts), first_x, first_y
                            )
                        )

                    for pi, p in enumerate(pts):
                        x_elems = p.getElementsByTagName("x")
                        y_elems = p.getElementsByTagName("y")
                        x_nm = float(
                            self._get_element_text(x_elems[0] if x_elems else None)
                        )
                        y_nm = float(
                            self._get_element_text(y_elems[0] if y_elems else None)
                        )
                        x_um = int(round(x_nm / 1000.0))
                        y_um = int(round(y_nm / 1000.0))
                        out.write("    <X_{}>{}</X_{}>\n".format(pi + 1, x_um, pi + 1))
                        out.write("    <Y_{}>{}</Y_{}>\n".format(pi + 1, y_um, pi + 1))
                    out.write("  </Shape_{}>\n".format(shape_num))

                out.write("</ImageData>\n")

            self._enqueue_log("  ✓ Saved to: {}".format(os.path.basename(out_path)))
            self._enqueue_log(
                "  DEBUG: Conversion complete - check calibration point coordinates"
            )
            return True
        except Exception as e:
            import traceback

            self._enqueue_log("  ✗ ERROR when converting NDPA: {}".format(e))
            self._enqueue_log("  DEBUG: {}".format(traceback.format_exc()))
            return False

    def convert_csv_file(self, input_path: str) -> bool:
        """
        Read a CSV where first row is header and subsequent rows include X (col 5) and Y (col 6).
        Use first 3 data rows as calibration points (in micrometers already).
        Remaining rows create single-point shapes.
        """
        try:
            base = os.path.splitext(os.path.basename(input_path))[0]
            out_dir = self.output_folder.get() or os.path.dirname(input_path)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(
                out_dir, "{}_LMD{}".format(base, self.output_extension)
            )

            with open(input_path, newline="", encoding="utf-8") as fh:
                rdr = csv.reader(fh)
                rows = [r for r in rdr if r]

            self._enqueue_log("  Found {} rows in CSV".format(len(rows)))
            if len(rows) < 4:
                self._enqueue_log(
                    "  ✗ ERROR: Need at least 4 rows (header + 3 calibration points)"
                )
                return False

            data = rows[1:]  # skip header
            if len(data) < 3:
                self._enqueue_log(
                    "  ✗ ERROR: Need at least 3 data rows for calibration points"
                )
                return False

            with open(out_path, "w", encoding="utf-8") as out:
                out.write('<?xml version="1.0" encoding="utf-8"?>\n')
                out.write("<ImageData>\n")
                out.write("  <GlobalCoordinates>1</GlobalCoordinates>\n")

                # calibration from first 3 rows (columns 5/6 -> indices 5,6)
                for i in range(3):
                    row = data[i]
                    if len(row) >= 7:
                        try:
                            x_val = float(row[5])
                            y_val = float(row[6])
                        except Exception:
                            x_val = 0.0
                            y_val = 0.0
                    else:
                        x_val = 0.0
                        y_val = 0.0
                    out.write(
                        "  <X_CalibrationPoint_{}>{}</X_CalibrationPoint_{}>\n".format(
                            i + 1, int(round(x_val)), i + 1
                        )
                    )
                    out.write(
                        "  <Y_CalibrationPoint_{}>{}</Y_CalibrationPoint_{}>\n".format(
                            i + 1, int(round(y_val)), i + 1
                        )
                    )

                num_shapes = max(0, len(data) - 3)
                out.write("  <ShapeCount>{}</ShapeCount>\n".format(num_shapes))

                self._enqueue_log(
                    "  ⚠️ Note: CSV contains centroids only; polygons unavailable"
                )
                self._enqueue_log(
                    "  Creating single-point shapes for {} regions".format(num_shapes)
                )

                for si in range(3, len(data)):
                    row = data[si]
                    if len(row) >= 7:
                        try:
                            x_val = float(row[5])
                            y_val = float(row[6])
                        except Exception:
                            x_val = 0.0
                            y_val = 0.0
                    else:
                        x_val = 0.0
                        y_val = 0.0
                    out.write("  <Shape_{}>\n".format(si - 2))
                    out.write("    <PointCount>1</PointCount>\n")
                    out.write("    <X_1>{}</X_1>\n".format(int(round(x_val))))
                    out.write("    <Y_1>{}</Y_1>\n".format(int(round(y_val))))
                    out.write("  </Shape_{}>\n".format(si - 2))

                out.write("</ImageData>\n")

            self._enqueue_log("  ✓ Saved to: {}".format(os.path.basename(out_path)))
            self._enqueue_log(
                "  ⚠️ CSV export lacks polygon vertices - use NDPA format for full shape data"
            )
            return True
        except Exception as e:
            self._enqueue_log("  ✗ ERROR when converting CSV: {}".format(e))
            return False


if __name__ == "__main__":
    root = tk.Tk()
    app = MicroBridgeConverterApp(root)
    root.mainloop()

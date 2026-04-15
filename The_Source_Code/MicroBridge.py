#!/usr/bin/env python3
"""
MicroBridge.py

Thread-safe GUI for converting Hamamatsu NDP (.ndpa) and CSV annotations into a
simplified LMD-compatible XML. This file is a cleaned implementation that:

- Uses a background worker thread for conversions.
- Uses a queue.Queue for thread-safe log/progress messages.
- Safely extracts text from minidom elements (avoids AttributeError).
- Writes outputs to a selected output folder or the input file's folder.
- Fixes Many Bugs from the Original Code.
"""

import csv
import os
import queue
import sys
import threading
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, scrolledtext, ttk
from xml.dom import minidom
from xml.parsers.expat import ExpatError

# Configuration
WINDOW_TITLE = "MicroBridge - NDP/CSV to LMD Converter"
DEFAULT_OUTPUT_EXT = ".xml"
QUEUE_POLL_MS = 100


def convert_ndpa_to_lmd(
    input_filename, output_filename=None, allow_missing_calibration=False, log_fn=print
):
    """
    Convert NDP.view2 annotation file (.ndpa) to LMD-compatible XML format.

    Args:
        input_filename: Path to the .ndpa XML file
        output_filename: Optional output filename. If not provided, will use input name with '_LMD.xml'
        allow_missing_calibration: If False, conversion fails when calibration points are missing.
                                   If True, writes placeholder (0,0) coordinates with warning.

    Returns:
        True if successful, False otherwise
    """

    try:
        # Check if input file exists
        if not os.path.exists(input_filename):
            log_fn(f"ERROR: Input file not found: {input_filename}")
            return False

        # Generate output filename if not provided
        if output_filename is None:
            base_name = os.path.splitext(input_filename)[0]
            output_filename = f"{base_name}_LMD.xml"

        log_fn(f"Reading: {input_filename}")

        # Parse the NDP.view2 XML file
        with open(input_filename, "r", encoding="utf-8") as file:
            ndpa_xml = minidom.parse(file)

        # Get all ndpviewstate elements (regions)
        regions = ndpa_xml.getElementsByTagName("ndpviewstate")

        log_fn(f"Found {len(regions)} regions in the file")

        if len(regions) < 4:
            log_fn(
                f"WARNING: Found only {len(regions)} regions. Need at least 4 (3 calibration + 1 shape)"
            )
            if len(regions) < 3:
                log_fn("ERROR: Need at least 3 regions for calibration points!")
                return False
            log_fn("Proceeding with available regions...")

        log_fn("\nProcessing calibration points...")

        # First pass: validate and collect calibration points BEFORE writing any file
        calibration_points = []
        for cal_idx in range(min(3, len(regions))):
            region = regions[cal_idx]

            # Get region title for debugging
            title_elem = region.getElementsByTagName("title")
            title = (
                title_elem[0].firstChild.data  # type: ignore[attr-defined]
                if title_elem and title_elem[0].firstChild
                else "Unnamed"
            )

            # Try to get coordinates from annotation element first (circle annotations)
            # If not found, fall back to pointlist (freehand annotations)
            x_um = None
            y_um = None

            # Method 1: Check for annotation element (circle annotations)
            annotations = region.getElementsByTagName("annotation")
            if annotations:
                annotation = annotations[0]
                x_elems = annotation.getElementsByTagName("x")
                y_elems = annotation.getElementsByTagName("y")

                if x_elems and y_elems:
                    try:
                        x_nm = float(
                            x_elems[0].firstChild.data  # type: ignore[attr-defined]
                            if x_elems[0].firstChild
                            else 0
                        )
                        y_nm = float(
                            y_elems[0].firstChild.data  # type: ignore[attr-defined]
                            if y_elems[0].firstChild
                            else 0
                        )
                        x_um = int(round(x_nm / 1000))
                        y_um = int(round(y_nm / 1000))
                        log_fn(
                            f"  Calibration Point {cal_idx + 1} ('{title}'): X={x_um} µm, Y={y_um} µm (from circle annotation)"
                        )
                    except (ValueError, AttributeError):
                        pass

            # Method 2: Fallback to pointlist (freehand/polygon annotations)
            if x_um is None:
                pointlist = region.getElementsByTagName("point")
                if len(pointlist) > 0:
                    try:
                        first_point = pointlist[0]
                        x_elem = first_point.getElementsByTagName("x")[0]
                        y_elem = first_point.getElementsByTagName("y")[0]

                        x_nm = float(
                            x_elem.firstChild.data  # type: ignore[attr-defined]
                            if x_elem.firstChild and hasattr(x_elem.firstChild, "data")
                            else 0
                        )
                        y_nm = float(
                            y_elem.firstChild.data  # type: ignore[attr-defined]
                            if y_elem.firstChild and hasattr(y_elem.firstChild, "data")
                            else 0
                        )
                        x_um = int(round(x_nm / 1000))
                        y_um = int(round(y_nm / 1000))
                        log_fn(
                            f"  Calibration Point {cal_idx + 1} ('{title}'): X={x_um} µm, Y={y_um} µm (from pointlist)"
                        )
                    except (ValueError, AttributeError):
                        pass

            # If both methods failed, handle missing calibration point
            if x_um is None:
                log_fn(
                    f"  ERROR: Calibration region {cal_idx + 1} ('{title}') has no valid coordinates!"
                )
                if not allow_missing_calibration:
                    log_fn("\n✗ CONVERSION FAILED")
                    log_fn(
                        f"  Calibration point {cal_idx + 1} is missing valid coordinate data."
                    )
                    log_fn(
                        "  The LMD system requires accurate calibration points to function correctly."
                    )
                    log_fn("\n  To fix this issue:")
                    log_fn("    1. Open the file in NDP.view2")
                    log_fn("    2. Ensure the first 3 regions have valid annotations")
                    log_fn(
                        "    3. Use circle annotations for calibration points (recommended)"
                    )
                    log_fn(
                        "\n  To force conversion with placeholder (0,0) coordinates, use --force flag"
                    )
                    return False
                else:
                    # User explicitly allowed placeholder coordinates
                    x_um = 0
                    y_um = 0
                    log_fn(
                        "  WARNING: Using placeholder coordinates (0,0) - LMD system may malfunction!"
                    )
                    log_fn(
                        f"  Calibration Point {cal_idx + 1} ('{title}'): X={x_um} µm, Y={y_um} µm (placeholder)"
                    )

            calibration_points.append((x_um, y_um))

        # Collect valid shapes (regions with points)
        # Skip ruler/linear measure annotations - they are measurement tools, not capture regions
        valid_shapes = []
        shape_num = 0  # Track shape numbering independently
        for shape_idx in range(3, len(regions)):
            region = regions[shape_idx]

            # Get region title
            title_elem = region.getElementsByTagName("title")
            title = (
                title_elem[0].firstChild.data  # type: ignore[attr-defined]
                if title_elem and title_elem[0].firstChild
                else f"Shape_{shape_num + 1}"
            )

            # Skip ruler annotations (linearmeasure type)
            annotations = region.getElementsByTagName("annotation")
            if annotations:
                ann_type = annotations[0].getAttribute("type")
                if ann_type == "linearmeasure":
                    log_fn(f"  Skipping ruler annotation: '{title}'")
                    continue

            shape_num += 1

            # Get all points in this region
            pointlist = region.getElementsByTagName("point")
            num_points = len(pointlist)

            if num_points > 0:
                # Extract all point coordinates
                points = []
                for point in pointlist:
                    x_elem = point.getElementsByTagName("x")[0]
                    y_elem = point.getElementsByTagName("y")[0]

                    x_nm = float(
                        x_elem.firstChild.data  # type: ignore[attr-defined]
                        if x_elem.firstChild and hasattr(x_elem.firstChild, "data")
                        else 0
                    )
                    y_nm = float(
                        y_elem.firstChild.data  # type: ignore[attr-defined]
                        if y_elem.firstChild and hasattr(y_elem.firstChild, "data")
                        else 0
                    )
                    points.append((int(round(x_nm / 1000)), int(round(y_nm / 1000))))

                valid_shapes.append(
                    {
                        "shape_num": shape_num,
                        "title": title,
                        "points": points,
                        "num_points": num_points,
                    }
                )

        num_shapes = len(valid_shapes)
        log_fn(f"\nProcessing {num_shapes} capture shapes...")

        for shape_data in valid_shapes:
            log_fn(
                f"  Shape {shape_data['shape_num']} ('{shape_data['title']}'): {shape_data['num_points']} vertices"
            )

        # All validation passed - now write the output file
        with open(output_filename, "w", encoding="utf-8") as f1:
            # Write XML header
            f1.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f1.write("<ImageData>\n")
            f1.write("  <GlobalCoordinates>1</GlobalCoordinates>\n")

            # Write calibration points
            for cal_idx, (x_um, y_um) in enumerate(calibration_points):
                f1.write(
                    f"  <X_CalibrationPoint_{cal_idx + 1}>{x_um}</X_CalibrationPoint_{cal_idx + 1}>\n"
                )
                f1.write(
                    f"  <Y_CalibrationPoint_{cal_idx + 1}>{y_um}</Y_CalibrationPoint_{cal_idx + 1}>\n"
                )

            # Write ShapeCount
            f1.write(f"  <ShapeCount>{num_shapes}</ShapeCount>\n")

            # Write shapes
            for shape_data in valid_shapes:
                shape_num = shape_data["shape_num"]
                points = shape_data["points"]

                f1.write(f"  <Shape_{shape_num}>\n")
                f1.write(f"    <PointCount>{len(points)}</PointCount>\n")

                for point_idx, (x_um, y_um) in enumerate(points):
                    f1.write(f"    <X_{point_idx + 1}>{x_um}</X_{point_idx + 1}>\n")
                    f1.write(f"    <Y_{point_idx + 1}>{y_um}</Y_{point_idx + 1}>\n")

                f1.write(f"  </Shape_{shape_num}>\n")

            # Close XML
            f1.write("</ImageData>\n")

        log_fn("\n✓ Conversion complete!")
        log_fn(f"  Output saved to: {output_filename}")
        log_fn(f"  Total regions processed: {len(regions)}")
        log_fn("    - 3 calibration/reference points")
        log_fn(f"    - {num_shapes} capture shapes")

        return True

    except FileNotFoundError:
        log_fn("\n✗ ERROR: Input file not found")
        log_fn(f"  File: {input_filename}")
        log_fn("\n  The file may have been moved or deleted.")
        log_fn("  Please check the file path and try again.")
        return False
    except PermissionError:
        log_fn("\n✗ ERROR: Permission denied")
        log_fn(f"  File: {input_filename}")
        log_fn(
            "\n  You don't have permission to read this file or write to the output location."
        )
        log_fn(
            "  Try running with appropriate permissions or choose a different output folder."
        )
        return False
    except ExpatError as e:
        log_fn("\n✗ ERROR: Invalid XML format")
        log_fn(f"  File: {input_filename}")
        log_fn(f"  Details: {e}")
        log_fn("\n  This file may be corrupted or not a valid NDPA file.")
        log_fn("  Try opening it in NDP.view2 to verify it's valid.")
        return False
    except ValueError as e:
        log_fn("\n✗ ERROR: Invalid data in file")
        log_fn(f"  File: {input_filename}")
        log_fn(f"  Details: {e}")
        log_fn("\n  The file contains invalid coordinate or numeric data.")
        log_fn("  Please check the annotation data in NDP.view2.")
        return False
    except Exception as e:
        log_fn("\n✗ ERROR: Unexpected error during conversion")
        log_fn(f"  File: {input_filename}")
        log_fn(f"  Error: {e}")
        log_fn("\n  This is an unexpected error. If it persists:")
        log_fn("    1. Check that the file is a valid NDPA file")
        log_fn("    2. Try converting other files to see if the issue is file-specific")
        log_fn(
            "    3. Report this issue at: https://github.com/Snowman-scott/MicroBridge/issues"
        )

        # Only show traceback if debug mode
        if "--debug" in sys.argv:
            log_fn("\n  Debug traceback:")
            traceback.print_exc()
        else:
            log_fn("\n  (Use --debug flag to see detailed error information)")
        return False


def batch_convert_directory(
    directory=".", allow_missing_calibration=False, log_fn=print
):
    """
    Convert all .ndpa files in the specified directory.

    Args:
        directory: Path to directory containing .ndpa files (default is current directory)
        allow_missing_calibration: If False, skip files with missing calibration points

    Returns:
        Number of files successfully converted
    """
    # Find all .ndpa files
    ndpa_files = []
    for file in os.listdir(directory):
        if file.endswith(".ndpa"):
            ndpa_files.append(os.path.join(directory, file))

    if not ndpa_files:
        log_fn(f"No .ndpa files found in directory: {directory}")
        return 0

    log_fn("=" * 70)
    log_fn(f"Found {len(ndpa_files)} .ndpa file(s) to convert:")
    for file in ndpa_files:
        log_fn(f"  - {os.path.basename(file)}")
    log_fn("=" * 70)
    log_fn()

    # Convert each file
    successful = 0
    for ndpa_file in ndpa_files:
        try:
            if convert_ndpa_to_lmd(
                ndpa_file,
                allow_missing_calibration=allow_missing_calibration,
                log_fn=log_fn,
            ):
                successful += 1
            log_fn()
        except Exception as e:
            log_fn(f"✗ Unexpected error converting {os.path.basename(ndpa_file)}: {e}")
            log_fn()

    log_fn("=" * 70)
    log_fn(
        f"Batch conversion complete: {successful}/{len(ndpa_files)} files converted successfully"
    )
    log_fn("=" * 70)

    return successful


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class MicroBridgeConverterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(WINDOW_TITLE)
        try:
            self.root.iconbitmap(resource_path("MicroBridge_Icon.ico"))
        except Exception:
            # Fallback if icon loading fails
            pass
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # State
        self.input_files = []  # absolute paths
        self.input_format = tk.StringVar(value="auto")  # 'auto', 'ndpa', 'csv'
        self.output_extension = ".xml"
        self.output_folder = tk.StringVar(value="")  # empty => use input file folder

        # Thread-safe queue for log/progress updates
        self.queue = queue.Queue()

        # Worker thread management
        self.worker_thread = None
        self._stop_event = threading.Event()

        # Build UI
        self._build_ui()

        # Start polling queue for log/progress updates
        self.root.after(QUEUE_POLL_MS, self._process_queue)

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()

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

        # Non-intrusive attribution label:
        # Place the label using absolute placement so it does NOT affect the existing pack layout.
        # This keeps the UI exactly where it was while adding a subtle attribution.
        self.attribution_label = tk.Label(
            self.root,
            text="Made by Rose Scott - Snowman-scott on GitHub",
            font=("Segoe UI", 8),
            fg="#666666",
        )
        try:
            # place at bottom-right corner slightly above the bottom widgets so it doesn't clip the convert button
            self.attribution_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-48)
        except Exception:
            # If place() fails for any reason, fall back to packing on the bottom-right but keep it unobtrusive and above the button
            self.attribution_label.pack(
                side=tk.BOTTOM, anchor="e", padx=8, pady=(0, 12)
            )

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for common operations"""
        # Ctrl+O - Open files
        self.root.bind("<Control-o>", lambda e: self.select_files())
        self.root.bind("<Control-O>", lambda e: self.select_files())

        # Ctrl+Shift+O - Open folder
        self.root.bind("<Control-Shift-O>", lambda e: self.select_folder())
        self.root.bind("<Control-Shift-o>", lambda e: self.select_folder())

        # Ctrl+Q - Quit
        self.root.bind("<Control-q>", lambda e: self._on_closing())
        self.root.bind("<Control-Q>", lambda e: self._on_closing())

        # Enter - Start conversion (if files are selected)
        self.root.bind("<Return>", lambda e: self._handle_enter_key())

        # Delete - Remove selected files from list
        self.file_listbox.bind("<Delete>", lambda e: self._remove_selected_files())
        self.file_listbox.bind("<BackSpace>", lambda e: self._remove_selected_files())

        # Ctrl+A - Select all files in list
        self.file_listbox.bind("<Control-a>", lambda e: self._select_all_files())
        self.file_listbox.bind("<Control-A>", lambda e: self._select_all_files())

    def _handle_enter_key(self):
        """Handle Enter key - start conversion if files are selected"""
        if self.input_files and self.convert_btn["state"] != tk.DISABLED:
            self.start_conversion()

    def _remove_selected_files(self):
        """Remove selected files from the list"""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            return

        # Remove in reverse order to maintain correct indices
        for index in reversed(selected_indices):
            del self.input_files[index]

        self._refresh_file_list()
        self._enqueue_log(f"Removed {len(selected_indices)} file(s) from list")

    def _select_all_files(self):
        """Select all files in the listbox"""
        self.file_listbox.select_set(0, tk.END)
        return "break"  # Prevent default behavior

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

        # Pre-flight validation
        validation_errors = []

        # Check 1: Verify all files still exist
        missing_files = []
        for filepath in self.input_files:
            if not os.path.exists(filepath):
                missing_files.append(os.path.basename(filepath))

        if missing_files:
            validation_errors.append(
                "Missing files ({}):\n  • {}".format(
                    len(missing_files), "\n  • ".join(missing_files[:5])
                )
            )
            if len(missing_files) > 5:
                validation_errors[-1] += f"\n  • ... and {len(missing_files) - 5} more"

        # Check 2: Verify output folder is writable
        out_dir = self.output_folder.get()
        if not out_dir and self.input_files:
            # Use first input file's directory
            out_dir = os.path.dirname(self.input_files[0])

        if out_dir and not os.access(out_dir, os.W_OK):
            validation_errors.append(
                "Output folder is not writable:\n  {}".format(out_dir)
            )

        # Check 3: Verify files are readable and appear to be valid format
        unreadable_files = []
        invalid_format_files = []

        for filepath in self.input_files:
            if not os.path.exists(filepath):
                continue  # Already caught in missing files check

            if not os.access(filepath, os.R_OK):
                unreadable_files.append(os.path.basename(filepath))
                continue

            # Quick format validation
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    first_chars = f.read(100)
                    lower_path = filepath.lower()

                    # Check if format matches extension
                    if lower_path.endswith(
                        ".ndpa"
                    ) and not first_chars.strip().startswith("<?xml"):
                        invalid_format_files.append(
                            "{} (not XML)".format(os.path.basename(filepath))
                        )
                    elif lower_path.endswith(".csv") and "<?xml" in first_chars:
                        invalid_format_files.append(
                            "{} (appears to be XML, not CSV)".format(
                                os.path.basename(filepath)
                            )
                        )
            except Exception as e:
                unreadable_files.append(
                    "{} ({})".format(os.path.basename(filepath), str(e))
                )

        if unreadable_files:
            validation_errors.append(
                "Cannot read files ({}):\n  • {}".format(
                    len(unreadable_files), "\n  • ".join(unreadable_files[:5])
                )
            )

        if invalid_format_files:
            validation_errors.append(
                "Invalid file format ({}):\n  • {}".format(
                    len(invalid_format_files), "\n  • ".join(invalid_format_files[:5])
                )
            )

        # Display validation errors if any
        if validation_errors:
            error_msg = "Pre-flight validation failed:\n\n" + "\n\n".join(
                validation_errors
            )
            error_msg += "\n\nPlease fix these issues before starting conversion."
            messagebox.showerror("Validation Failed", error_msg)
            return

        # All checks passed - proceed with conversion
        # disable button
        self.convert_btn.config(state=tk.DISABLED)
        self.progress_bar["maximum"] = len(self.input_files)
        self.progress_bar["value"] = 0
        self.progress_label.config(text="Starting...")

        # Clear stop event and start non-daemon worker thread
        self._stop_event.clear()
        self.worker_thread = threading.Thread(
            target=self._worker_convert_files, daemon=False
        )
        self.worker_thread.start()

    def _worker_convert_files(self):
        total = len(self.input_files)
        successful = 0
        self._enqueue_log("\n" + "=" * 60)
        self._enqueue_log("🚀 Starting batch conversion...")
        self._enqueue_log("=" * 60)

        # iterate over a shallow copy so modifications to self.input_files won't break loop
        for idx, path in enumerate(list(self.input_files)):
            # Check if stop was requested
            if self._stop_event.is_set():
                self._enqueue_log("\n⚠️ Conversion cancelled by user")
                break

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
        if self._stop_event.is_set():
            self._enqueue_log(
                "⚠️ Conversion stopped: {}/{} files converted before cancellation".format(
                    successful, total
                )
            )
        else:
            self._enqueue_log(
                "✓ Conversion complete: {}/{} files successful".format(
                    successful, total
                )
            )
            self._enqueue_done(successful, total)
        self._enqueue_log("=" * 60)

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
        out_dir = self.output_folder.get() or os.path.dirname(input_path)
        base = os.path.splitext(os.path.basename(input_path))[0]
        output_filename = os.path.join(out_dir, f"{base}_LMD.xml")
        os.makedirs(out_dir, exist_ok=True)
        return convert_ndpa_to_lmd(
            input_path, output_filename=output_filename, log_fn=self._enqueue_log
        )

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
        except FileNotFoundError:
            self._enqueue_log("  ✗ ERROR: Input file not found")
            self._enqueue_log("  The file may have been moved or deleted.")
            return False
        except PermissionError:
            self._enqueue_log("  ✗ ERROR: Permission denied")
            self._enqueue_log(
                "  You don't have permission to read this file or write to the output location."
            )
            return False
        except UnicodeDecodeError as e:
            self._enqueue_log("  ✗ ERROR: Cannot read file - encoding issue")
            self._enqueue_log("  Details: {}".format(e))
            self._enqueue_log(
                "  The file may not be a valid CSV or may use an unsupported encoding."
            )
            return False
        except Exception as e:
            import traceback

            self._enqueue_log("  ✗ ERROR: Unexpected error converting CSV")
            self._enqueue_log("  Error: {}".format(e))
            self._enqueue_log("  Please verify the CSV file format is correct.")
            self._enqueue_log("\n  Debug information:")
            self._enqueue_log("  {}".format(traceback.format_exc()))
            return False

    def _on_closing(self):
        """Handle window close event - warn if conversion is running"""
        if self.worker_thread and self.worker_thread.is_alive():
            # Conversion is running - ask user to confirm
            response = messagebox.askyesno(
                "Conversion in Progress",
                "A file conversion is currently running. Closing now may leave incomplete files.\n\n"
                "Do you want to stop the conversion and exit?",
                icon="warning",
            )
            if response:
                # User confirmed - signal worker to stop
                self._stop_event.set()
                self._enqueue_log(
                    "\n⚠️ Shutdown requested - waiting for current file to finish..."
                )
                self.progress_label.config(text="Stopping...")

                # Wait for worker thread to finish (with timeout)
                self.worker_thread.join(timeout=10.0)

                if self.worker_thread.is_alive():
                    # Thread didn't finish in time - warn user
                    messagebox.showwarning(
                        "Force Close",
                        "Worker thread did not stop in time. Some files may be incomplete.",
                    )

                # Close the window
                self.root.destroy()
            # else: user cancelled - do nothing, keep window open
        else:
            # No conversion running - safe to close
            self.root.destroy()


if __name__ == "__main__":
    # Check for CLI flags
    is_cli = "--cli" in sys.argv
    allow_missing = "--force" in sys.argv

    # Get all arguments that aren't flags
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if is_cli or args:  # If --cli is used OR files are dragged onto the EXE
        # CLI Mode
        if not args:
            print("MicroBridge CLI Mode")
            print("Usage: MicroBridge --cli [--force] <file1.ndpa> <file2.ndpa> ...")
            sys.exit(1)

        if allow_missing:
            print(
                "⚠️ --force flag detected: Using (0,0) for missing calibration points.\n"
            )

        print(f"Processing {len(args)} file(s)...\n")
        successful = 0
        for filename in args:
            if convert_ndpa_to_lmd(filename, allow_missing_calibration=allow_missing):
                successful += 1
            print()  # Spacer
        print(f"Finished: {successful}/{len(args)} files converted successfully.")
        sys.exit(0 if successful == len(args) else 1)
    else:
        # GUI Mode (Default)
        root = tk.Tk()
        app = MicroBridgeConverterApp(root)
        root.mainloop()

import os
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from xml.dom import minidom
import threading
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

class MicroBridgeConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("MicroBridge")
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{int(sw*0.7)}x{int(sh*0.8)}")
        self.root.resizable(True, True)
        self.root.minsize(800, 600)
        
        # Modern color scheme - Vibrant & Clean
        self.colors = {
            'bg': '#f0f2f5',           # Lighter, cooler gray for background
            'header': '#1a1a1a',       # Almost black for high contrast header
            'primary': '#0066ff',      # Vibrant modern blue
            'primary_hover': '#0052cc',
            'success': '#00b894',      # Minty green
            'success_hover': '#00a383',
            'danger': '#ff7675',       # Soft red
            'danger_hover': '#d63031',
            'warning': '#fdcb6e',      # Warm yellow
            'warning_hover': '#e17055',
            'card': '#ffffff',
            'text': '#2d3436',         # Dark gray, softer than black
            'text_light': '#636e72',   # Medium gray
            'border': '#dfe6e9'        # Subtle border color
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Variables
        self.input_files = []
        self.output_extension = tk.StringVar(value=".xml")
        self.input_format = tk.StringVar(value="auto")  # auto, ndpa, csv
        
        # Configure modern scrollbar style
        self.configure_scrollbar_style()
        
        # Create modern GUI
        self.create_widgets()
        
    def create_widgets(self):
        # Header
        header_frame = tk.Frame(self.root, bg=self.colors['header'], height=100)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="MicroBridge",
            font=("Segoe UI", 32, "bold"),
            bg=self.colors['header'],
            fg="white"
        )
        title_label.pack(pady=(25, 5))
        
        subtitle_label = tk.Label(
            header_frame,
            text="Convert Hamamatsu NDP annotations to LMD-compatible annotation files",
            font=("Segoe UI", 11),
            bg=self.colors['header'],
            fg="#b2bec3"
        )
        subtitle_label.pack(pady=(0, 25))
        
        content_frame = tk.Frame(self.root, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        self.main_canvas = tk.Canvas(content_frame, bg=self.colors['bg'], highlightthickness=0)
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=self.main_canvas.yview, style="Custom.Vertical.TScrollbar")
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.main_canvas.configure(yscrollcommand=v_scroll.set)
        self.scrollable_frame = tk.Frame(self.main_canvas, bg=self.colors['bg'])
        self._canvas_window = self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))
        self.main_canvas.bind("<Configure>", lambda e: self.main_canvas.itemconfig(self._canvas_window, width=e.width))
        self.main_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        main_container = self.scrollable_frame
        
        # Info card
        info_card = tk.Frame(main_container, bg=self.colors['card'], relief=tk.FLAT, bd=0)
        info_card.pack(fill=tk.X, pady=(0, 25), padx=2) # Add horizontal padding for shadow effect simulation
        
        # Add a subtle border effect
        info_card_border = tk.Frame(info_card, bg=self.colors['border'], padx=1, pady=1)
        info_card_border.pack(fill=tk.BOTH, expand=True)
        
        info_inner = tk.Frame(info_card_border, bg=self.colors['card'])
        info_inner.pack(fill=tk.BOTH, padx=25, pady=20)
        
        info_title = tk.Label(
            info_inner,
            text="ℹ️  Important Information",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['card'],
            fg=self.colors['text'],
            anchor='w'
        )
        info_title.pack(fill=tk.X, pady=(0, 10))
        
        info_points = [
            "First 3 regions in your file will be used as calibration/reference points",
            "All remaining regions will be converted to capture shapes",
            "Make sure your reference points are easily identifiable on the LMD microscope"
        ]
        
        for point in info_points:
            point_frame = tk.Frame(info_inner, bg=self.colors['card'])
            point_frame.pack(fill=tk.X, pady=2)
            
            bullet = tk.Label(
                point_frame,
                text="•",
                font=("Segoe UI", 10),
                bg=self.colors['card'],
                fg=self.colors['primary']
            )
            bullet.pack(side=tk.LEFT, padx=(0, 8))
            
            point_label = tk.Label(
                point_frame,
                text=point,
                font=("Segoe UI", 9),
                bg=self.colors['card'],
                fg=self.colors['text_light'],
                anchor='w'
            )
            point_label.pack(side=tk.LEFT, fill=tk.X)
        
        # Input Options Card
        input_card = tk.Frame(main_container, bg=self.colors['card'], relief=tk.FLAT)
        input_card.pack(fill=tk.X, pady=(0, 25), padx=2)
        
        input_card_border = tk.Frame(input_card, bg=self.colors['border'], padx=1, pady=1)
        input_card_border.pack(fill=tk.BOTH, expand=True)
        
        input_inner = tk.Frame(input_card_border, bg=self.colors['card'])
        input_inner.pack(fill=tk.BOTH, padx=25, pady=20)
        
        input_title = tk.Label(
            input_inner,
            text="📥  Input Options",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['card'],
            fg=self.colors['text'],
            anchor='w'
        )
        input_title.pack(fill=tk.X, pady=(0, 10))
        
        format_label = tk.Label(
            input_inner,
            text="Input file format:",
            font=("Segoe UI", 9),
            bg=self.colors['card'],
            fg=self.colors['text_light']
        )
        format_label.pack(anchor='w', pady=(0, 8))
        
        radio_frame = tk.Frame(input_inner, bg=self.colors['card'])
        radio_frame.pack(fill=tk.X)
        
        formats = [
            ("Auto-detect", "auto"),
            ("NDPA (.ndpa)", "ndpa"),
            ("CSV (.csv)", "csv")
        ]
        
        for text, value in formats:
            rb = tk.Radiobutton(
                radio_frame,
                text=text,
                variable=self.input_format,
                value=value,
                font=("Segoe UI", 9),
                bg=self.colors['card'],
                fg=self.colors['text'],
                selectcolor=self.colors['card'],
                activebackground=self.colors['card']
            )
            rb.pack(side=tk.LEFT, padx=(0, 20))
        
        # File Selection Card
        file_card = tk.Frame(main_container, bg=self.colors['card'], relief=tk.FLAT)
        file_card.pack(fill=tk.BOTH, expand=True, pady=(0, 25), padx=2)
        
        file_card_border = tk.Frame(file_card, bg=self.colors['border'], padx=1, pady=1)
        file_card_border.pack(fill=tk.BOTH, expand=True)
        
        file_inner = tk.Frame(file_card_border, bg=self.colors['card'])
        file_inner.pack(fill=tk.BOTH, padx=25, pady=20)
        
        file_title = tk.Label(
            file_inner,
            text="📁  File Selection",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['card'],
            fg=self.colors['text'],
            anchor='w'
        )
        file_title.pack(fill=tk.X, pady=(0, 15))
        
        # Button container
        btn_container = tk.Frame(file_inner, bg=self.colors['card'])
        btn_container.pack(fill=tk.X, pady=(0, 15))
        
        self.select_files_btn = self.create_modern_button(
            btn_container,
            "📄 Select Files",
            self.select_files,
            self.colors['primary']
        )
        self.select_files_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.select_folder_btn = self.create_modern_button(
            btn_container,
            "📂 Select Folder",
            self.select_folder,
            self.colors['warning']
        )
        self.select_folder_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = self.create_modern_button(
            btn_container,
            "🗑️ Clear",
            self.clear_files,
            self.colors['danger']
        )
        self.clear_btn.pack(side=tk.LEFT)
        
        # File list
        list_label = tk.Label(
            file_inner,
            text="Selected files:",
            font=("Segoe UI", 9),
            bg=self.colors['card'],
            fg=self.colors['text_light']
        )
        list_label.pack(anchor='w', pady=(0, 8))
        
        # Modern listbox with custom styling
        list_frame = tk.Frame(file_inner, bg=self.colors['card'])
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, style="Custom.Vertical.TScrollbar")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(
            list_frame,
            font=("Consolas", 9),
            bg='#fafbfc',
            fg=self.colors['text'],
            selectbackground=self.colors['primary'],
            selectforeground='white',
            relief=tk.FLAT,
            bd=1,
            highlightthickness=1,
            highlightbackground='#e1e4e8',
            yscrollcommand=scrollbar.set
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Output Options Card
        output_card = tk.Frame(main_container, bg=self.colors['card'], relief=tk.FLAT)
        output_card.pack(fill=tk.X, pady=(0, 25), padx=2)
        
        output_card_border = tk.Frame(output_card, bg=self.colors['border'], padx=1, pady=1)
        output_card_border.pack(fill=tk.BOTH, expand=True)
        
        output_inner = tk.Frame(output_card_border, bg=self.colors['card'])
        output_inner.pack(fill=tk.BOTH, padx=25, pady=20)
        
        output_title = tk.Label(
            output_inner,
            text="📤  Output Options",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['card'],
            fg=self.colors['text'],
            anchor='w'
        )
        output_title.pack(fill=tk.X, pady=(0, 10))
        
        output_label = tk.Label(
            output_inner,
            text="Output file extension:",
            font=("Segoe UI", 9),
            bg=self.colors['card'],
            fg=self.colors['text_light']
        )
        output_label.pack(anchor='w', pady=(0, 8))
        
        output_radio_frame = tk.Frame(output_inner, bg=self.colors['card'])
        output_radio_frame.pack(fill=tk.X)
        
        for text, value in [(".xml", ".xml"), (".sld", ".sld")]:
            rb = tk.Radiobutton(
                output_radio_frame,
                text=text,
                variable=self.output_extension,
                value=value,
                font=("Segoe UI", 9),
                bg=self.colors['card'],
                fg=self.colors['text'],
                selectcolor=self.colors['card'],
                activebackground=self.colors['card']
            )
            rb.pack(side=tk.LEFT, padx=(0, 20))
        
        # Progress bar
        progress_frame = tk.Frame(main_container, bg=self.colors['bg'])
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#e1e4e8',
            background=self.colors['success'],
            bordercolor=self.colors['bg'],
            lightcolor=self.colors['success'],
            darkcolor=self.colors['success']
        )
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            style="Custom.Horizontal.TProgressbar",
            mode='determinate',
            length=300
        )
        self.progress_bar.pack(fill=tk.X)
        
        # Convert button
        convert_btn_frame = tk.Frame(main_container, bg=self.colors['bg'])
        convert_btn_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.convert_btn = tk.Button(
            convert_btn_frame,
            text="⚡ Convert Files",
            command=self.start_conversion,
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['success'],
            fg="white",
            relief=tk.FLAT,
            padx=40,
            pady=15,
            cursor="hand2",
            activebackground="#229954",
            activeforeground="white"
        )
        self.convert_btn.pack()
        
        # Log Card
        log_card = tk.Frame(main_container, bg=self.colors['card'], relief=tk.FLAT)
        log_card.pack(fill=tk.BOTH, expand=True, padx=2)
        
        log_card_border = tk.Frame(log_card, bg=self.colors['border'], padx=1, pady=1)
        log_card_border.pack(fill=tk.BOTH, expand=True)
        
        log_inner = tk.Frame(log_card_border, bg=self.colors['card'])
        log_inner.pack(fill=tk.BOTH, padx=25, pady=20)
        
        log_title = tk.Label(
            log_inner,
            text="📋  Conversion Log",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['card'],
            fg=self.colors['text'],
            anchor='w'
        )
        log_title.pack(fill=tk.X, pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(
            log_inner,
            height=8,
            font=("Consolas", 9),
            bg='#fafbfc',
            fg=self.colors['text'],
            relief=tk.FLAT,
            bd=1,
            highlightthickness=1,
            highlightbackground='#e1e4e8',
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def configure_scrollbar_style(self):
        """Configure modern scrollbar styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom vertical scrollbar
        style.configure(
            "Custom.Vertical.TScrollbar",
            background=self.colors['bg'],
            troughcolor='#e1e4e8',
            bordercolor=self.colors['bg'],
            arrowcolor=self.colors['text_light'],
            relief=tk.FLAT
        )
        
        # Scrollbar hover effects
        style.map(
            "Custom.Vertical.TScrollbar",
            background=[
                ('pressed', self.colors['primary']),
                ('active', self.colors['secondary'])
            ]
        )

    def _on_mousewheel(self, event):
        if hasattr(self, 'main_canvas'):
            self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def create_modern_button(self, parent, text, command, bg_color):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 9, "bold"),
            bg=bg_color,
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground=self.colors.get(f'{bg_color}_hover', self.adjust_color_brightness(bg_color, 0.8)),
            activeforeground="white"
        )
        btn.bind("<Enter>", lambda e: btn.configure(bg=self.adjust_color_brightness(bg_color, 0.9)))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg_color))
        return btn
    
    def adjust_color_brightness(self, hex_color, factor):
        """Darken a hex color by a factor"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(int(c * factor) for c in rgb)
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
    
    def select_files(self):
        format_filter = self.get_file_filter()
        files = filedialog.askopenfilenames(
            title="Select files",
            filetypes=format_filter
        )
        if files:
            for file in files:
                if file not in self.input_files:
                    self.input_files.append(file)
                    self.file_listbox.insert(tk.END, os.path.basename(file))
            self.log(f"✓ Added {len(files)} file(s)")
    
    def select_folder(self):
        folder = filedialog.askdirectory(title="Select folder")
        if folder:
            extensions = self.get_extensions()
            found_files = [f for f in os.listdir(folder) 
                          if any(f.endswith(ext) for ext in extensions)]
            
            if not found_files:
                messagebox.showwarning("No Files", f"No {', '.join(extensions)} files found in selected folder")
                return
            
            count = 0
            for file in found_files:
                full_path = os.path.join(folder, file)
                if full_path not in self.input_files:
                    self.input_files.append(full_path)
                    self.file_listbox.insert(tk.END, file)
                    count += 1
            self.log(f"✓ Added {count} file(s) from folder")
    
    def get_file_filter(self):
        format_type = self.input_format.get()
        if format_type == "ndpa":
            return [("NDPA files", "*.ndpa"), ("All files", "*.*")]
        elif format_type == "csv":
            return [("CSV files", "*.csv"), ("All files", "*.*")]
        else:  # auto
            return [("Supported files", "*.ndpa *.csv"), ("All files", "*.*")]
    
    def get_extensions(self):
        format_type = self.input_format.get()
        if format_type == "ndpa":
            return [".ndpa"]
        elif format_type == "csv":
            return [".csv"]
        else:  # auto
            return [".ndpa", ".csv"]
    
    def clear_files(self):
        self.input_files.clear()
        self.file_listbox.delete(0, tk.END)
        self.log("🗑️ Cleared file list")
    
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_conversion(self):
        if not self.input_files:
            messagebox.showwarning("No Files", "Please select files to convert")
            return
        
        self.convert_btn.config(state=tk.DISABLED)
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = len(self.input_files)
        
        thread = threading.Thread(target=self.convert_files, daemon=True)
        thread.start()
    
    def convert_files(self):
        self.log("\n" + "="*70)
        self.log("🚀 Starting batch conversion...")
        self.log("="*70)
        
        successful = 0
        for idx, input_file in enumerate(self.input_files):
            self.log(f"\n[{idx+1}/{len(self.input_files)}] Processing: {os.path.basename(input_file)}")
            
            # Detect file type
            if input_file.endswith('.ndpa'):
                success = self.convert_ndpa_file(input_file)
            elif input_file.endswith('.csv'):
                success = self.convert_csv_file(input_file)
            else:
                self.log(f"  ✗ Unknown file type")
                success = False
            
            if success:
                successful += 1
            
            self.progress_bar['value'] = idx + 1
            self.root.update_idletasks()
        
        self.log("\n" + "="*70)
        self.log(f"✓ Conversion complete: {successful}/{len(self.input_files)} files successful")
        self.log("="*70)
        
        self.convert_btn.config(state=tk.NORMAL)
        
        messagebox.showinfo(
            "Conversion Complete",
            f"Successfully converted {successful} out of {len(self.input_files)} files"
        )
    
    def convert_ndpa_file(self, input_filename):
        try:
            base_name = os.path.splitext(input_filename)[0]
            output_filename = f"{base_name}_LMD{self.output_extension.get()}"
            
            with open(input_filename, 'r', encoding='utf-8') as file:
                ndpa_xml = minidom.parse(file)
            
            regions = ndpa_xml.getElementsByTagName('ndpviewstate')
            self.log(f"  Found {len(regions)} regions")
            
            if len(regions) < 3:
                self.log(f"  ✗ ERROR: Need at least 3 regions for calibration points!")
                return False
            
            with open(output_filename, 'w', encoding='utf-8') as f1:
                f1.write('<?xml version="1.0" encoding="utf-8"?>\n')
                f1.write("<ImageData>\n")
                f1.write("  <GlobalCoordinates>1</GlobalCoordinates>\n")
                
                # Calibration points
                for cal_idx in range(3):
                    region = regions[cal_idx]
                    pointlist = region.getElementsByTagName('point')
                    
                    if len(pointlist) == 0:
                        continue
                    
                    first_point = pointlist[0]
                    x_elem = first_point.getElementsByTagName('x')[0]
                    y_elem = first_point.getElementsByTagName('y')[0]
                    
                    x_nm = float(x_elem.firstChild.data)
                    y_nm = float(y_elem.firstChild.data)
                    x_um = int(round(x_nm / 1000))
                    y_um = int(round(y_nm / 1000))
                    
                    f1.write(f"  <X_CalibrationPoint_{cal_idx + 1}>{x_um}</X_CalibrationPoint_{cal_idx + 1}>\n")
                    f1.write(f"  <Y_CalibrationPoint_{cal_idx + 1}>{y_um}</Y_CalibrationPoint_{cal_idx + 1}>\n")
                
                num_shapes = len(regions) - 3
                f1.write(f"  <ShapeCount>{num_shapes}</ShapeCount>\n")
                
                # Shapes
                for shape_idx in range(3, len(regions)):
                    region = regions[shape_idx]
                    shape_num = shape_idx - 2
                    
                    pointlist = region.getElementsByTagName('point')
                    num_points = len(pointlist)
                    
                    if num_points == 0:
                        continue
                    
                    f1.write(f"  <Shape_{shape_num}>\n")
                    f1.write(f"    <PointCount>{num_points}</PointCount>\n")
                    
                    for point_idx, point in enumerate(pointlist):
                        x_elem = point.getElementsByTagName('x')[0]
                        y_elem = point.getElementsByTagName('y')[0]
                        
                        x_nm = float(x_elem.firstChild.data)
                        y_nm = float(y_elem.firstChild.data)
                        x_um = int(round(x_nm / 1000))
                        y_um = int(round(y_nm / 1000))
                        
                        f1.write(f"    <X_{point_idx + 1}>{x_um}</X_{point_idx + 1}>\n")
                        f1.write(f"    <Y_{point_idx + 1}>{y_um}</Y_{point_idx + 1}>\n")
                    
                    f1.write(f"  </Shape_{shape_num}>\n")
                
                f1.write("</ImageData>\n")
            
            self.log(f"  ✓ Saved to: {os.path.basename(output_filename)}")
            return True
            
        except Exception as e:
            self.log(f"  ✗ ERROR: {str(e)}")
            return False
    
    def convert_csv_file(self, input_filename):
        try:
            base_name = os.path.splitext(input_filename)[0]
            output_filename = f"{base_name}_LMD{self.output_extension.get()}"
            
            # Read CSV file
            with open(input_filename, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                data = list(csv_reader)
            
            # Remove empty rows
            data = [row for row in data if row]
            
            self.log(f"  Found {len(data)} rows in CSV")
            
            if len(data) < 4:
                self.log(f"  ✗ ERROR: Need at least 4 rows (header + 3 calibration points)")
                return False
            
            # Assuming first row is header, skip it
            data = data[1:]
            
            if len(data) < 3:
                self.log(f"  ✗ ERROR: Need at least 3 data rows for calibration points")
                return False
            
            with open(output_filename, 'w', encoding='utf-8') as f1:
                f1.write('<?xml version="1.0" encoding="utf-8"?>\n')
                f1.write("<ImageData>\n")
                f1.write("  <GlobalCoordinates>1</GlobalCoordinates>\n")
                
                # Use first 3 rows as calibration points
                # Assuming columns: Index, Type, Name, Details, Color, X, Y, Length, Area
                for cal_idx in range(3):
                    if len(data[cal_idx]) >= 7:
                        x_val = float(data[cal_idx][5])  # Column 5 is X
                        y_val = float(data[cal_idx][6])  # Column 6 is Y
                        
                        # Already in micrometers from CSV
                        x_um = int(round(x_val))
                        y_um = int(round(y_val))
                        
                        f1.write(f"  <X_CalibrationPoint_{cal_idx + 1}>{x_um}</X_CalibrationPoint_{cal_idx + 1}>\n")
                        f1.write(f"  <Y_CalibrationPoint_{cal_idx + 1}>{y_um}</Y_CalibrationPoint_{cal_idx + 1}>\n")
                
                num_shapes = len(data) - 3
                f1.write(f"  <ShapeCount>{num_shapes}</ShapeCount>\n")
                
                self.log(f"  ⚠️ Note: CSV format contains centroids only, not full polygon data")
                self.log(f"  Creating single-point shapes for {num_shapes} regions")
                
                # Create single-point shapes for remaining rows
                for shape_idx in range(3, len(data)):
                    shape_num = shape_idx - 2
                    
                    if len(data[shape_idx]) >= 7:
                        x_val = float(data[shape_idx][5])
                        y_val = float(data[shape_idx][6])
                        
                        x_um = int(round(x_val))
                        y_um = int(round(y_val))
                        
                        f1.write(f"  <Shape_{shape_num}>\n")
                        f1.write(f"    <PointCount>1</PointCount>\n")
                        f1.write(f"    <X_1>{x_um}</X_1>\n")
                        f1.write(f"    <Y_1>{y_um}</Y_1>\n")
                        f1.write(f"  </Shape_{shape_num}>\n")
                
                f1.write("</ImageData>\n")
            
            self.log(f"  ✓ Saved to: {os.path.basename(output_filename)}")
            self.log(f"  ⚠️ CSV export lacks polygon vertices - use NDPA format for full shape data")
            return True
            
        except Exception as e:
            self.log(f"  ✗ ERROR: {str(e)}")
            return False

if __name__ == "__main__":
    root = tk.Tk()
    app = MicroBridgeConverter(root)
    root.mainloop()

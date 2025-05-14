import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import subprocess
import platform
import pyautogui
import shutil
from PIL import Image, ImageTk
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as reportlab_canvas
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Image as ReportLabImage
from constants import *

try:
    import win32api
    import win32print
except ImportError:
    win32api = None
    win32print = None

class ShelfTab:
    def __init__(self, tab, controller, view):
        self.tab = tab
        self.controller = controller
        self.view = view
        # Get sections and shelf structure from the model
        self.sections = self.controller.model.get_sections()
        self.shelf_structure = self.controller.model.get_shelf_structure()
        # Aisles and sides will be set dynamically based on the selected section
        self.aisles = []
        self.sides = []
        self.families = self.controller.get_families()
        
        # Variables for shelf sizing
        self.initial_cell_width = None
        self.initial_cell_height = None
        self.initial_aspect_ratio = None
        self.scale_factor = 1.0
        
        # Dictionary to store front face item IDs for each shelf
        self.front_face_ids = {}
        self.cell_coords = {}
        
        # Dropdown variables
        self.section_var = None
        self.aisle_var = None
        self.side_var = None
        self.family_var = None
        self.category_var = None
        
        # Dropdown widgets
        self.aisle_dropdown = None
        self.side_dropdown = None
        
        # Canvas and buttons
        self.canvas = None
        self.clear_button = None
        self.print_button = None

        # Base dimensions for dropdowns (to be scaled), reduced by 50%
        self.base_dropdown_width = 7  # Reduced from 15 to 7 (50% reduction)
        self.base_dropdown_font_size = 8  # Reduced from 16 to 8 (50% reduction)

    def create(self):
        """Create the shelf view tab with 3D shelf visualization."""
        frame = ttk.Frame(self.tab, style=CUSTOM_FRAME_STYLE)
        frame.pack(padx=20, pady=20, fill="both", expand=True)
        print("Created main frame for Shelf View tab")
        
        # Create dropdown frame and center it
        self.dropdown_frame = ttk.Frame(frame, style=CUSTOM_FRAME_STYLE)
        self.dropdown_frame.pack(anchor="center", pady=10)  # Center the frame horizontally
        print("Created dropdown frame for Shelf View tab")
        
        print(f"Sections: {self.sections}")
        
        # Configure grid columns to center the content
        for col in range(10):  # 5 dropdowns (label + combobox = 10 columns)
            self.dropdown_frame.columnconfigure(col, weight=1, uniform="dropdown")

        # Section dropdown
        ttk.Label(self.dropdown_frame, text="Section:", font=LARGE_FONT).grid(row=0, column=0, padx=5, sticky="e")
        self.section_var = tk.StringVar()
        self.section_dropdown = ttk.Combobox(self.dropdown_frame, textvariable=self.section_var, values=self.sections, state="readonly", style=COMBOBOX_STYLE, font=DROPDOWN_FONT, width=self.base_dropdown_width)
        self.section_dropdown.grid(row=0, column=1, padx=5, sticky="w")
        self.section_dropdown.bind("<<ComboboxSelected>>", self.on_section_changed)
        print("Added Section dropdown")
        
        # Aisle dropdown (will be populated dynamically)
        ttk.Label(self.dropdown_frame, text="Aisle:", font=LARGE_FONT).grid(row=0, column=2, padx=5, sticky="e")
        self.aisle_var = tk.StringVar()
        self.aisle_dropdown = ttk.Combobox(self.dropdown_frame, textvariable=self.aisle_var, state="readonly", style=COMBOBOX_STYLE, font=DROPDOWN_FONT, width=self.base_dropdown_width)
        self.aisle_dropdown.grid(row=0, column=3, padx=5, sticky="w")
        self.aisle_dropdown.bind("<<ComboboxSelected>>", self.on_aisle_changed)
        print("Added Aisle dropdown")
        
        # Side dropdown (will be populated dynamically)
        ttk.Label(self.dropdown_frame, text="Side:", font=LARGE_FONT).grid(row=0, column=4, padx=5, sticky="e")
        self.side_var = tk.StringVar()
        self.side_dropdown = ttk.Combobox(self.dropdown_frame, textvariable=self.side_var, state="readonly", style=COMBOBOX_STYLE, font=DROPDOWN_FONT, width=self.base_dropdown_width)
        self.side_dropdown.grid(row=0, column=5, padx=5, sticky="w")
        self.side_dropdown.bind("<<ComboboxSelected>>", self.on_side_changed)
        print("Added Side dropdown")
        
        # Family dropdown
        ttk.Label(self.dropdown_frame, text="Family:", font=LARGE_FONT).grid(row=0, column=6, padx=5, sticky="e")
        self.family_var = tk.StringVar()
        self.family_dropdown = ttk.Combobox(self.dropdown_frame, textvariable=self.family_var, values=self.families, state="readonly", style=COMBOBOX_STYLE, font=DROPDOWN_FONT, width=self.base_dropdown_width)
        self.family_dropdown.grid(row=0, column=7, padx=5, sticky="w")
        self.family_dropdown.bind("<<ComboboxSelected>>", self.controller.on_family_changed)
        print("Added Family dropdown")
        
        # Category dropdown
        ttk.Label(self.dropdown_frame, text="Category:", font=LARGE_FONT).grid(row=0, column=8, padx=5, sticky="e")
        self.category_var = tk.StringVar()
        self.category_dropdown = ttk.Combobox(self.dropdown_frame, textvariable=self.category_var, state="readonly", style=COMBOBOX_STYLE, font=DROPDOWN_FONT, width=self.base_dropdown_width)
        self.category_dropdown.grid(row=0, column=9, padx=5, sticky="w")
        print("Added Category dropdown")
        
        # Create Canvas for 3D shelf visualization
        self.canvas_frame = ttk.Frame(frame, style=CUSTOM_FRAME_STYLE)
        self.canvas_frame.pack(fill="both", expand=True)
        print("Created canvas frame for Shelf View tab")
        
        self.canvas = tk.Canvas(self.canvas_frame, bg=CANVAS_BG_COLOR)
        self.canvas.pack(fill="both", expand=True)
        print("Created canvas for 3D shelf visualization")
        
        # Bind mouse events for selection
        self.canvas.bind("<Button-1>", self.controller.start_selection)
        self.canvas.bind("<B1-Motion>", self.controller.update_selection)
        self.canvas.bind("<ButtonRelease-1>", self.controller.end_selection)
        print("Bound mouse events for selection on canvas")
        
        # Bind resize event to redraw the shelf
        self.canvas.bind("<Configure>", self.controller.on_resize)
        print("Bound resize event to canvas")
        
        # Create buttons frame
        button_frame = ttk.Frame(frame, style=CUSTOM_FRAME_STYLE)
        button_frame.pack(pady=10)
        
        # Add Clear Values button
        self.clear_button = ttk.Button(button_frame, text="Clear Values: Off", command=self.controller.toggle_clear_values_mode, style=BUTTON_STYLE)
        self.clear_button.grid(row=0, column=0, padx=5)
        print("Added Clear Values button to Shelf View tab")
        
        # Add Print Shelf Layout button
        self.print_button = ttk.Button(button_frame, text="Print Shelf Layout", command=self.print_shelf_layout, style=BUTTON_STYLE)
        self.print_button.grid(row=0, column=1, padx=5)
        print("Added Print Shelf Layout button to Shelf View tab")

    def initialize_dropdowns(self):
        """Initialize dropdown values after the UI is fully ready."""
        # Only set the Family dropdown; leave Section, Aisle, and Side empty
        if self.families:
            self.family_var.set(self.families[0])
            # Set the category dropdown based on the first family
            categories = self.controller.model.categories.get(self.families[0], ["No Categories Available"])
            self.update_category_dropdown(categories)
        print("Initialized shelf view with dropdown values (Section, Aisle, Side left blank)")

    def on_section_changed(self, event):
        """Update the Aisle and Side dropdowns based on the selected section."""
        selected_section = self.section_var.get()
        if selected_section and selected_section in self.shelf_structure:
            config = self.shelf_structure[selected_section]
            self.aisles = list(range(1, config["aisles"] + 1))
            self.sides = list(range(1, config["sides"] + 1))
            
            # Update the Aisle dropdown
            self.aisle_dropdown['values'] = self.aisles
            self.aisle_var.set(self.aisles[0] if self.aisles else "")
            print(f"Updated Aisle dropdown for Section '{selected_section}': {self.aisles}")
            
            # Update the Side dropdown
            self.side_dropdown['values'] = self.sides
            self.side_var.set(self.sides[0] if self.sides else "")
            print(f"Updated Side dropdown for Section '{selected_section}': {self.sides}")
        
        # Trigger an update to refresh the view
        self.controller.on_section_changed(event)

    def on_aisle_changed(self, event):
        """Handle Aisle dropdown change."""
        self.controller.on_aisle_changed(event)

    def on_side_changed(self, event):
        """Handle Side dropdown change."""
        self.controller.on_side_changed(event)

    def update_category_dropdown(self, categories):
        """Update the Category dropdown with the given categories."""
        self.category_dropdown['values'] = categories
        self.category_var.set(categories[0] if categories else "")

    def update_dropdown_sizes(self):
        """Update the size of dropdown combo boxes based on the current scale factor."""
        # Calculate new width and font size based on scale_factor
        new_dropdown_width = int(self.base_dropdown_width * self.scale_factor)
        new_dropdown_width = max(new_dropdown_width, 5)  # Reduced minimum width (50% of previous 10)
        new_font_size = int(self.base_dropdown_font_size * self.scale_factor)
        new_font_size = max(new_font_size, 6)  # Reduced minimum font size (50% of previous 12)
        
        # Update the width and font of all dropdowns
        dropdowns = [
            self.section_dropdown,
            self.aisle_dropdown,
            self.side_dropdown,
            self.family_dropdown,
            self.category_dropdown
        ]
        
        for dropdown in dropdowns:
            dropdown.configure(width=new_dropdown_width)
            dropdown.configure(font=('Helvetica', new_font_size))
        
        print(f"Updated dropdown sizes: width={new_dropdown_width}, font_size={new_font_size}")

    def print_shelf_layout(self):
        """Handle the print action for the shelf layout."""
        # Check if all dropdowns are filled
        section = self.section_var.get()
        aisle = self.aisle_var.get()
        side = self.side_var.get()
        if not section or not aisle or not side:
            self.view.show_message("Warning", "Please select Section, Aisle, and Side values before printing.")
            return
        
        # Create a dialog to choose print option
        print_dialog = tk.Toplevel(self.tab)
        print_dialog.title("Print Shelf Layout")
        
        # Get screen dimensions
        screen_width = self.tab.winfo_screenwidth()
        screen_height = self.tab.winfo_screenheight()
        
        # Current size is 50% of screen; reduce by 40% (i.e., new size is 60% of current size)
        dialog_width = int(screen_width * 0.5 * 0.6)  # 50% * 60%
        dialog_height = int(screen_height * 0.5 * 0.6)
        
        # Center the dialog on the screen
        position_x = (screen_width - dialog_width) // 2
        position_y = (screen_height - dialog_height) // 2
        print_dialog.geometry(f"{dialog_width}x{dialog_height}+{position_x}+{position_y}")
        
        print_dialog.transient(self.tab)
        print_dialog.grab_set()
        
        ttk.Label(print_dialog, text="Select print option:", font=LARGE_FONT).pack(pady=10)
        
        # Set a uniform width for buttons and add spacing
        button_width = 20
        button_spacing = 10
        
        ttk.Button(print_dialog, text="Save as PDF", width=button_width, command=lambda: self.save_as_pdf(section, aisle, side, print_dialog), style=BUTTON_STYLE).pack(pady=button_spacing)
        ttk.Button(print_dialog, text="Print to Printer", width=button_width, command=lambda: self.print_to_printer(section, aisle, side, print_dialog), style=BUTTON_STYLE).pack(pady=button_spacing)
        ttk.Button(print_dialog, text="Cancel", width=button_width, command=print_dialog.destroy, style=BUTTON_STYLE).pack(pady=button_spacing)

    def save_as_pdf(self, section, aisle, side, dialog):
        """Save the shelf layout as a PDF file using a screenshot and reportlab."""
        dialog.destroy()
        
        # Ask user for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Shelf Layout as PDF"
        )
        if not file_path:
            return
        
        try:
            # Ensure the window is in focus and visible for the screenshot
            self.tab.winfo_toplevel().focus_force()
            self.tab.winfo_toplevel().update()
            
            # Get the canvas coordinates and dimensions
            self.canvas.update_idletasks()
            x = self.canvas.winfo_rootx()
            y = self.canvas.winfo_rooty()
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            # Validate coordinates and dimensions
            if width <= 0 or height <= 0:
                raise ValueError("Canvas width or height is invalid for screenshot.")
            
            # Capture a screenshot of the canvas area
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            screenshot_path = "temp_shelf_layout.png"
            screenshot.save(screenshot_path)
            
            # Verify the screenshot file exists
            if not os.path.exists(screenshot_path):
                raise FileNotFoundError(f"Screenshot file not created: {screenshot_path}")
            
            # Create a PDF using reportlab with letter size in landscape orientation
            from reportlab.lib.pagesizes import landscape
            pdf = SimpleDocTemplate(file_path, pagesize=landscape(letter))
            pdf_width, pdf_height = landscape(letter)  # Letter size in landscape: 792 x 612 points
            
            # Create content for the PDF
            elements = []
            
            # Add header text directly in the PDF (Section, Aisle, Side are already here)
            margin = 0.5 * inch
            c = reportlab_canvas.Canvas("temp_header.pdf", pagesize=landscape(letter))
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(pdf_width / 2, pdf_height - 50, "Shelf Layout")
            
            c.setFont("Helvetica", 12)
            c.drawCentredString(pdf_width / 2, pdf_height - 80, f"Section: {section}")
            c.drawCentredString(pdf_width / 2, pdf_height - 100, f"Aisle: {aisle}")
            c.drawCentredString(pdf_width / 2, pdf_height - 120, f"Side: {side}")
            c.showPage()
            c.save()
            
            # Load the shelf layout image
            img = ImageReader(screenshot_path)
            # Fit the image to the entire printable area with minimal margins
            img_width = pdf_width - 2 * margin
            img_height = pdf_height - 2 * margin - 150  # Leave space for header
            image = ReportLabImage(screenshot_path, width=img_width, height=img_height)
            image.hAlign = 'CENTER'
            image.vAlign = 'TOP'
            image.spaceBefore = 150  # Space for the header text
            elements.append(image)
            
            # Build the PDF
            pdf.build(elements)
            
            self.view.show_message("Success", f"Shelf layout saved as PDF to {file_path}")
            
        except Exception as e:
            self.view.show_message("Error", f"Failed to save PDF: {str(e)}")
        
        finally:
            # Clean up temporary files
            temp_files = ["temp_shelf_layout.png", "temp_header.pdf"]
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception as e:
                        print(f"Failed to remove temporary file {temp_file}: {str(e)}")

    def print_to_printer(self, section, aisle, side, dialog):
        """Print the shelf layout to a local printer."""
        dialog.destroy()
        
        try:
            # Generate a temporary PDF file with the shelf layout
            pdf_file = "temp_shelf_layout_with_info.pdf"
            
            # Ensure the window is in focus and visible for the screenshot
            self.tab.winfo_toplevel().focus_force()
            self.tab.winfo_toplevel().update()
            
            # Get the canvas coordinates and dimensions
            self.canvas.update_idletasks()
            x = self.canvas.winfo_rootx()
            y = self.canvas.winfo_rooty()
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            # Validate coordinates and dimensions
            if width <= 0 or height <= 0:
                raise ValueError("Canvas width or height is invalid for screenshot.")
            
            # Capture a screenshot of the canvas area
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            screenshot_path = "temp_shelf_layout.png"
            screenshot.save(screenshot_path)
            
            # Verify the screenshot file exists
            if not os.path.exists(screenshot_path):
                raise FileNotFoundError(f"Screenshot file not created: {screenshot_path}")
            
            # Create a PDF using reportlab with letter size in landscape orientation
            from reportlab.lib.pagesizes import landscape
            pdf = SimpleDocTemplate(pdf_file, pagesize=landscape(letter))
            pdf_width, pdf_height = landscape(letter)
            
            # Create content for the PDF
            elements = []
            
            # Add header text directly in the PDF (Section, Aisle, Side are already here)
            margin = 0.5 * inch
            c = reportlab_canvas.Canvas("temp_header.pdf", pagesize=landscape(letter))
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(pdf_width / 2, pdf_height - 50, "Shelf Layout")
            
            c.setFont("Helvetica", 12)
            c.drawCentredString(pdf_width / 2, pdf_height - 80, f"Section: {section}")
            c.drawCentredString(pdf_width / 2, pdf_height - 100, f"Aisle: {aisle}")
            c.drawCentredString(pdf_width / 2, pdf_height - 120, f"Side: {side}")
            c.showPage()
            c.save()
            
            # Load the shelf layout image
            img_width = pdf_width - 2 * margin
            img_height = pdf_height - 2 * margin - 150
            image = ReportLabImage(screenshot_path, width=img_width, height=img_height)
            image.hAlign = 'CENTER'
            image.vAlign = 'TOP'
            image.spaceBefore = 150
            elements.append(image)
            
            # Build the PDF
            pdf.build(elements)
            
            # Platform-specific printing
            system = platform.system()
            if system == "Windows":
                if win32api is None or win32print is None:
                    self.view.show_message("Error", "Printing on Windows requires the pywin32 library. Please install it using 'pip install pywin32'.")
                    # Fallback: Open the PDF with the default application and let the user print manually
                    os.startfile(pdf_file)  # Opens the PDF with the default application
                    self.view.show_message("Info", f"PDF opened with default application. Please print manually using your PDF reader.")
                else:
                    try:
                        # Get the default printer
                        printer_name = win32print.GetDefaultPrinter()
                        # Attempt to open the PDF with the default application and print
                        # We'll use subprocess to call the default PDF reader with a print command
                        # This assumes Adobe Acrobat Reader is installed; adjust for other PDF readers
                        try:
                            # Try to find Adobe Acrobat Reader (common path)
                            acrobat_path = r"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe"
                            if not os.path.exists(acrobat_path):
                                acrobat_path = r"C:\Program Files\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe"
                            if not os.path.exists(acrobat_path):
                                raise FileNotFoundError("Adobe Acrobat Reader not found. Please install a PDF reader and set it as the default for .pdf files.")
                            
                            # Use Acrobat Reader to print the PDF
                            subprocess.run([acrobat_path, "/p", "/h", pdf_file], check=True)
                            self.view.show_message("Success", f"Shelf layout sent to printer: {printer_name}")
                        except FileNotFoundError:
                            # Fallback: Open the PDF with the default application and let the user print manually
                            os.startfile(pdf_file)  # Opens the PDF with the default application
                            self.view.show_message("Info", f"PDF opened with default application. Please print manually using your PDF reader to {printer_name}.")
                    except Exception as e:
                        self.view.show_message("Error", f"Failed to print: {str(e)}. Ensure a PDF reader is installed and set as the default for .pdf files.")
            elif system in ["Linux", "Darwin"]:  # Darwin is macOS
                # Use lp (Linux) or lpr (macOS) to print the PDF
                if not shutil.which("lp" if system == "Linux" else "lpr"):
                    raise FileNotFoundError("Printing command 'lp' or 'lpr' not found. Please ensure printing utilities are installed.")
                subprocess.run(["lp" if system == "Linux" else "lpr", pdf_file], check=True)
                self.view.show_message("Success", "Shelf layout sent to default printer.")
            else:
                self.view.show_message("Error", f"Printing not supported on this platform: {system}")
            
        except Exception as e:
            self.view.show_message("Error", f"Failed to print: {str(e)}")
        
        finally:
            # Clean up temporary files
            temp_files = ["temp_shelf_layout.png", pdf_file, "temp_header.pdf"]
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception as e:
                        print(f"Failed to remove temporary file {temp_file}: {str(e)}")

    def draw_shelf_view(self, filtered_df, section, aisle, side):
        """Draw the 3D shelf visualization based on the filtered data."""
        self.canvas.delete("all")
        self.front_face_ids.clear()
        
        # Update dropdown sizes before redrawing the shelf view
        self.update_dropdown_sizes()
        
        # If any dropdown is empty or no data, display a reminder message instead of the shelf
        if not section or not aisle or not side or filtered_df is None:
            print("Section, Aisle, or Side is empty or no data; displaying reminder message")
            # Get canvas dimensions
            self.canvas.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            # Center the message
            center_x = canvas_width // 2
            center_y = canvas_height // 2
            # Display the reminder message with large text
            self.canvas.create_text(
                center_x, center_y,
                text="Please select Section, Aisle, and Side values",
                font=('Helvetica', 24, 'bold'),
                fill="black",
                anchor="center"
            )
            return
        
        # Determine max_level and max_shelf for drawing the shelf grid
        max_level = filtered_df['Level'].max()
        max_shelf = filtered_df['Shelf'].max()
        
        self.max_level = int(max_level)
        self.max_shelf = int(max_shelf)
        print(f"Max Level: {self.max_level}, Max Shelf: {self.max_shelf}")
        
        # Calculate base cell size (before scaling)
        canvas_width_base = 1000
        canvas_height_base = 600
        cell_width_base = canvas_width_base // self.max_shelf
        cell_height_base = canvas_height_base // self.max_level
        self.cell_width_base = min(cell_width_base, 60)
        self.cell_height_base = min(cell_height_base, 80)
        
        # Calculate the initial aspect ratio (only once)
        if self.initial_aspect_ratio is None:
            self.initial_cell_width = self.cell_width_base
            self.initial_cell_height = self.cell_height_base
            self.initial_aspect_ratio = self.initial_cell_width / self.initial_cell_height
            print(f"Initial aspect ratio: {self.initial_aspect_ratio}")
        
        # Apply the scale factor to maintain aspect ratio
        self.cell_width = self.cell_width_base * self.scale_factor
        self.cell_height = self.cell_height_base * self.scale_factor
        
        # Ensure the aspect ratio is maintained
        current_aspect_ratio = self.cell_width / self.cell_height
        if abs(current_aspect_ratio - self.initial_aspect_ratio) > 0.01:
            self.cell_height = self.cell_width / self.initial_aspect_ratio
            print(f"Adjusted cell height to maintain aspect ratio: cell_width={self.cell_width}, cell_height={self.cell_height}")
        
        # Scale the depth and fonts dynamically
        self.depth = 10 * self.scale_factor
        label_font_size = int(LABEL_FONT_BASE * self.scale_factor)  # Recalculate dynamically
        self.label_font = ('Helvetica', max(label_font_size, 6))  # Update label font with new size
        print(f"Scaled sizes: cell_width={self.cell_width}, cell_height={self.cell_height}, depth={self.depth}, label_font_size={label_font_size}")
        
        # Calculate the total size of the shelf grid (including space for labels)
        label_space_left = 50 * self.scale_factor
        label_space_top = 30 * self.scale_factor
        total_width = self.max_shelf * self.cell_width + self.depth + label_space_left
        total_height = self.max_level * self.cell_height + self.depth + label_space_top
        
        # Center the shelf grid in the canvas
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        offset_x = (canvas_width - total_width) // 2 + label_space_left
        offset_y = (canvas_height - total_height) // 2 + label_space_top
        print(f"Centering shelf grid: offset_x={offset_x}, offset_y={offset_y}")
        
        # Draw shelf labels (Shelf 1, Shelf 2, etc.) above the grid
        for shelf in range(1, self.max_shelf + 1):
            label_x = (shelf - 1) * self.cell_width + offset_x + self.cell_width / 2
            label_y = offset_y - self.depth - 10 * self.scale_factor
            self.canvas.create_text(
                label_x, label_y,
                text=f"S{shelf}",
                font=self.label_font,
                fill="black",
                anchor="center"
            )
        
        # Draw level labels (Level 1, Level 2, etc.) to the left of the grid
        for level in range(1, self.max_level + 1):
            display_row = self.max_level - level
            label_y = display_row * self.cell_height + offset_y + self.cell_height / 2
            label_x = offset_x - self.depth - 30 * self.scale_factor
            self.canvas.create_text(
                label_x, label_y,
                text=f"L{level}",
                font=self.label_font,
                fill="black",
                anchor="center"
            )
        
        # Draw the shelf grid
        self.cell_coords = {}
        for level in range(1, self.max_level + 1):
            display_row = self.max_level - level
            for shelf in range(1, self.max_shelf + 1):
                x1 = (shelf - 1) * self.cell_width + offset_x
                y1 = display_row * self.cell_height + offset_y
                x2 = x1 + self.cell_width
                y2 = y1 + self.cell_height
                
                x1_3d = x1 + self.depth
                y1_3d = y1
                x2_3d = x2 + self.depth
                y2_3d = y2
                
                front_face_tag = f"front_face_{level}_{shelf}"
                front_face_id = self.canvas.create_polygon(
                    x1_3d, y1_3d,
                    x2_3d, y1_3d,
                    x2, y2,
                    x1, y2,
                    fill=SHELF_FRONT_COLOR, outline="black",
                    tags=front_face_tag
                )
                self.front_face_ids[(level, shelf)] = front_face_id
                
                self.canvas.create_polygon(
                    x1_3d, y1_3d,
                    x2_3d, y1_3d,
                    x2_3d - self.depth, y1_3d - self.depth,
                    x1_3d - self.depth, y1_3d - self.depth,
                    fill=SHELF_TOP_COLOR, outline="black"
                )
                
                self.canvas.create_polygon(
                    x2_3d, y1_3d,
                    x2_3d - self.depth, y1_3d - self.depth,
                    x2 - self.depth, y2 - self.depth,
                    x2, y2,
                    fill=SHELF_RIGHT_COLOR, outline="black"
                )
                
                self.cell_coords[(level, shelf)] = (x1, y1, x2, y2)
        
        # Only draw category information if all dropdown values are non-empty
        if not section or not aisle or not side:
            print("Skipping category information drawing due to empty dropdown values")
            print(f"Drew 3D shelf grid with {self.max_level} levels and {self.max_shelf} shelves")
            return
        
        # Calculate the maximum number of categories in any family in the current view
        family_category_counts = filtered_df.groupby('Family')['Category'].nunique()
        max_categories = family_category_counts.max() if not family_category_counts.empty else 0
        print(f"Maximum number of categories in any family in current view: {max_categories}")
        
        # Assign colors to categories, reusing existing assignments and ensuring uniqueness within families
        for family in family_category_counts.index:
            # Initialize color usage set for this family if not already present
            if family not in self.view.family_color_usage:
                self.view.family_color_usage[family] = set()
            
            # Get unique categories for this family, sorted alphabetically for consistency
            categories_in_family = sorted(filtered_df[filtered_df['Family'] == family]['Category'].dropna().unique())
            for category in categories_in_family:
                key = f"{family}|{category}"
                # Skip if this category already has a color assigned
                if key in self.view.category_colors:
                    continue
                
                # Find an unused color for this family
                used_colors = self.view.family_color_usage[family]
                available_color_indices = [i for i in range(len(self.view.available_colors)) if i not in used_colors]
                if not available_color_indices:
                    # If no unused colors, cycle through the colors starting from the beginning
                    color_idx = len(used_colors) % len(self.view.available_colors)
                else:
                    color_idx = available_color_indices[0]
                
                # Assign the color and mark it as used
                self.view.category_colors[key] = self.view.available_colors[color_idx]
                self.view.family_color_usage[family].add(color_idx)
        
        print(f"Updated category color mapping: {self.view.category_colors}")
        
        # Draw category information on the shelves
        for level in range(1, self.max_level + 1):
            display_row = self.max_level - level
            for shelf in range(1, self.max_shelf + 1):
                x1 = (shelf - 1) * self.cell_width + offset_x
                y1 = display_row * self.cell_height + offset_y
                x2 = x1 + self.cell_width
                y2 = y1 + self.cell_height
                
                x1_3d = x1 + self.depth
                y1_3d = y1
                x2_3d = x2 + self.depth
                y2_3d = y2
                
                # Use filtered_df to get the Family and Category for this shelf
                mask = (
                    (filtered_df['Level'] == level) &
                    (filtered_df['Shelf'] == shelf)
                )
                row = filtered_df[mask]
                if not row.empty:
                    category = str(row.iloc[0]['Category'])
                    family = str(row.iloc[0]['Family'])
                    if pd.isna(category) or category == "" or category == "nan":
                        continue
                    
                    # Get the colors for the horizontal bar using Family|Category key
                    key = f"{family}|{category}"
                    colors = self.view.category_colors.get(key, {
                        'front': "gray",
                        'top': "lightgray",
                        'right': "darkgray"
                    })
                    bar_color_front = colors['front']
                    bar_color_top = colors['top']
                    bar_color_right = colors['right']
                    
                    # Calculate the dimensions of the horizontal bar
                    bar_width = self.cell_width  # 100% of the shelf width
                    bar_height = self.cell_height * 0.4  # 40% of the shelf height
                    bar_x1 = x1_3d  # Span the full width of the shelf
                    bar_x2 = x2_3d
                    bar_y1 = (y1_3d + y2_3d) / 2 - bar_height / 2  # Center the bar vertically
                    bar_y2 = bar_y1 + bar_height
                    
                    # Draw the 3D horizontal bar
                    # Front face
                    print(f"Drawing 3D horizontal bar for L{level} S{shelf} (Family: {family}, Category: {category}): x1={bar_x1}, x2={bar_x2}, y1={bar_y1}, y2={bar_y2}, front_color={bar_color_front}")
                    self.canvas.create_polygon(
                        bar_x1, bar_y1,
                        bar_x2, bar_y1,
                        bar_x2, bar_y2,
                        bar_x1, bar_y2,
                        fill=bar_color_front, outline=""
                    )
                    # Top face
                    self.canvas.create_polygon(
                        bar_x1, bar_y1,
                        bar_x2, bar_y1,
                        bar_x2 - self.depth, bar_y1 - self.depth,
                        bar_x1 - self.depth, bar_y1 - self.depth,
                        fill=bar_color_top, outline=""
                    )
                    # Right face
                    self.canvas.create_polygon(
                        bar_x2, bar_y1,
                        bar_x2 - self.depth, bar_y1 - self.depth,
                        bar_x2 - self.depth, bar_y2 - self.depth,
                        bar_x2, bar_y2,
                        fill=bar_color_right, outline=""
                    )
                    
                    # Draw the Category text in black, centered on the shelf
                    # Step 1: Calculate the maximum font size based on shelf dimensions
                    max_width = self.cell_width - 20  # Padding to prevent overflow
                    max_height = self.cell_height - 20  # Padding to prevent overflow
                    
                    # Start with a conservative font size
                    font_size = int(self.cell_width / 15)
                    font_size = max(font_size, 6)  # Minimum font size
                    
                    # Split the text into words
                    words = category.split()  # Split at spaces
                    lines = []
                    
                    # Step 2: Adjust font size and calculate lines to fit within the shelf
                    while font_size > 6:  # Minimum font size
                        avg_char_width = font_size * 0.7  # Adjusted multiplier for better fit
                        max_chars_per_line = int(max_width / avg_char_width)
                        print(f"Trying font size {font_size}, max_chars_per_line={max_chars_per_line} for category '{category}'")
                        
                        # Split text into lines based on the current font size
                        lines = []
                        current_line = []
                        current_char_count = 0
                        
                        for word in words:
                            word_length = len(word)
                            # Account for the space between words (1 char per space)
                            space_needed = 1 if current_line else 0
                            if current_char_count + word_length + space_needed <= max_chars_per_line:
                                current_line.append(word)
                                current_char_count += word_length + space_needed
                            else:
                                if current_line:
                                    lines.append(" ".join(current_line))
                                current_line = [word]
                                current_char_count = word_length
                        if current_line:
                            lines.append(" ".join(current_line))
                        
                        # Calculate the total text height
                        num_lines = len(lines)
                        line_spacing = font_size * 1.1
                        total_text_height = num_lines * line_spacing
                        
                        # Check if the text fits within the shelf dimensions
                        fits_width = all(len(line) * avg_char_width <= max_width for line in lines)
                        fits_height = total_text_height <= max_height
                        print(f"Font size {font_size}: num_lines={num_lines}, total_text_height={total_text_height}, fits_width={fits_width}, fits_height={fits_height}")
                        
                        if fits_width and fits_height:
                            break  # Font size is good
                        font_size -= 1  # Reduce font size and try again
                    
                    # Step 3: Reduce font size by 30% as requested
                    original_font_size = font_size
                    font_size = int(font_size * 0.7)  # Reduce by 30%
                    font_size = max(font_size, 6)  # Ensure minimum font size
                    print(f"Reduced font size by 30%: from {original_font_size} to {font_size} for category '{category}'")
                    
                    # Recalculate line spacing and total text height with the new font size
                    line_spacing = font_size * 1.1
                    total_text_height = num_lines * line_spacing
                    
                    # Step 4: Draw the text with the adjusted font size
                    self.shelf_text_font = ('Helvetica', font_size, 'bold')
                    print(f"Final font size {font_size} for category '{category}' on shelf L{level} S{shelf}, lines={num_lines}")
                    
                    start_y = (y1 + y2) / 2 - total_text_height / 2 + line_spacing / 2
                    
                    for idx, line in enumerate(lines):
                        text_x = (x1 + x2) / 2 + self.depth / 2
                        text_y = start_y + idx * line_spacing
                        self.canvas.create_text(
                            text_x, text_y,
                            text=line,
                            font=self.shelf_text_font,
                            fill="black",
                            anchor="center"
                        )
        print(f"Drew 3D shelf grid with {self.max_level} levels and {self.max_shelf} shelves")

    def get_selection_coords(self):
        """Return the coordinates of the shelves for selection."""
        return self.cell_coords

    def highlight_shelf(self, level, shelf, color):
        """Highlight the front face of a shelf with the given color."""
        front_face_tag = f"front_face_{level}_{shelf}"
        self.canvas.itemconfig(front_face_tag, fill=color)
        print(f"{'Highlighted' if color == 'lightblue' else 'Reset color for'} shelf (L{level}, S{shelf}) with tag {front_face_tag}")
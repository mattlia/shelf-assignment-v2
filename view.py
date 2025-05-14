import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from .menu_bar import create_menu_bar
from .logo_display import create_logo
from .table_tab import TableTab
from .shelf_tab import ShelfTab
from .styles import apply_styles
from constants import LARGE_FONT

class ShelfView:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        
        # Set window title
        self.root.title("Shelf Assignment Editor")
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set window size to 90% of the screen size
        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.9)
        
        # Center the window on the screen
        position_x = (screen_width - window_width) // 2
        position_y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
        
        # Maximize the window on start
        self.root.state('zoomed')
        
        # Initialize attributes
        self.table_tab_component = None
        self.shelf_tab = None
        self.notebook = None
        self.style = None
        
        # Persistent color mapping for categories within families
        self.category_colors = {}
        self.family_color_usage = {}
        self.available_colors = [
            {'front': "#87CEEB", 'top': "#B0E0E6", 'right': "#5F9EA0"},
            {'front': "#90EE90", 'top': "#ADFF2F", 'right': "#7FFF00"},
            {'front': "#F08080", 'top': "#FF4040", 'right': "#CD5C5C"},
            {'front': "#FFFF99", 'top': "#FFFFCC", 'right': "#EEE8AA"},
            {'front': "#FFB6C1", 'top': "#FFC1CC", 'right': "#FF9999"},
            {'front': "#E0FFFF", 'top': "#EFFFFF", 'right': "#B0E0E6"},
            {'front': "#FFA07A", 'top': "#FFBB99", 'right': "#FF8C69"},
            {'front': "#D3D3D3", 'top': "#E6E6E6", 'right': "#C0C0C0"},
            {'front': "#98FB98", 'top': "#BFFFBA", 'right': "#90EE90"},
            {'front': "#FFDAB9", 'top': "#FFE4C4", 'right': "#FFCC99"},
            {'front': "#FFECB3", 'top': "#FFF9C4", 'right': "#FFD54F"},
            {'front': "#B0C4DE", 'top': "#C6D9F1", 'right': "#9AC0CD"},
            {'front': "#F0E68C", 'top': "#FFFACD", 'right': "#EEE8AA"},
            {'front': "#FFE4E1", 'top': "#FFE4E4", 'right': "#FFB6C1"},
            {'front': "#E6E6FA", 'top': "#F0F0FF", 'right': "#D8BFD8"},
            {'front': "#FFDEAD", 'top': "#FFEFD5", 'right': "#FFCE96"},
            {'front': "#DDA0DD", 'top': "#E6B0E6", 'right': "#DA70D6"},
            {'front': "#F5F5DC", 'top': "#FFFFE4", 'right': "#F0EAD6"},
            {'front': "#AFEEEE", 'top': "#C1F0F0", 'right': "#96CDCD"},
            {'front': "#FFFACD", 'top': "#FFFDE7", 'right': "#FFFACD"},
        ]
        
        # Load the original logo image to get its aspect ratio
        try:
            logo_image = Image.open("enson_logo.jpg")
            self.original_logo_width, self.original_logo_height = logo_image.size
            self.logo_aspect_ratio = self.original_logo_width / self.original_logo_height
            print(f"Original logo dimensions: {self.original_logo_width}x{self.original_logo_height}, aspect ratio: {self.logo_aspect_ratio}")
        except Exception as e:
            print(f"Failed to load original logo for aspect ratio: {str(e)}")
            # Fallback to a default aspect ratio (2:1) if the image can't be loaded
            self.logo_aspect_ratio = 2.0
            self.original_logo_width = 100
            self.original_logo_height = 50
        
        # Initialize UI components (without setting dropdowns)
        self.initialize_ui()
        
        print("ShelfView initialization completed")

    def initialize_ui(self):
        """Initialize all UI components after the controller is set."""
        # Create the menu bar
        create_menu_bar(self.root, self.controller)
        
        # Apply a modern theme and custom styles
        self.style = ttk.Style()
        apply_styles(self.style)
        
        # Create a frame for the logo between the menu bar and the tab bar
        logo_frame = tk.Frame(self.root, bg="white")
        logo_frame.pack(fill="x", pady=5)
        
        # Load and display the logo in the center of the frame
        self.logo_label = create_logo(logo_frame)
        self.logo_label.pack(anchor="center")
        
        # Bind resize event to update logo size
        self.root.bind("<Configure>", self.on_resize)
        
        # Create tabbed interface
        print("Creating ttk.Notebook for tabbed interface")
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs with original names
        self.table_tab = ttk.Frame(self.notebook, style="Custom.TFrame")
        self.shelf_tab_frame = ttk.Frame(self.notebook, style="Custom.TFrame")
        self.notebook.add(self.table_tab, text="Table View")
        self.notebook.add(self.shelf_tab_frame, text="Shelf View")
        print("Tabs created: Table View, Shelf View")
        
        # Initialize tab views
        self.table_tab_component = TableTab(self.table_tab, self.controller, self)
        self.shelf_tab = ShelfTab(self.shelf_tab_frame, self.controller, self)
        self.table_tab_component.create()
        self.shelf_tab.create()
        
        # Bind tab change event after tabs are fully initialized
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def initialize_dropdowns(self):
        """Initialize dropdown values after the UI is fully ready."""
        if self.shelf_tab:
            self.shelf_tab.initialize_dropdowns()
        else:
            print("Warning: ShelfTab not initialized; cannot set dropdowns.")

    def on_tab_changed(self, event):
        """Handle tab change events to refresh the Table View when selected."""
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        print(f"Tab changed to: {selected_tab}")
        if selected_tab == "Table View":
            self.table_tab_component.update_treeview()
        elif selected_tab == "Shelf View":
            self.controller.update_shelf_view()

    def on_resize(self, event):
        """Handle window resize to adjust logo size."""
        # Only proceed if the event is for the root window
        if event.widget != self.root:
            return
        
        # Get current window size
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Base logo size (original size when window is at 90% of 1920x1080, increased by 50%)
        base_window_width = int(1920 * 0.9)  # 1728
        base_logo_width = 150  # Increased by 50% from 100
        base_logo_height = int(base_logo_width / self.logo_aspect_ratio)  # Maintain aspect ratio
        
        # Calculate scale factor based on window width
        scale_factor = window_width / base_window_width
        new_logo_width = int(base_logo_width * scale_factor)
        new_logo_height = int(new_logo_width / self.logo_aspect_ratio)  # Preserve aspect ratio
        
        # Ensure minimum size
        new_logo_width = max(new_logo_width, 75)  # Adjusted minimum to match 50% increase
        new_logo_height = max(new_logo_height, int(75 / self.logo_aspect_ratio))
        
        # Update logo size
        try:
            logo_image = Image.open("enson_logo.jpg")
            logo_image = logo_image.resize((new_logo_width, new_logo_height), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_image)
            self.logo_label.configure(image=logo_photo)
            self.logo_label.image = logo_photo  # Keep a reference to avoid garbage collection
            print(f"Resized logo to {new_logo_width}x{new_logo_height}")
        except Exception as e:
            print(f"Failed to resize logo: {str(e)}")

    def show_message(self, title, message):
        """Display a message to the user."""
        print(f"Showing message box: Title='{title}', Message='{message}'")
        if "Success" not in title:
            messagebox.showwarning(title, message)
        else:
            messagebox.showinfo(title, message)
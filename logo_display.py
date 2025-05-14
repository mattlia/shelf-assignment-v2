import tkinter as tk
from PIL import Image, ImageTk
from constants import LOGO_FILE

def create_logo(root):
    """Load and display the logo at the top of the window and return the label."""
    try:
        logo_image = Image.open(LOGO_FILE)
        # Initial size (will be resized dynamically in view.py)
        logo_image = logo_image.resize((100, 100), Image.Resampling.LANCZOS)
        logo_photo = ImageTk.PhotoImage(logo_image)
        
        logo_label = tk.Label(root, image=logo_photo, bg="white")
        logo_label.image = logo_photo  # Keep a reference to avoid garbage collection
        logo_label.pack(pady=10)
        print("Loaded and displayed logo")
    except Exception as e:
        print(f"Error loading logo: {str(e)}")
        # Create a placeholder label if the logo fails to load
        logo_label = tk.Label(root, text="Logo Placeholder", bg="white", fg="black")
        logo_label.pack(pady=10)
    
    return logo_label
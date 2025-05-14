import tkinter as tk
from tkinter import ttk
from constants import BUTTON_FONT, DROPDOWN_FONT

def apply_styles(style):
    """Apply custom styles to ttk widgets."""
    # Configure the style for frames
    style.configure("Custom.TFrame", background="#f0f0e8")
    
    # Configure the style for Treeview
    style.configure("Treeview", rowheight=35, font=('Helvetica', 10), background="#f0f0e8")
    style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'))
    
    # Configure the style for buttons with better contrast and simulated rounded corners
    style.configure("TButton",
                    font=BUTTON_FONT,
                    padding=15,
                    background="#4a90e2",  # Vivid blue background
                    foreground="#333333",  # Dark gray (light black) text for high contrast
                    borderwidth=1,
                    relief="raised")
    style.map("TButton",
              background=[('active', '#357abd'), ('pressed', '#2c6399')],
              foreground=[('active', '#333333'), ('pressed', '#333333')],  # Dark gray in all states
              relief=[('active', 'raised'), ('pressed', 'sunken')],
              borderwidth=[('active', 1), ('pressed', 1)])
    
    # Configure the style for comboboxes
    style.configure("TCombobox", font=DROPDOWN_FONT, padding=5, arrowsize=30)
    
    # Configure the dropdown list font for Combobox
    style.configure("TCombobox.Listbox", font=('Helvetica', 21))
    
    # Configure the style for notebook tabs with a more vivid, less boxy look
    style.configure("TNotebook", tabmargins=[5, 5, 5, 0], background="#f0f0e8")
    style.configure("TNotebook.Tab",
                    padding=[15, 8],
                    font=('Helvetica', 12, 'bold'),
                    borderwidth=2,
                    relief="raised")
    style.map("TNotebook.Tab",
              background=[('selected', '#ffcc80'), ('!selected', '#ffe0b2')],
              foreground=[('selected', 'black'), ('!selected', 'black')],
              relief=[('selected', 'raised'), ('!selected', 'flat')],
              borderwidth=[('selected', 2), ('!selected', 1)],
              shadow=[('selected', 5), ('!selected', 3)],
              expand=[('selected', [0, 0, 0, 0]), ('!selected', [0, 0, 0, 0])])
    
    print("Applied custom styles to ttk widgets")
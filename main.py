import tkinter as tk
import os
from model import ShelfModel
from view.view import ShelfView
from controller import ShelfController
from constants import FAMILY_FILE, OUTPUT_FILE

def main():
    if not os.path.exists(FAMILY_FILE):
        print(f"Family file not found: {FAMILY_FILE}")
        return
    
    root = tk.Tk()
    try:
        model = ShelfModel()
        # Check if OUTPUT_FILE exists; if not, generate it
        if not os.path.exists(OUTPUT_FILE):
            print(f"Output file not found: {OUTPUT_FILE}. Generating a new one...")
            success, message = model.generate_shelf_assignment()
            if not success:
                print(f"Failed to generate output file: {message}")
                root.destroy()
                return
            print(f"Output file generated: {OUTPUT_FILE}")
        
        controller = ShelfController(root, model, None)
        view = ShelfView(root, controller)
        controller.view = view
        controller.set_ui_ready()
        # Initialize the dropdowns (keeping Section, Aisle, Side empty)
        view.initialize_dropdowns()
        # Draw the initial empty shelf view
        controller.update_shelf_view()
        print("ShelfController instance created")
        root.mainloop()
    except Exception as e:
        print(f"Failed to initialize application: {str(e)}")
        root.destroy()

if __name__ == "__main__":
    main()
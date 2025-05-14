import tkinter as tk
from tkinter import ttk
from constants import *

class TableTab:
    def __init__(self, tab, controller, view):
        self.tab = tab
        self.controller = controller
        self.view = view
        self.tree = None
        self.dropdown = None

    def create(self):
        """Create the table view tab with a Treeview for data editing."""
        frame = ttk.Frame(self.tab, style=CUSTOM_FRAME_STYLE)
        frame.pack(padx=20, pady=20, fill="both", expand=True)
        print("Created main frame for Table View tab")
        
        columns = self.controller.get_columns()
        print(f"Created Treeview with columns: {columns}")
        
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", style=TREEVIEW_STYLE)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        self.update_treeview()
        
        # Add scrollbars
        yscroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        print("Added scrollbars to Treeview")
        
        # Layout the Treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        print("Laid out Treeview and scrollbars")
        
        # Bind click event to the Treeview
        self.tree.bind("<ButtonRelease-1>", self.controller.on_table_click)
        
        # Add Save button
        save_button = ttk.Button(frame, text="Save", command=self.controller.save_data, style=BUTTON_STYLE)
        save_button.grid(row=2, column=0, pady=10, columnspan=2)
        print("Added Save button to Table View tab")

    def update_treeview(self):
        """Update the Treeview with the latest data."""
        print("Refreshing Table View")
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get the latest data
        df = self.controller.get_data()
        for idx, row in df.iterrows():
            self.tree.insert("", "end", iid=str(idx), values=list(row))
        print(f"Inserted {len(df)} rows into Treeview")

    def update_treeview_row(self, row_id, values):
        """Update a specific row in the Treeview."""
        print(f"Updating Treeview row {row_id} with values: {values}")
        self.tree.item(row_id, values=values)
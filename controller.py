class ShelfController:
    def __init__(self, root, model, view):
        print("Starting ShelfController initialization")
        self.model = model
        self.view = view
        self.selected_cells = set()
        self.start_x = None
        self.start_y = None
        self.selection_rect = None
        self.clear_values_mode = False  # Toggle for clearing values during selection
        self.is_ui_ready = False  # Flag to ensure UI is ready
        self.resize_timer = None  # Timer for debouncing resize events
        print("ShelfController initialization completed")

    def set_ui_ready(self):
        """Mark the UI as ready for interaction."""
        self.is_ui_ready = True

    def get_columns(self):
        return list(self.model.df.columns)

    def get_data(self):
        return self.model.df

    def get_families(self):
        return self.model.families

    def get_unique_values(self, column):
        return self.model.get_unique_values(column)

    def save_data(self):
        success, message = self.model.save_data()
        # Only show message if there is an error during saving
        if not success:
            self.view.show_message("Warning", message)

    def generate_shelf_assignment(self):
        """Generate the shelf assignment output file and refresh the view."""
        if not self.is_ui_ready:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        success, message = self.model.generate_shelf_assignment()
        self.view.show_message("Shelf Assignment Generation", message)
        if success:
            # Refresh the Table View and Shelf View to reflect the new data
            self.view.table_tab_component.update_treeview()
            self.update_shelf_view()

    def toggle_clear_values_mode(self):
        """Toggle the clear values mode and update the button label."""
        if not self.is_ui_ready or not hasattr(self.view, 'shelf_tab') or self.view.shelf_tab is None:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        self.clear_values_mode = not self.clear_values_mode
        if self.clear_values_mode:
            self.view.shelf_tab.clear_button.config(text="Clear Values: On")
            print("Clear Values mode enabled")
        else:
            self.view.shelf_tab.clear_button.config(text="Clear Values: Off")
            print("Clear Values mode disabled")

    def on_table_click(self, event):
        if not self.is_ui_ready or not hasattr(self.view, 'table_tab_component') or self.view.table_tab_component is None:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        region = self.view.table_tab_component.tree.identify("region", event.x, event.y)
        if region != "cell":
            print("Not a cell region, exiting")
            return
        
        row_id = self.view.table_tab_component.tree.identify_row(event.y)
        column_id = self.view.table_tab_component.tree.identify_column(event.x)
        column_idx = int(column_id.replace("#", "")) - 1
        column_name = self.model.df.columns[column_idx]
        
        if column_name not in ["Family", "Category"]:
            print(f"Column {column_name} is not editable (Family or Category required)")
            return
        
        bbox = self.view.table_tab_component.tree.bbox(row_id, column_id)
        if not bbox:
            print("Bounding box is empty, cannot place dropdown")
            return
        
        x, y, width, height = bbox
        window_width = self.view.root.winfo_width()
        max_width = window_width - x - 20
        adjusted_width = min(width + 20, max_width)
        if x + adjusted_width > window_width:
            x = window_width - adjusted_width - 20
        
        dropdown = ttk.Combobox(self.view.table_tab_component.tree, state="normal", style="TCombobox")
        if column_name == "Family":
            full_values = self.model.families
            dropdown["values"] = full_values
            current_value = str(self.model.df.at[int(row_id), "Family"])
            if pd.isna(current_value) or current_value == "nan":
                current_value = ""
            if current_value in full_values:
                dropdown.set(current_value)
            else:
                dropdown.set("")
            print(f"Family dropdown created with values: {full_values}, current: {current_value}")
        else:
            family = str(self.model.df.at[int(row_id), "Family"])
            if pd.isna(family) or family == "nan":
                family = ""
            full_values = self.model.categories.get(family, ["No Categories Available"])
            dropdown["values"] = full_values
            current_value = str(self.model.df.at[int(row_id), "Category"])
            if pd.isna(current_value) or current_value == "nan":
                current_value = ""
            if current_value in dropdown["values"]:
                dropdown.set(current_value)
            else:
                dropdown.set("")
            print(f"Category dropdown created for family '{family}' with values: {dropdown['values']}, current: {current_value}")
        
        dropdown.place(x=x, y=y, width=adjusted_width, height=height)
        dropdown.lift()
        dropdown.focus_set()
        
        dropdown.bind("<KeyRelease>", lambda e: self.on_table_dropdown_key_release(e, dropdown, full_values))
        dropdown.bind("<<ComboboxSelected>>", lambda e: self.on_table_dropdown_select(e, dropdown, row_id, column_name))
        dropdown.bind("<FocusOut>", lambda e: self.on_table_dropdown_close(e, dropdown))
        dropdown.bind("<Return>", lambda e: self.on_table_dropdown_select(e, dropdown, row_id, column_name))
        self.view.table_tab_component.dropdown = dropdown

    def on_table_dropdown_key_release(self, event, dropdown, full_values):
        if not self.is_ui_ready:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        if event.keysym in ["Up", "Down", "Return"]:
            print(f"Arrow key or Enter pressed: {event.keysym}, skipping filter")
            return
        
        typed_text = dropdown.get().strip().lower()
        print(f"Key released, typed text: {typed_text}")
        
        if typed_text == "":
            dropdown["values"] = full_values
            print(f"Restored full values: {full_values}")
        else:
            filtered_values = [val for val in full_values if val.lower().startswith(typed_text)]
            dropdown["values"] = filtered_values
            print(f"Filtered values: {filtered_values}")
        
        self.view.root.after(100, lambda: dropdown.event_generate('<Down>'))
        dropdown.focus_set()

    def on_table_dropdown_select(self, event, dropdown, row_id, column_name):
        if not self.is_ui_ready:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        print("Dropdown selection made")
        selected_value = dropdown.get()
        print(f"Selected value: {selected_value} for {column_name} in row {row_id}")
        
        values = self.model.update_cell(row_id, column_name, selected_value)
        self.view.table_tab_component.update_treeview_row(row_id, values)
        
        if column_name == "Family":
            if self.view.shelf_tab and hasattr(self.view.shelf_tab, 'family_var'):
                self.view.shelf_tab.family_var.set(selected_value)
                self.on_family_changed(None)
        elif column_name == "Category":
            if self.view.shelf_tab and hasattr(self.view.shelf_tab, 'category_var'):
                self.view.shelf_tab.category_var.set(selected_value)
        
        dropdown.destroy()
        self.view.table_tab_component.dropdown = None

    def on_table_dropdown_close(self, event, dropdown):
        if not self.is_ui_ready:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        print("Dropdown lost focus, closing")
        dropdown.destroy()
        self.view.table_tab_component.dropdown = None

    def on_section_changed(self, event):
        if not self.is_ui_ready:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        # The section change has already updated the aisle and side dropdowns in ShelfTab
        # Reset aisle and side variables to ensure valid selections
        if self.view.shelf_tab.aisles:
            self.view.shelf_tab.aisle_var.set(self.view.shelf_tab.aisles[0])
        if self.view.shelf_tab.sides:
            self.view.shelf_tab.side_var.set(self.view.shelf_tab.sides[0])
        self.update_shelf_view()

    def on_aisle_changed(self, event):
        if not self.is_ui_ready:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        # Reset side variable to ensure a valid selection
        if self.view.shelf_tab.sides:
            self.view.shelf_tab.side_var.set(self.view.shelf_tab.sides[0])
        self.update_shelf_view()

    def on_side_changed(self, event):
        if not self.is_ui_ready:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        self.update_shelf_view()

    def on_family_changed(self, event):
        if not self.is_ui_ready or not hasattr(self.view, 'shelf_tab') or self.view.shelf_tab is None:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        family = self.view.shelf_tab.family_var.get()
        categories = self.model.categories.get(family, ["No Categories Available"])
        self.view.shelf_tab.update_category_dropdown(categories)
        print(f"Updated Category dropdown for Family '{family}': {categories}")

    def update_shelf_view(self, event=None):
        if not self.is_ui_ready or not hasattr(self.view, 'shelf_tab') or self.view.shelf_tab is None:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        section = self.view.shelf_tab.section_var.get()
        aisle = self.view.shelf_tab.aisle_var.get()
        side = self.view.shelf_tab.side_var.get()
        # Ensure aisle and side are valid integers
        try:
            aisle = int(aisle) if aisle else 0
            side = int(side) if side else 0
        except ValueError:
            print(f"Invalid aisle or side value: Aisle='{aisle}', Side='{side}'")
            return
        filtered_df = self.model.get_filtered_data(section, aisle, side)
        print(f"Updating shelf view with filtered_df: {filtered_df.shape if filtered_df is not None else 'None'}")
        self.view.shelf_tab.draw_shelf_view(filtered_df, section, aisle, side)

    def on_resize(self, event):
        if not self.is_ui_ready or not hasattr(self.view, 'shelf_tab') or self.view.shelf_tab is None:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        
        # Cancel any previously scheduled redraw
        if self.resize_timer is not None:
            self.view.root.after_cancel(self.resize_timer)
            print("Cancelled previous resize timer")
        
        # Update scale factor
        new_width = self.view.shelf_tab.canvas.winfo_width()
        new_height = self.view.shelf_tab.canvas.winfo_height()
        initial_width = 1000
        initial_height = 600
        scale_width = new_width / initial_width
        scale_height = new_height / initial_height
        self.view.shelf_tab.scale_factor = min(scale_width, scale_height)
        print(f"Window resized: new width={new_width}, new height={new_height}, scale_factor={self.view.shelf_tab.scale_factor}")
        
        # Schedule a redraw after a 200ms delay to debounce the resize event
        self.resize_timer = self.view.root.after(200, self._perform_redraw)
        print("Scheduled redraw after 200ms")

    def _perform_redraw(self):
        """Perform the actual redraw of the shelf view after resizing."""
        print("Performing redraw after resize")
        self.update_shelf_view()
        self.resize_timer = None  # Clear the timer

    def start_selection(self, event):
        if not self.is_ui_ready or not hasattr(self.view, 'shelf_tab') or self.view.shelf_tab is None:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        # Check if any dropdown is empty
        section = self.view.shelf_tab.section_var.get()
        aisle = self.view.shelf_tab.aisle_var.get()
        side = self.view.shelf_tab.side_var.get()
        if not section or not aisle or not side:
            self.view.show_message("Warning", "Please select Section, Aisle, and Side values before interacting with the shelf.")
            return
        self.start_x = self.view.shelf_tab.canvas.canvasx(event.x)
        self.start_y = self.view.shelf_tab.canvas.canvasy(event.y)
        self.selection_rect = self.view.shelf_tab.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="blue", dash=(2, 2)
        )
        print(f"Started selection at ({self.start_x}, {self.start_y})")

    def update_selection(self, event):
        if not self.is_ui_ready or not hasattr(self.view, 'shelf_tab') or self.view.shelf_tab is None:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        # Check if any dropdown is empty
        section = self.view.shelf_tab.section_var.get()
        aisle = self.view.shelf_tab.aisle_var.get()
        side = self.view.shelf_tab.side_var.get()
        if not section or not aisle or not side:
            self.view.show_message("Warning", "Please select Section, Aisle, and Side values before interacting with the shelf.")
            return
        current_x = self.view.shelf_tab.canvas.canvasx(event.x)
        current_y = self.view.shelf_tab.canvas.canvasy(event.y)
        self.view.shelf_tab.canvas.coords(self.selection_rect, self.start_x, self.start_y, current_x, current_y)
        
        self.selected_cells.clear()
        for (level, shelf), (x1, y1, x2, y2) in self.view.shelf_tab.get_selection_coords().items():
            sel_x1, sel_y1, sel_x2, sel_y2 = self.view.shelf_tab.canvas.coords(self.selection_rect)
            if (min(sel_x1, sel_x2) <= x2 and max(sel_x1, sel_x2) >= x1 and
                min(sel_y1, sel_y2) <= y2 and max(sel_y1, sel_y2) >= y1):
                self.selected_cells.add((level, shelf))
                self.view.shelf_tab.highlight_shelf(level, shelf, "lightblue")
            else:
                self.view.shelf_tab.highlight_shelf(level, shelf, "#d3d3d3")
        print(f"Updated selection: {len(self.selected_cells)} cells selected")

    def end_selection(self, event):
        if not self.is_ui_ready or not hasattr(self.view, 'shelf_tab') or self.view.shelf_tab is None:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        # Check if any dropdown is empty
        section = self.view.shelf_tab.section_var.get()
        aisle = self.view.shelf_tab.aisle_var.get()
        side = self.view.shelf_tab.side_var.get()
        if not section or not aisle or not side:
            self.view.show_message("Warning", "Please select Section, Aisle, and Side values before interacting with the shelf.")
            return
        self.view.shelf_tab.canvas.delete(self.selection_rect)
        self.selection_rect = None
        self.start_x = None
        self.start_y = None
        print(f"Ended selection with {len(self.selected_cells)} cells selected")
        if self.selected_cells:
            if self.clear_values_mode:
                self.clear_selected_values()
                # Toggle off after one use
                self.clear_values_mode = False
                self.view.shelf_tab.clear_button.config(text="Clear Values: Off")
                print("Clear Values mode disabled after clearing")
            else:
                self.apply_selection()

    def clear_selected_values(self):
        """Clear Family and Category values for the selected shelves."""
        if not self.is_ui_ready or not hasattr(self.view, 'shelf_tab') or self.view.shelf_tab is None:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        section = self.view.shelf_tab.section_var.get()
        aisle = self.view.shelf_tab.aisle_var.get()
        side = self.view.shelf_tab.side_var.get()
        
        if not section or not aisle or not side:
            self.view.show_message("Warning", "Please select Section, Aisle, and Side values.")
            return
        
        try:
            aisle = int(aisle)
            side = int(side)
        except ValueError:
            self.view.show_message("Warning", "Invalid Aisle or Side value.")
            return
        
        updated_rows = 0
        for level, shelf in self.selected_cells:
            mask = (
                (self.model.df['Section'] == section) &
                (self.model.df['Aisle'] == aisle) &
                (self.model.df['Side'] == side) &
                (self.model.df['Level'] == level) &
                (self.model.df['Shelf'] == shelf)
            )
            row_idx = self.model.df.index[mask]
            if not row_idx.empty:
                row_idx = row_idx[0]
                self.model.df.at[row_idx, 'Family'] = ""
                self.model.df.at[row_idx, 'Category'] = ""
                updated_rows += 1
                print(f"Cleared row {row_idx}: Family and Category set to empty")
        
        print(f"Cleared Family and Category for {updated_rows} shelves")
        self.selected_cells.clear()
        self.update_shelf_view()

    def apply_selection(self):
        if not self.is_ui_ready or not hasattr(self.view, 'shelf_tab') or self.view.shelf_tab is None:
            self.view.show_message("Warning", "Please wait for the UI to fully initialize.")
            return
        section = self.view.shelf_tab.section_var.get()
        aisle = self.view.shelf_tab.aisle_var.get()
        side = self.view.shelf_tab.side_var.get()
        family = self.view.shelf_tab.family_var.get()
        category = self.view.shelf_tab.category_var.get()
        
        try:
            aisle = int(aisle)
            side = int(side)
        except ValueError:
            self.view.show_message("Warning", "Invalid Aisle or Side value.")
            return
        
        print(f"Applying selection with Section: {section}, Aisle: {aisle}, Side: {side}, Family: {family}, Category: {category}")
        success, message = self.model.apply_selection(self.selected_cells, section, aisle, side, family, category)
        # Only show message if there is an error
        if not success:
            self.view.show_message("Warning", message)
        if success:
            self.selected_cells.clear()
            self.update_shelf_view()
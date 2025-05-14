import pandas as pd
import os
from constants import FAMILY_FILE, SHELF_INFO_FILE, OUTPUT_FILE

class ShelfModel:
    def __init__(self):
        self.df = None
        self.families = []
        self.categories = {}  # Maps family to list of categories
        self.shelf_structure = {}  # Maps section to its configuration
        self.sections = []  # List of sections
        self.load_shelf_structure()  # Load shelf structure first
        self.load_data()

    def load_shelf_structure(self):
        """Load the shelf structure from the shelf information Excel file."""
        try:
            if not os.path.exists(SHELF_INFO_FILE):
                raise FileNotFoundError(f"Shelf information file not found: {SHELF_INFO_FILE}")
            
            # Read the shelf information Excel file
            # Assuming the first sheet contains the shelf structure with columns:
            # section, aisles, sides, levels max, shelves max
            df = pd.read_excel(SHELF_INFO_FILE, sheet_name=0)
            
            # Clean column names (remove spaces, convert to lowercase)
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Required columns
            required_columns = ['section', 'aisles', 'sides', 'levels_max', 'shelves_max']
            if not all(col in df.columns for col in required_columns):
                missing = [col for col in required_columns if col not in df.columns]
                raise ValueError(f"Shelf information Excel file missing required columns: {missing}")
            
            # Convert section to string and other columns to integers
            df['section'] = df['section'].astype(str)
            for col in ['aisles', 'sides', 'levels_max', 'shelves_max']:
                df[col] = df[col].astype(int)
            
            # Populate shelf_structure dictionary
            for _, row in df.iterrows():
                section = row['section']
                self.shelf_structure[section] = {
                    "aisles": row['aisles'],
                    "sides": row['sides'],
                    "max_levels": row['levels_max'],
                    "max_shelves": row['shelves_max']
                }
            
            # Populate sections list
            self.sections = list(self.shelf_structure.keys())
            print(f"Loaded shelf structure: {self.shelf_structure}")
            print(f"Sections: {self.sections}")
            
        except Exception as e:
            print(f"Error loading shelf structure: {str(e)}")
            raise

    def load_data(self):
        """Load data from the Excel files."""
        try:
            # Read the output file if it exists
            if os.path.exists(OUTPUT_FILE):
                self.df = pd.read_excel(OUTPUT_FILE)
                print(f"Read output file. Rows: {len(self.df)}")
                print(f"Columns in output file: {list(self.df.columns)}")
            else:
                # If the file doesn't exist, set df to None; it will be generated later
                self.df = None
                print(f"Output file {OUTPUT_FILE} does not exist. It will be generated if needed.")
            
            # Read family information to get families and categories
            xls = pd.ExcelFile(FAMILY_FILE)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(FAMILY_FILE, sheet_name=sheet_name)
                print(f"\nReading sheet: {sheet_name}")
                print(f"First few rows of the sheet:\n{df.head()}")
                
                # Read family name from cell A2 (row 2 in Excel, index 0 in pandas)
                family_row = 0
                family = str(df.iloc[family_row, 0]) if not pd.isna(df.iloc[family_row, 0]) else ""
                print(f"Family in cell A2 (row 2, index {family_row}): {family}")
                
                if family:
                    category_row = family_row
                    categories = df.iloc[category_row, 1:].dropna().tolist()
                    print(f"Raw categories in row 2 (B2 onward, index {category_row}): {categories}")
                    categories = [str(cat) for cat in categories]
                    print(f"Categories after converting to strings: {categories}")
                    
                    self.families.append(family)
                    self.categories[family] = categories
            print(f"\nFamilies loaded: {self.families}")
            print(f"Categories loaded: {self.categories}")
            
            # Ensure Family and Category columns exist if df is loaded
            if self.df is not None:
                if 'Family' not in self.df.columns:
                    self.df['Family'] = ""
                if 'Category' not in self.df.columns:
                    self.df['Category'] = ""
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            raise

    def save_data(self):
        """Save the updated data back to the Excel file."""
        try:
            self.df.to_excel(OUTPUT_FILE, index=False)
            print(f"Updated data saved to: {OUTPUT_FILE}")
            return True, f"Data saved successfully to {OUTPUT_FILE}"
        except Exception as e:
            print(f"Error saving data: {str(e)}")
            return False, f"Error saving data: {str(e)}"

    def apply_selection(self, selected_cells, section, aisle, side, family, category):
        """Apply the selected Family and Category to the selected shelves in the DataFrame."""
        if not section or not aisle or not side or not family or not category:
            return False, "Please select all dropdown values."
        
        if not selected_cells:
            return False, "Please select at least one shelf in the grid."
        
        updated_rows = 0
        for level, shelf in selected_cells:
            mask = (
                (self.df['Section'] == section) &
                (self.df['Aisle'] == int(aisle)) &
                (self.df['Side'] == int(side)) &
                (self.df['Level'] == level) &
                (self.df['Shelf'] == shelf)
            )
            row_idx = self.df.index[mask]
            if not row_idx.empty:
                row_idx = row_idx[0]
                self.df.at[row_idx, 'Family'] = family
                self.df.at[row_idx, 'Category'] = category
                updated_rows += 1
                print(f"Updated row {row_idx}: Family={family}, Category={category}")
        print(f"Applied Family: {family}, Category: {category} to {updated_rows} shelves")
        return True, f"Family and Category values applied to {updated_rows} shelves."

    def update_cell(self, row_id, column_name, value):
        """Update a specific cell in the DataFrame."""
        self.df.at[int(row_id), column_name] = value
        if column_name == "Family":
            self.df.at[int(row_id), "Category"] = ""  # Reset Category if Family changes
        return list(self.df.iloc[int(row_id)])

    def get_filtered_data(self, section, aisle, side):
        """Get filtered data for the selected Section, Aisle, and Side."""
        if not section or not aisle or not side:
            print(f"Cannot filter data: Section='{section}', Aisle='{aisle}', Side='{side}'")
            return None
        if self.df is None:
            print("Dataframe is not loaded.")
            return None
        filtered_df = self.df[
            (self.df['Section'] == section) &
            (self.df['Aisle'] == int(aisle)) &
            (self.df['Side'] == int(side))
        ]
        if filtered_df.empty:
            print(f"No data found for Section='{section}', Aisle='{aisle}', Side='{side}'")
            return None
        return filtered_df

    def get_unique_values(self, column):
        """Get unique values for a given column in the DataFrame."""
        if self.df is None or column not in self.df.columns:
            return []
        return sorted(self.df[column].unique().tolist())

    def generate_shelf_assignment(self):
        """Generate the shelf assignment output file based on shelf structure."""
        try:
            data = []
            for section, config in self.shelf_structure.items():
                aisles = config["aisles"]
                sides = config["sides"]
                max_levels = config["max_levels"]
                max_shelves = config["max_shelves"]
                
                for aisle in range(1, aisles + 1):
                    for side in range(1, sides + 1):
                        for level in range(1, max_levels + 1):
                            for shelf in range(1, max_shelves + 1):
                                data.append({
                                    'Section': section,
                                    'Aisle': aisle,
                                    'Side': side,
                                    'Level': level,
                                    'Shelf': shelf,
                                    'Family': '',
                                    'Category': ''
                                })
            
            # Create DataFrame and save to Excel
            output_df = pd.DataFrame(data)
            output_df.to_excel(OUTPUT_FILE, index=False)
            
            # Reload the data to update the model
            self.df = pd.read_excel(OUTPUT_FILE)
            if 'Family' not in self.df.columns:
                self.df['Family'] = ""
            if 'Category' not in self.df.columns:
                self.df['Category'] = ""
                
            print(f"Shelf assignment generated and saved to {OUTPUT_FILE}")
            return True, f"Shelf assignment generated and saved to {OUTPUT_FILE}"
        except Exception as e:
            print(f"Error generating shelf assignment: {str(e)}")
            return False, f"Error generating shelf assignment: {str(e)}"

    def get_shelf_structure(self):
        """Return the loaded shelf structure."""
        return self.shelf_structure

    def get_sections(self):
        """Return the list of sections."""
        return self.sections
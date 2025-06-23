
def tabulate_data_no_headers(data):
    """
    Tabulates data into columns with equal distance separation, without headers.

    This function calculates the maximum width required for each column
    based on the content, then formats the data using f-strings to ensure
    consistent spacing. It assumes the input `data` is a list of lists,
    where each inner list represents a row and has the same number of columns.

    Args:
        data (list of lists): The data to tabulate. Each inner list
            should represent a row, and all rows should have the same
            number of elements (columns).

    Returns:
        str: A multi-line string representing the tabulated data.
             Returns an empty string if data is empty or invalid.
    """

    if not data:
        return "" # Return empty string if no data

    # Determine the number of columns from the first row
    num_columns = len(data[0])
    if num_columns == 0:
        return "" # Return empty string if first row is empty

    # Initialize column widths with 0
    column_widths = [0] * num_columns

    # Calculate maximum width for each column based on data content
    for row_index, row in enumerate(data):
        if len(row) != num_columns:
            print(f"Warning: Row {row_index} has {len(row)} items, expected {num_columns}. Skipping this row.")
            continue # Skip rows that don't match the expected column count

        for col_index, cell_content in enumerate(row):
            column_widths[col_index] = max(column_widths[col_index], len(str(cell_content)))

    # Define the space between columns (can be adjusted)
    space_between_columns = 3

    # Construct the data rows
    data_lines = []
    for row_index, row in enumerate(data):
        if len(row) != num_columns:
            continue # Skip rows that were warned about earlier

        row_parts = []
        for col_index, cell_content in enumerate(row):
            # Use f-string to left-align and pad to the calculated width
            row_parts.append(f"{str(cell_content):<{column_widths[col_index]}}")
        data_lines.append((" " * space_between_columns).join(row_parts))

    return "\n".join(data_lines)

# --- Example Usage ---

# Example 1: Basic data
print("--- Example 1: Basic Data ---")
data1 = [
    ["Alice", 30, "New York"],
    ["Bob", 24, "Los Angeles"],
    ["Charlie", 35, "San Francisco"],
    ["David", 28, "Chicago"]
]
print(tabulate_data_no_headers(data1))
print("\n")

# Example 2: Data with varying string lengths
print("--- Example 2: Data with Varying String Lengths ---")
data2 = [
    ["Product A", 1200.00, True],
    ["Small Item", 25.50, False],
    ["Very Long Product Name Here", 75.99, True],
    ["Another Item", 450.00, True]
]
print(tabulate_data_no_headers(data2))
print("\n")

# Example 3: Empty data input
print("--- Example 3: Empty Data Input ---")
data3 = []
print(f"Output for empty data: '{tabulate_data_no_headers(data3)}'")
print("\n")

# Example 4: Data with integer and float types
print("--- Example 4: Data with Mixed Types ---")
data4 = [
    [1, 100, 10.5],
    [12, 5, 200.75],
    [345, 12345, 0.99]
]
print(tabulate_data_no_headers(data4))
print("\n")

# Example 5: Data with missing elements in a row (will skip warning)
print("--- Example 5: Data with Inconsistent Rows (Warning expected) ---")
data5 = [
    ["Item One", "Value One", "Detail One"],
    ["Item Two", "Value Two"], # This row has fewer columns
    ["Item Three", "Value Three", "Detail Three"]
]
print(tabulate_data_no_headers(data5))
print("\n")

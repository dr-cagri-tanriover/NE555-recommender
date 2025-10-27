
import json
from pathlib import Path

# -----------------------------------------------------------------------------
# FUNCTION: write_to_json_file
# -----------------------------------------------------------------------------
def write_to_json_file(filepath: str, data_to_write: dict = {}):
    """
    Creates the json file in filepath (overwrites it if exists) and writes the
    data_to_write to it.

    Args:
        filepath (str): Path to the JSON file to write (relative or absolute).
        data_to_write (dict): Dictionary data to write to JSON file.

    Returns:
        N/A
    """

    try:
        # Attempt to open the file in write mode with UTF-8 encoding.
        # This ensures support for non-ASCII characters in prompt files.
        file_path = Path(filepath)
        
        if not file_path.exists():
            # Creating a non-existent
            file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data_to_write, f, indent=4)

    except Exception as e:
        # Catch any exception (e.g. permission issues, IO errors) and print it.
        print(f"[ERROR] Failed to write to json file: {e}")

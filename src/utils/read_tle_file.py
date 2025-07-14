import pandas as pd

def read_tle_file(file_path):
    """
    Bare bones function to read a TLE file and return a DataFrame with the data.

    Example usage:
    file_path = "ALLAN_manual_2024-06-01_08-23-00_krag_LEO_D1_full.txt"
    df = read_tle_file(file_path)
    """
    with open(file_path, "r") as file:
        lines = file.readlines()
    
    tle_data = []
    
    for i in range(0, len(lines), 3):  # Each TLE set consists of three lines
        if i + 2 >= len(lines):
            break  # Ensure we don't go out of bounds
        
        name = lines[i].strip()[2:]  # Remove leading '0 '
        line1 = lines[i + 1].strip()
        line2 = lines[i + 2].strip()
        tle_id = line1.split()[1]  # Extract the satellite ID
        tle_data.append([name, tle_id, line1, line2])
    
    df = pd.DataFrame(tle_data, columns=["Name", "ID", "Line1", "Line2"])
    return df

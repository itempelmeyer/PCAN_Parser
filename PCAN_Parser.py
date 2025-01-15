# Reads PCAN trc files will output a csv file of all the CAN data in same folder as pathcl
# Made by Ian Tempelmeyer 7/29/2024 updated 1/10/2025 to self select file location and open at end of script.

import csv
import re
import os
from tkinter import Tk
from tkinter.filedialog import askopenfilename

def parse_can_id(can_id):
    can_id_int = int(can_id, 16)
    priority = (can_id_int >> 26) & 0x07
    reserved = (can_id_int >> 25) & 0x01
    data_page = (can_id_int >> 24) & 0x01
    pdu_format = (can_id_int >> 16) & 0xFF
    pdu_specific = (can_id_int >> 8) & 0xFF
    source_address = can_id_int & 0xFF

    if pdu_format >= 0xF0:
        pgn = (can_id_int >> 8) & 0xFFFF
        dest_address = pdu_specific
    else:
        pgn = (can_id_int >> 8) & 0xFFFF
        dest_address = 'All'

    return {
        'Priority': f'{priority:02X}',
        'Reserved': f'{reserved:01X}',
        'Data Page': f'{data_page:01X}',
        'PDU Format': f'{pdu_format:02X}',
        'PDU Specific': f'{pdu_specific:02X}',
        'PGN': f'{pgn:04X}',
        'Source Address': f'{source_address:02X}',
        'Destination Address': f'{dest_address:02X}' if dest_address != 'All' else 'All'
    }

def parse_trc_file(trc_file_path, csv_file_path):
    file_version = None
    with open(trc_file_path, 'r') as trc_file:
        for line in trc_file:
            if line.startswith(';$FILEVERSION='):
                file_version = line.split('=')[1].strip()
                break

    if file_version.startswith('1.3'):
        line_pattern = re.compile(r'^\s*\d+\)\s*([\d\.]+)\s+\d+\s+(Rx|Tx)\s+([0-9A-F]{8})\s*-\s*(\d+)\s+((?:[0-9A-F]{2}\s*){1,8})$')
    elif file_version.startswith('2.1'):
        line_pattern = re.compile(r'^\s*\d+\s+([\d\.]+)\s+DT\s+\d+\s+([0-9A-F]{8})\s+(Rx|Tx)\s*-\s*(\d+)\s+((?:[0-9A-F]{2}\s*){1,8})$')
    else:
        raise ValueError(f"Unsupported file version: {file_version}")

    # Debug print statements
    print(f"Reading from: {trc_file_path}")
    print(f"Writing to: {csv_file_path}")

    try:
        with open(trc_file_path, 'r') as trc_file, open(csv_file_path, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Timestamp', 'Direction', 'CAN ID', 'Priority', 'Reserved', 'Data Page', 'PDU Format', 'PDU Specific', 'PGN', 'Source Address', 'Destination Address', 'Data Length', 'Data Field 1', 'Data Field 2', 'Data Field 3', 'Data Field 4', 'Data Field 5', 'Data Field 6', 'Data Field 7', 'Data Field 8'])
            
            for line in trc_file:
                if line.startswith(';'):
                    continue
                
                match = line_pattern.match(line)
                if match:
                    # Commented out the debug print statements
                    # print(f"Matched line: {line.strip()}")
                    # print(f"Match groups: {match.groups()}")
                    
                    if file_version.startswith('1.3'):
                        timestamp, direction, can_id, data_length, data_fields = match.groups()
                    elif file_version.startswith('2.1'):
                        timestamp, can_id, direction, data_length, data_fields = match.groups()

                    data_fields = data_fields.split()
                    data_fields.extend([''] * (8 - len(data_fields)))

                    can_id_components = parse_can_id(can_id)
                    csv_writer.writerow([timestamp, direction, can_id,
                                        can_id_components['Priority'],
                                        can_id_components['Reserved'],
                                        can_id_components['Data Page'],
                                        can_id_components['PDU Format'],
                                        can_id_components['PDU Specific'],
                                        can_id_components['PGN'],
                                        can_id_components['Source Address'],
                                        can_id_components['Destination Address'],
                                        data_length] + data_fields[:8])
                else:
                    # Commented out the debug print statement
                    # print(f"Line did not match pattern: {line.strip()}")
                    pass
    except FileNotFoundError:
        print(f"Error: The file {trc_file_path} was NOT found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    Tk().withdraw()  # Hide the root window
    trc_file_path = askopenfilename(filetypes=[("TRC files", "*.trc")], title="Select a TRC file")
    
    if not trc_file_path:
        print("No file selected. Exiting.")
        exit()

    base_name = os.path.splitext(os.path.basename(trc_file_path))[0]
    csv_file_path = os.path.join(os.path.dirname(trc_file_path), base_name + '.csv')
    
    print(f"Processing: {trc_file_path}")
    print(f"Output file: {csv_file_path}")

    parse_trc_file(trc_file_path, csv_file_path)
    print(f"CSV file created: {csv_file_path}")

    # Open the folder where the CSV file was created
    os.startfile(os.path.dirname(csv_file_path))
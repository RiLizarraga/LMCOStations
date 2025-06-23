import datetime
import os

def save_lines_to_log(lines_to_log, filename="application_log.txt", timestamp_each_line=True):
    """
    Saves a list of text lines into a specified log file.

    If the file does not exist, it will be created. If it exists,
    new lines will be appended to the end of the file.

    Args:
        lines_to_log (list): A list of strings, where each string is a line to be logged.
        filename (str): The name of the text file to write to. Defaults to "application_log.txt".
        timestamp_each_line (bool): If True, a timestamp will be prepended to each line.
                                    Defaults to True.
    """
    try:
        # Open the file in append mode ('a'). If it doesn't exist, it will be created.
        with open(filename, 'a', encoding='utf-8') as log_file:
            for line in lines_to_log:
                if timestamp_each_line:
                    # Get current timestamp
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_file.write(f"[{timestamp}] {line}\n")
                else:
                    log_file.write(f"{line}\n")
        print(f"Successfully saved {len(lines_to_log)} lines to '{filename}'")

    except IOError as e:
        print(f"Error: Could not write to file '{filename}'. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Example Usage ---
if __name__ == "__main__":
    print("-" * 40)
    log_data_1 = [
        "************************************************",
        "***************** New sequence *****************",
        "************************************************"
    ]
    save_lines_to_log(log_data_1)
    line = "DESCRIPTION 123V 456 789"
    log_data_1 = [
        line
    ]
    save_lines_to_log(log_data_1)






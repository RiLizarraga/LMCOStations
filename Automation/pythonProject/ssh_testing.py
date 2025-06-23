from colorama import Fore, Style, init
import paramiko, datetime, enum, time, sys

###################
class Mode(enum.Enum):
    CONNECTION = 0,
    SEARCH = 1

col1_W = 36; col2_W = 20;provided_widths = [col1_W, col2_W]

###################

def tabulate_data_no_headers(data, column_widths=None):
    """
    Tabulates data into columns with equal distance separation, without headers.

    This function formats the data using f-strings to ensure consistent spacing.
    You can optionally provide a list of desired column widths. If not provided,
    the function will automatically calculate the maximum width required for each
    column based on the content. It assumes the input `data` is a list of lists,
    where each inner list represents a row and has the same number of columns.

    Args:
        data (list of lists): The data to tabulate. Each inner list
            should represent a row, and all rows should have the same
            number of elements (columns).
        column_widths (list of int, optional): A list of integers specifying
            the desired width for each column. If None, widths are calculated
            automatically based on content.

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

    # Validate provided column_widths or calculate them
    if column_widths is None:
        # Initialize column widths with 0
        calculated_column_widths = [0] * num_columns
        # Calculate maximum width for each column based on data content
        for row_index, row in enumerate(data):
            if len(row) != num_columns:
                print(f"Warning: Row {row_index} has {len(row)} items, expected {num_columns}. Skipping this row.")
                continue # Skip rows that don't match the expected column count

            for col_index, cell_content in enumerate(row):
                calculated_column_widths[col_index] = max(calculated_column_widths[col_index], len(str(cell_content)))
        final_column_widths = calculated_column_widths
    else:
        if len(column_widths) != num_columns:
            print(f"Warning: Provided column_widths length ({len(column_widths)}) does not match data columns ({num_columns}). Using automatic width calculation instead.")
            return tabulate_data_no_headers(data) # Recurse without provided widths
        final_column_widths = column_widths

    # Define the space between columns (can be adjusted)
    space_between_columns = 3

    # Construct the data rows
    data_lines = []
    for row_index, row in enumerate(data):
        if len(row) != num_columns:
            continue # Skip rows that were warned about earlier

        row_parts = []
        for col_index, cell_content in enumerate(row):
            # Use f-string to left-align and pad to the calculated/provided width
            # Ensure the content is truncated/padded correctly if it exceeds/falls short of the width
            formatted_content = str(cell_content)
            row_parts.append(f"{formatted_content:<{final_column_widths[col_index]}}")
        data_lines.append((" " * space_between_columns).join(row_parts))

    return "\n".join(data_lines)


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


def ping_via_ssh(hostname, port, username, password=None, key_filename=None, sudo=False, sudoPW='2114', mode=Mode.SEARCH, strPass="64 bytes",
                 command='ping -c 4 127.0.0.1'):
    """
    Connects to a remote host via SSH and executes a ping command.

    Args:
        hostname (str): The hostname or IP address of the SSH server.
        port (int): The port number for the SSH connection (default is 22).
        username (str): The username for SSH authentication.
        password (str, optional): The password for SSH authentication.
                                  Only use if key_filename is not provided.
        key_filename (str, optional): The path to the private key file for SSH authentication.
                                      Preferred method over password.
        command (str, optional): The command to execute on the remote host.
                                 Defaults to "ping -c 4 127.0.0.1" (ping 4 times).
    """
    Pass = False
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Automatically add the server's host key (use with caution in production)
    print(f"Attempting to connect to {username}@{hostname}:{port}...")
    try:
        if key_filename:
            ssh_client.connect(hostname=hostname, port=port, username=username, key_filename=key_filename) # Use key-based authentication
        else:
            ssh_client.connect(hostname=hostname, port=port, username=username, password=password)  # Use password-based authentication

        print("SSH connection established successfully.")
        if mode == Mode.CONNECTION:
            Pass = True
        print(f"Executing command: '{command}' on the remote host...")
        # Execute the command
        stdin, stdout, stderr = ssh_client.exec_command(command, get_pty=sudo)



        if sudo:
            stdin.write(sudoPW + '\n')
            stdin.flush()

        # Read output from stdout
        print("\n--- Command Output (stdout) ---")

        for line in stdout:
            print("\t"+line.strip())
            if mode == Mode.SEARCH:
                if strPass in line:
                    Pass = True
                    str1 = strPass+" found"
                    print(f"{Fore.GREEN}"+str1)
                    print(f"{Fore.WHITE} {Style.RESET_ALL}")
                    break

        # Read output from stderr (if any errors occurred)
        error_output = stderr.read().decode().strip()
        if error_output:
            print("\n--- Error Output (stderr) ---")
            print(error_output)

    except paramiko.AuthenticationException:
        print("Authentication failed. Please check your username and password/key.")
    except paramiko.SSHException as e:
        print(f"Could not establish SSH connection: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if ssh_client:
            ssh_client.close()
            print("\nSSH connection closed.")
    return Pass

def exec(DESCRIPTION, SSH_HOSTNAME, SSH_USERNAME, SSH_PASSWORD, SSH_PORT, CMD, SUDO, SUDOPW, MODE, STRPASS ):
    PassFail = False
    print("--- Running "+DESCRIPTION+" ---")
    result = ping_via_ssh(hostname=SSH_HOSTNAME,port=SSH_PORT,username=SSH_USERNAME,password=SSH_PASSWORD,
                          sudo=SUDO, sudoPW=SUDOPW, mode=MODE, strPass=STRPASS, command=CMD )
    test_result = "Pass" if result else "Fail"
    raw = [ [DESCRIPTION, test_result] ]
    line = tabulate_data_no_headers(raw, provided_widths)
    print("*** ["+line+"] ***")
    log_data = [ line ];save_lines_to_log(log_data)

    return PassFail

####################################################################################################################
# "ping -c 1 -i 2 -w 10 "+"127.0.0.1" ## (-c 4) = Ping localhost 4 times, (-i 2)=every 2 seconds,(-w 10)=timeout 10 sec
if __name__ == "__main__":
    print("-" * 40)
    log_data = [
        "",
        "***********************************************************",
        "********************** New sequence ***********************",
        "***********************************************************"
    ]
    save_lines_to_log(log_data)

    raw = [ ["DESCRIPTION", "RESULTS"] ]
    line = tabulate_data_no_headers(raw, provided_widths)
    log_data = [ line ];save_lines_to_log(log_data)

    raw = [ ["-----------------------------------", "--------------------"] ]
    line = tabulate_data_no_headers(raw, provided_widths)
    log_data = [ line ];save_lines_to_log(log_data)
    # ( 1 ) -----------------------------------------------------
    DESCRIPTION = "( 1 ) 5GC EN: ping "+"127.0.0.1";SSH_HOSTNAME = "172.25.32.132";SSH_USERNAME = "ricardo";SSH_PASSWORD = "2114";SSH_PORT = 22
    sudo = False;sudoPW='2114';mode=Mode.SEARCH;strPass="";CMD = "ping -c 1 -i 2 -w 10 "+"127.0.0.1"
    ret = exec(DESCRIPTION,SSH_HOSTNAME,SSH_USERNAME,SSH_PASSWORD,SSH_PORT,CMD,sudo,sudoPW,mode,strPass)

    # ( 2 ) -----------------------------------------------------
    DESCRIPTION = "( 2 ) 5GC EN: docker container ls";SSH_HOSTNAME = "172.25.32.132";SSH_USERNAME = "ricardo";SSH_PASSWORD = "2114";SSH_PORT = 22
    sudo = True;sudoPW='2114';mode=Mode.SEARCH;strPass="alpine";CMD = "sudo docker container ls"
    ret = exec(DESCRIPTION,SSH_HOSTNAME,SSH_USERNAME,SSH_PASSWORD,SSH_PORT,CMD,sudo,sudoPW,mode,strPass)

    # ( 3 ) -----------------------------------------------------
    DESCRIPTION = "( 3 ) MR RAN: ping "+"127.0.0.1";SSH_HOSTNAME = "172.25.32.132";SSH_USERNAME = "ricardo";SSH_PASSWORD = "2114";SSH_PORT = 22
    sudo = False;sudoPW='2114';mode=Mode.SEARCH;strPass="";CMD = "ping -c 1 -i 2 -w 10 "+"127.0.0.1"
    ret = exec(DESCRIPTION,SSH_HOSTNAME,SSH_USERNAME,SSH_PASSWORD,SSH_PORT,CMD,sudo,sudoPW,mode,strPass)






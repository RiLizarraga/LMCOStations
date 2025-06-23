from colorama import Fore, Style, init
import paramiko
import time

# SSH connection details
hostname = '172.25.32.132' #'your.server.com'    # or IP address like '192.168.1.10'
port = 22
username = 'ricardo'
password = '2114'      # or use a private key instead

try:
    # Create SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # auto-add host key

    # Connect to the server
    client.connect(hostname, port=port, username=username, password=password)

    print(f"Connected to {hostname}")

    # Run a command
    #stdin, stdout, stderr = client.exec_command('ping 227.0.0.1') #'uname -a','ls -ltr'

    # Search
    sub_str = "Music"
    print("Output:")
    found = False

    while True:
        stdin, stdout, stderr = client.exec_command('ping 127.0.0.1')  # 'uname -a','ls -ltr'
        output = stdout.read().decode()
        error = stderr.read().decode()
        print(output)
        print(error)
        for line in stdout:
            print(line.strip())
            if sub_str in line:
                found = True
                str1 = sub_str+" found"
                print(f"{Fore.GREEN}"+str1)
                print(f"{Fore.WHITE} {Style.RESET_ALL}")

        time.sleep(0.5)

    if not found:
        print(f"{Fore.RED}{Style.BRIGHT} Not found{Style.RESET_ALL}")


    # Close connection
    client.close()

except Exception as e:
    print(f"Failed to connect: {e}")

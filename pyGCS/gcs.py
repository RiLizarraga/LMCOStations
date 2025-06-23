import sys, serial, threading, time, os
import random
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,QCheckBox)
from PyQt5.QtCore import Qt, QTimer,pyqtSignal,QObject,QThread,QDate,QTime
from PyQt5.QtWidgets import QPushButton, QDialog, QGroupBox,QComboBox, QHBoxLayout, QVBoxLayout, QGridLayout, \
    QScrollArea, QTextEdit, QMessageBox, QLabel, QSizePolicy
from PyQt5.QtGui import QTextCursor, QFont,QColor, QPalette

auto = False
port = 'COM17'#12/17
baudrate = 115200


# Globals
serial_connection = None
receive_thread = None
send_thread = None
thr_running = False
serial_port = None
tower = 1
rotation_mode = False
tower_curr = 1
max_tower = 4
cmd ="idn?"
dly_cmd = 200
dly_comm = 2000

rssi = 0
station = "-"
idn = "-"
sync_flg = True
filename = "GCS_data.csv" ####saving data to a file
Sequence_script = "Sequence_Script_1.txt"
def load_string_from_file(filepath):
    """
    Loads the entire content of a text file into a single string.

    Args:
        filepath (str): The path to the text file.

    Returns:
        str: The content of the file as a string.  Returns an empty string
             if the file does not exist or an error occurs.
    """
    try:
        with open(filepath, 'r') as file:
            # Read the entire content of the file
            file_content = file.read()
            return file_content
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return ""  # Return empty string for file not found
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return "" # Return empty string for other errors
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
def save_string_line(filename, line, append=True):
    # 1. Input Validation
    if not isinstance(filename, str):
        raise TypeError(f"filename must be a string, not {type(filename).__name__}")
    if not isinstance(line, str):
        raise TypeError(f"line must be a string, not {type(line).__name__}")
    if not isinstance(append, bool):
        raise TypeError(f"append must be a bool, not {type(append).__name__}")

    mode = "a" if append else "w"  # Determine the file open mode
    try:
        with open(filename, mode) as file:
            # 3. Write Line
            file.write(line + "\n")  # Add newline character
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")
        return

    print(f"Line saved to {filename} (append={append}): {line}")
def build_cmd():
    global cmd,tower,dly_cmd,tower_curr,max_tower
    if rotation_mode:
        if tower_curr > max_tower:
            tower_curr = 1

    strcmd = cmd+","+ str(tower_curr)+ ","+str(dly_cmd)
    if rotation_mode:
        tower_curr = tower_curr + 1

    return strcmd
def build_cmd_line(msg,twr):
    global dly_cmd
    return msg+","+ str(twr)+ ","+str(dly_cmd)
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def breakdownfields(_str):
    section = _str.split("@")
    testing = section[1].split(",")
    return int(testing[0]),int(testing[1]),testing[2]

def comparevalues(_rx,_from,_to, _ref):
    if _rx[_from:_to] == _ref:
        return "o"
    else:
        return "error: rx = "+_rx[_from:_to]+" DIFFERENT TO "+_ref
class GGCCSS(QWidget):
    eventlogInt = pyqtSignal(int)
    eventlogStr = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GCS")
        #self.setGeometry(100, 100, 300, 200)
        self.left = 200
        self.top = 100
        self.width = 2800
        self.height = 2000
        self.setGeometry(self.left, self.top, self.width, self.height)
        #####self.iconName = "???????????????????.PNG"

        self.main_layout = QVBoxLayout()
        self.h_layout0 = QHBoxLayout()
        self.h_layout1 = QHBoxLayout()  # Cmd controls
        self.h_layout2 = QHBoxLayout()   #Create a horizontal layout for buttons

        self.voltage_label = QLabel("G r o u n d    C o n t r o l    S t a t i o n")
        self.voltage_label.setAlignment(Qt.AlignCenter)
        self.voltage_label.setStyleSheet("font-size: 68px;font-weight: bold;italic;")
        self.main_layout.addWidget(self.voltage_label)

        self.unit_label = QLabel("System configuration, verification, regression test, POST (Power On Self Test) and readiness")
        self.unit_label.setAlignment(Qt.AlignCenter)
        self.unit_label.setStyleSheet("font-size: 36px;")
        self.main_layout.addWidget(self.unit_label)

        self.value_label = QLabel("-.-- dBm")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 65px; font-weight: bold;color: green; background-color: black;")
        self.palette1 = self.value_label.palette()
        self.palette1.setColor(QPalette.WindowText, QColor("green"))
        self.value_label.setPalette(self.palette1)

        self.main_layout.addWidget(self.value_label)
        #
        self.label1 = QLabel("         ", self)
        self.label1.setAlignment(Qt.AlignCenter)
        self.label1.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.label2 = QLabel("Select", self)
        self.label2.setAlignment(Qt.AlignCenter)
        self.label2.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.label3 = QLabel("Command", self)
        self.label3.setAlignment(Qt.AlignCenter)
        self.label3.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.label4 = QLabel("Rx delay (mS)", self)
        self.label4.setAlignment(Qt.AlignCenter)
        self.label4.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.label5 = QLabel("Timer (mS)", self)
        self.label5.setAlignment(Qt.AlignCenter)
        self.label5.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.h_layout0.addWidget(self.label1)
        self.h_layout0.addWidget(self.label2)
        self.h_layout0.addWidget(self.label3)
        self.h_layout0.addWidget(self.label4)
        self.h_layout0.addWidget(self.label5)
        self.main_layout.addLayout(self.h_layout0)  #

        # Label
        self.label = QLabel("-", self)
        self.label.setStyleSheet("font-size: 48px; font-weight: bold;")
        #self.main_layout.addWidget(self.label)
        self.h_layout1.addWidget(self.label)
        # ComboBox1
        self.combo1 = QComboBox(self)
        self.combo1.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.combo1.addItems(["Ground Control Station","Tower # 1", "Tower # 2", "Tower # 3", "Tower # 4"])
        self.combo1.setCurrentIndex(tower)
        #self.main_layout.addWidget(self.combo1)
        self.h_layout1.addWidget(self.combo1)
        self.combo1.currentIndexChanged.connect(self.on_combobox1_changed) # Connect event
        # ComboBox2
        self.combo2 = QComboBox(self)
        self.combo2.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.combo2.addItems(["idn?","rssi?", "dl?", "ul?", "rec?","adc?","rly?","dout?"])
        self.combo2.setCurrentIndex(0)
        #self.main_layout.addWidget(self.combo2)
        self.h_layout1.addWidget(self.combo2)
        self.combo2.currentIndexChanged.connect(self.on_combobox2_changed) # Connect event
        # ComboBox3
        self.combo3 = QComboBox(self)
        self.combo3.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.combo3.addItems(["0","50", "80", "150", "200", "250", "300", "400"])
        self.combo3.setCurrentIndex(4)
        #self.main_layout.addWidget(self.combo3)
        self.h_layout1.addWidget(self.combo3)
        self.combo3.currentIndexChanged.connect(self.on_combobox3_changed) # Connect event
        # ComboBox4
        self.combo4 = QComboBox(self)
        self.combo4.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.combo4.addItems(["0", "50", "250", "500", "650", "750", "1000", "2000", "10000"])
        self.combo4.setCurrentIndex(7)
        #self.main_layout.addWidget(self.combo4)
        self.h_layout1.addWidget(self.combo4)
        self.combo4.currentIndexChanged.connect(self.on_combobox4_changed)  # Connect event
        self.main_layout.addLayout(self.h_layout1)  # Add the horizontal layout
        ##
        self.logOutput = QTextEdit()
        self.logOutput.setReadOnly(True)
        self.logOutput.setLineWrapMode(QTextEdit.NoWrap)
        self.font = QFont("Consolas", 18)
        self.font.setStyleHint(QFont.TypeWriter)
        self.logOutput.setCurrentFont(self.font)
        self.logOutput.setStyleSheet("background-color: black;")
        self.logOutput.setTextColor(QColor(255, 0, 0))  # Use QColor for RGB
        self.main_layout.addWidget(self.logOutput)
        ##
        self.checkbox = QCheckBox("Auto/ manual")
        self.checkbox.setChecked(False)
        self.checkbox.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.checkbox.stateChanged.connect(self.checkbox_changed)

        self.checkbox2 = QCheckBox("Rotation Mode")
        self.checkbox2.setChecked(False)
        self.checkbox2.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.checkbox2.stateChanged.connect(self.checkboxRotation_changed)

        self.buttonSTOP = QPushButton("STOP", self)
        self.buttonSTOP.setMinimumHeight(30)
        self.buttonSTOP.setMaximumHeight(52)
        self.buttonSTOP.setStyleSheet("color: red; background-color: white;")
        self.buttonSTOP.clicked.connect(self.clicked_STOP)
        self.buttonSTOP.setFont(QFont('Times', 11, QFont.Bold))
        self.buttonSTOP.setEnabled(True)
        ##
        self.button1 = QPushButton("Continuous Query", self)
        self.button1.setMinimumHeight(30)
        self.button1.setMaximumHeight(52)
        self.button1.setStyleSheet("color: green; background-color: white;")
        self.button1.clicked.connect(self.clicked_GCS1)
        self.button1.setFont(QFont('Times', 11, QFont.Bold))
        self.button1.setEnabled(True)

        self.button2 = QPushButton("Run a sequence", self)
        self.button2.setMinimumHeight(30)
        self.button2.setMaximumHeight(52)
        self.button2.setStyleSheet("color: green; background-color: white;")
        self.button2.clicked.connect(self.clicked_GCS2)
        self.button2.setFont(QFont('Times', 11, QFont.Bold))
        self.button2.setEnabled(True)

        self.h_layout2.addWidget(self.checkbox)
        self.h_layout2.addWidget(self.checkbox2)
        self.h_layout2.addWidget(self.buttonSTOP)
        self.h_layout2.addWidget(self.button1)
        self.h_layout2.addWidget(self.button2)
        self.main_layout.addLayout(self.h_layout2)  # Add the horizontal layout 2
        ####
        self.setLayout(self.main_layout)
        self.timer1 = QTimer(self)
        self.timer1.timeout.connect(self.update_rssi)
    def logInt(self, val):
        self.logOutput.insertPlainText(str(val) + "\n")
    def startSRThread_GCS1(self):
        self.SRThread_GCS1 = SRThread_GCS1()
        self.SRThread_GCS1.eventlogInt.connect(self.logInt)
        self.SRThread_GCS1.eventlogStr.connect(self.logStr)
        self.SRThread_GCS1.start()
    def startSRThread_GCS2(self):
        self.SRThread_GCS2 = SRThread_GCS2()
        self.SRThread_GCS2.eventlogInt.connect(self.logInt)
        self.SRThread_GCS2.eventlogStr.connect(self.logStr)
        self.SRThread_GCS2.start()
    def clicked_GCS1(self):
        global thr_running
        thr_running = True
        self.logStr("...Started Continuous Query Thread")
        self.startSRThread_GCS1()
    def clicked_GCS2(self):
        global thr_running
        thr_running = True
        self.logStr("...Started Sequence execution Thread")
        self.startSRThread_GCS2()

    def clicked_STOP(self):
        global thr_running
        thr_running = False
        self.logStr("...Stop all threads")

    def logStr(self, val):  # self.logOutput.moveCursor(QTextCursor.End)
        # self.logOutput.moveCursor(QTextCursor.End)
        # self.logOutput.insertPlainText(str(val) + "\n")
        self.logOutput.append(str(val))
        print(val + '\n')
    def on_combobox1_changed(self, index): #tower #
        global tower
        selected_text = self.combo1.itemText(index)
        self.label.setText(f"Selected: {selected_text}")
        print(f"Combo box changed to index {index}: {selected_text}")
        tower = index
    def on_combobox2_changed(self, index):
        global cmd
        selected_text = self.combo2.itemText(index)
        self.label.setText(f"Selected: {selected_text}")
        print(f"Combo box changed to index {index}: {selected_text}")
        cmd = selected_text
    def on_combobox3_changed(self, index):
        global dly_cmd
        selected_text = self.combo3.itemText(index)
        self.label.setText(f"Selected: {selected_text}")
        print(f"Combo box changed to index {index}: {selected_text}")
        dly_cmd = int(selected_text)
    def on_combobox4_changed(self, index): #timer delay
        global dly_comm
        selected_text = self.combo4.itemText(index)
        self.label.setText(f"Selected: {selected_text}")
        print(f"Combo box changed to index {index}: {selected_text}")
        dly_comm = int(selected_text)
    def checkbox_changed(self, state):
        global auto,sync_flg
        print("sync_flg = " + str(sync_flg))
        sync_flg = True
        if state == Qt.Checked:
            auto = True
            mf.timer1.start(dly_comm)
        else:
            auto = False
            mf.timer1.stop()

    def checkboxRotation_changed(self, state):
        global rotation_mode
        if state == Qt.Checked:
            rotation_mode = True
        else:
            rotation_mode = False
        print("rotation_mode = " + str(rotation_mode))

    def update_rssi(self):
        global serial_port
        """Generates a random voltage value and updates the display."""
        #voltage = random.uniform(0.0, 15.0)  # Generate random voltage between 0.0 and 15.0
        self.value_label.setText(f"{rssi:.0f} dBm")

# GCS1 ///////////////////////////////////////////////////////////////////////////////////
class SRThread_GCS1(QThread):
    eventlogInt = pyqtSignal(int)
    eventlogStr = pyqtSignal(str)
    global serial_connection, receive_thread, send_thread, rssi, station, RMODE,thr_running
    thr_running = True
    def receive_data(self):
        global serial_connection, receive_thread, send_thread, rssi, station, RMODE,filename,sync_flg
        """Continuously reads data from the serial port and prints it."""
        while thr_running:
            try:
                if serial_connection.in_waiting > 0:
                    received_bytes = serial_connection.readline()  # Read until newline (\n)
                    print("setting sync_flg!")
                    sync_flg = True
                    # received_bytes = serial_port.read(serial_port.in_waiting)
                    try:
                        received_text = received_bytes.decode('utf-8').strip()
                        print(f"{received_text}")
                        if len(received_text) > 0 and (is_number(received_text)):  # rssi = float(received_text) if (received_text.isnumeric()) else rssi #a if a > b else b
                            rssi = float(received_text)
                            self.logRow(received_text)
                        elif len(received_text) > 0:        # and RMODE == 2:
                            self.logRow(received_text)
                            try:
                                open(filename, 'a').close()
                            except Exception as e:
                                print(f"Error creating file: {e}")
                            fields = received_text.split(',')
                            num_fields = len(received_text.split(','))
                            if num_fields == 7:
                                save_string_line(filename, received_text, append=True)
                                # send "ACK"

                                text_to_send = build_cmd_line("ack",fields[1]) + "\r\n"
                                serial_connection.write(text_to_send.encode('utf-8'))
                                serial_connection.flush()
                                print(f"Sent: {text_to_send}")


                    except UnicodeDecodeError:
                        print(f"Received non-UTF-8 data: {received_bytes}")
            except serial.SerialException as e:
                print(f"Error reading from serial port: {e}")
                break
            time.sleep(0.1)  # Small delay to avoid busy-waiting
        serial_connection.close()
        print("serial_connection: Closed")

    def send_data(self):
        global serial_connection, receive_thread, send_thread, rssi, station, RMODE,auto,sync_flg
        """Continuously prompts the user for input and sends it over the serial port."""
        while thr_running:
            if auto:
                try:
                    if sync_flg:
                        serial_connection.reset_output_buffer()
                        serial_connection.reset_input_buffer()
                        serial_connection.flushInput()
                        serial_connection.flushOutput()
                        text_to_send = build_cmd() + "\r\n"
                        serial_connection.write(text_to_send.encode('utf-8'))
                        if text_to_send[:3]=="ack":
                            sync_flg = True
                        else:
                            sync_flg = False
                        serial_connection.flush()
                        print(f"Sent: {text_to_send}")
                        time.sleep(dly_comm/1000)
                        print("Clearing flag when cmd: "+ text_to_send)
                except serial.SerialException as e:
                    print(f"Error writing to serial port: {e}")
                    break
            else:
                time.sleep(1)

        print("Sending thread stopped.")
        serial_connection.close()

    def logRow(self, txt):
        self.eventlogStr.emit(txt)#strTS()

    def run(self): ## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ##
        #global filename
        print("GCS ... started\n")

        print("\n--- File Contents ---")
        try:
            with open(filename, "r") as file:
                print(file.read())
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
        except Exception as e:
            print(f"An error occurred reading the file: {e}")
        ####

        global serial_connection,receive_thread,send_thread
        try:
            serial_connection = serial.Serial(port, baudrate, timeout=3)
            time.sleep(0.6)
            print(f"Connected to {port} at {baudrate} bps")
            self.logRow("Connected to serial port ...ok\n")

            # Create and start the receiver thread
            receive_thread = threading.Thread(target=self.receive_data)
            receive_thread.daemon = True  # Allow main thread to exit even if this is running
            receive_thread.start()
            print("Receive thread active\n")

            # Create and start the sender thread
            send_thread = threading.Thread(target=self.send_data, args=serial_connection)
            send_thread.start()
            print("Sending thread active\n")
            send_thread.join()  # Wait for the sending thread to finish (when user enters 'quit')

        except serial.SerialException as e:
            print(f"Error opening serial port {port}: {e}")
            self.logRow("Error opening serial port !!!\n")
        finally:
            if serial_connection and serial_connection.is_open:
                # serial_connection.close();print(f"Closed serial port {port}")
                print(f"Keep serial port {port} open")

        time.sleep(1)
        #**********************************************************
        self.logRow("Thread ended\n")

# GCS2 ///////////////////////////////////////////////////////////////////////////////////
def wait_for_newline():
    global serial_connection
    timeout = None
    try:
        received_data = b""  # Use bytes for serial data
        while True:
            byte = serial_connection.read(1)  # Read one byte at a time
            if byte == b"":
                if timeout is not None:
                    print("Timeout occurred while waiting for data.")
                    serial_connection.close()
                    return None
                else:
                    continue  # no timeout, keep reading

            received_data += byte
            if byte == b'\n':
                break  # Exit loop when newline is received
        # Decode the received bytes into a string (remove the newline character)
        return received_data.decode('utf-8').rstrip('\n').rstrip('\r')

    except serial.SerialException as e:
        print(f"Error reading from serial port {port}: {e}")
        serial_connection.close()
        return None

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        serial_connection.close()
        return None

    finally:
        print(f"done receiving")
        # 3. Close the serial port
        ##serial_connection.close()
        ##print(f"Serial port {port} closed.")


class SRThread_GCS2(QThread):
    eventlogInt = pyqtSignal(int)
    eventlogStr = pyqtSignal(str)
    global serial_connection, receive_thread, send_thread, rssi, station, RMODE,thr_running
    thr_running = True
    def logRow(self, txt):
        self.eventlogStr.emit(txt)#strTS()
    def run(self): ## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ##
        global Sequence_script
        global serial_connection,receive_thread,send_thread
        loaded_string = load_string_from_file(Sequence_script)
        try:
            serial_connection = serial.Serial(port, baudrate, timeout=3)
            serial_connection.flushOutput()
            serial_connection.flushInput()
            serial_connection.reset_output_buffer()
            serial_connection.reset_input_buffer()
            time.sleep(0.6)
            print(f"Connected to {port} at {baudrate} bps")
            fields = loaded_string.split("\n")
            for item in fields:
                item = item.replace(" ", "").replace("\t", "").replace("\n", "").replace("\r", "")
                print("isnumeric?{" + item+"}")
                if is_number(item):
                    print("delay (Sec) : "+item)
                    #self.logRow("delay (Sec) : "+item)
                    time.sleep(float(item))
                elif len(item)>0:
                    text_to_send = item + "\r\n"
                    self.logRow(item)
                    #print("item<" + item + ">")
                    serial_connection.write(text_to_send.encode('utf-8'))
                    serial_connection.flush()
                    if text_to_send[:3] == "ack":
                        sync_flg = True
                    else:
                        sync_flg = False
                    print(f"Sent: {text_to_send}")
                    received_text = wait_for_newline()
                    print(received_text)
                    self.logRow("\t\t"+received_text)
                    sync_flg = True

            #serial_connection.close()

        except serial.SerialException as e:
            print(f"Error opening serial port {port}: {e}")
        finally:
            #serial_connection.close()
            if serial_connection and serial_connection.is_open:
                # serial_connection.close();print(f"Closed serial port {port}")
                serial_connection.close()
                print(f"Keep serial port {port} open")

        time.sleep(1)
        #**********************************************************
        self.logRow("Thread ended\n")

# Wrap up ////////////////////////////////////////////////////////
if __name__ == '__main__':
    app = QApplication(sys.argv)
    mf = GGCCSS()
    mf.show()
    sys.exit(app.exec_())
    send_thread.join()
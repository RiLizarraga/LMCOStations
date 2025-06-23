import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton
from PyQt5.QtCore import QThread, pyqtSignal, QObject
import time

class Worker(QObject):
    """
    Worker class to perform the text update in a separate thread.
    Inherits from QObject, not QThread.  This is the modern, preferred way.
    """
    finished = pyqtSignal()  # Signal emitted when the task is finished
    textChanged = pyqtSignal(str) # Signal to send text updates

    def __init__(self, text_to_send, delay=1, parent=None):
        super().__init__(parent)
        self.text_to_send = text_to_send
        self.delay = delay

    def run(self):
        """
        The main method that gets executed when the thread starts.
        """
        for i, char in enumerate(self.text_to_send):
            time.sleep(self.delay)  # Simulate some processing delay
            # Emit the signal with the updated text.  We send one *character*
            # at a time, to show how the text edit can be updated
            # incrementally.
            self.textChanged.emit(char)
        self.finished.emit()  # Emit the finished signal when done

class MyWidget(QWidget):
    """
    Main widget containing the QTextEdit and the button.
    """
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        """
        Sets up the user interface.
        """
        layout = QVBoxLayout()

        self.textEdit = QTextEdit()
        layout.addWidget(self.textEdit)

        self.startButton = QPushButton("Start Thread")
        self.startButton.clicked.connect(self.startThread)
        layout.addWidget(self.startButton)

        self.setLayout(layout)
        self.setWindowTitle("PyQt5 Threaded TextEdit Update")
        self.setGeometry(300, 300, 400, 300)

        self.worker_thread = None # No thread initially
        self.worker_object = None

    def startThread(self):
        """
        Starts the worker thread.
        """
        if self.worker_thread is not None:
            # Optionally, you might want to have a way to stop the previous
            # thread before starting a new one.  For simplicity here, we
            # just prevent starting a new one if one is already running.
            print("Thread already running!")
            return

        self.startButton.setEnabled(False)  # Disable button during processing
        self.textEdit.clear() # Clear any previous text

        # Create a QThread instance.
        self.worker_thread = QThread()
        # Create a worker object.  *This* object (not the thread itself)
        # does the work.
        self.worker_object = Worker("Hello from the other thread!  Updating live.", delay=0.1) # added delay
        # Move the worker object to the thread.  This is crucial.
        self.worker_object.moveToThread(self.worker_thread)

        # Connect signals and slots.
        # When the thread starts, start the worker's run method.
        self.worker_thread.started.connect(self.worker_object.run)
        # When the worker finishes, tell the thread to quit, and then
        # clean up.
        self.worker_object.finished.connect(self.worker_thread.quit)
        self.worker_object.finished.connect(self.worker_object.deleteLater)  # Clean up worker object
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)    # Clean up thread object
        self.worker_object.textChanged.connect(self.updateTextEdit) # connect the signal

        # Start the thread.
        self.worker_thread.start()

    def updateTextEdit(self, new_text):
        """
        Slot to update the QTextEdit with new text.  This runs in the *main*
        thread, so it's safe to update the GUI.
        """
        # Append the new character.
        self.textEdit.insertPlainText(new_text)

    def threadFinished(self):
        """
        Slot to handle thread completion.  This also runs in the main thread.
        """
        self.startButton.setEnabled(True)  # Re-enable the button
        print("Thread finished!")
        self.worker_thread = None # Clean up
        self.worker_object = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = MyWidget()
    widget.show()
    sys.exit(app.exec_())

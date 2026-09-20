import sys
from PyQt6.QtWidgets import QApplication, QFileDialog
app = QApplication(sys.argv)
filters = "All Files (*.*);;Text Files (*.txt)"
try:
    # QFileDialog might need a real parent or None.
    print(QFileDialog.getOpenFileName(None, "Open File", "", filters))
except Exception as e:
    print("ERROR:", e)

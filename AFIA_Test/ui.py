import tkinter as tk
from detection import run_inspection

class InspectionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Inspection App")
        self.geometry("300x150")

        self.start_btn = tk.Button(self, text="Start Inspection", command=self.start_inspection)
        self.start_btn.pack(pady=40)

    def start_inspection(self):
        # Disable button to prevent re-entry
        self.start_btn.config(state=tk.DISABLED)

        # Run inspection (opens OpenCV window, prints to console)
        run_inspection()

        # Re-enable button when done
        self.start_btn.config(state=tk.NORMAL)

if __name__ == '__main__':
    app = InspectionApp()
    app.mainloop()
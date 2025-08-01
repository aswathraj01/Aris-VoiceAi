import tkinter as tk
from tkinter import StringVar

class ArisUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Aris Assistant")
        self.root.geometry("300x150")
        self.root.configure(bg="black")

        self.status_text = StringVar()
        self.status_text.set("Initializing...")

        self.label = tk.Label(self.root, textvariable=self.status_text, font=("Helvetica", 16), fg="cyan", bg="black")
        self.label.pack(expand=True)

    def update_status(self, message):
        self.status_text.set(message)
        self.root.update()

    def run(self):
        self.root.mainloop()

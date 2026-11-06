import customtkinter as ctk
from tkinterdnd2 import TkinterDnD
from gui import MP3NormalizerApp

def main():
    root = ctk.CTk()
    TkinterDnD.require(root)
    app = MP3NormalizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

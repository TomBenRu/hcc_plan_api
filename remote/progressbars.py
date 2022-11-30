import tkinter as tk
import tkinter.ttk as ttk


class ProgressIndeterm(tk.Toplevel):
    def __init__(self, parent, lb_text='Emails werden gesendet...', progress_color=None):
        super().__init__(parent)
        self.grab_set()
        self.focus_set()
        self.wm_overrideredirect(True)

        self.style = ttk.Style()
        self.mainframe = ttk.Frame(self, padding='10 05 10 05', style='Mainframe.TFrame')
        self.style.configure('Mainframe.TFrame', background=progress_color)
        self.mainframe.pack()

        self.lb_hinweis = tk.Label(self.mainframe, text=lb_text, bg=progress_color)
        self.lb_hinweis.pack(pady=5)

        self.progressb = ttk.Progressbar(self.mainframe, orient='horizontal', length=200, mode='indeterminate')
        self.progressb.pack(pady=5)

        self.update()
        self.geometry(f'+{int((self.winfo_screenwidth() - self.winfo_width()) / 2)}'
                      f'+{int((self.winfo_screenheight() - self.winfo_height()) / 2)}')

    def start(self):
        self.progressb.start()

    def stop(self):
        self.progressb.stop()


class ProgressDeterm(tk.Toplevel):
    def __init__(self, parent, lb_text: str, progress_color=None, progress_text=False, maximum=100):
        super().__init__(parent)
        self.grab_set()
        self.wm_overrideredirect(True)
        self.progress_text = progress_text
        self.style = ttk.Style()
        self.mainframe = ttk.Frame(self, padding='10 00 10 00', style='Mainframe.TFrame')
        self.style.configure('Mainframe.TFrame', background=progress_color)
        self.mainframe.pack()

        self.lb_hinweis = tk.Label(self.mainframe, text=lb_text, bg=progress_color)
        self.lb_hinweis.pack(pady=5)

        self.var_progress = tk.DoubleVar(value=0)
        self.progressb = ttk.Progressbar(self.mainframe, orient='horizontal', length=200, mode='determinate',
                                         variable=self.var_progress, maximum=maximum)
        self.progressb.pack(padx=20, pady=5)

        if progress_text:
            self.lb_progress = tk.Label(self.mainframe, bg=progress_color)
            self.lb_progress.pack(pady=5)

        self.update()
        self.geometry(f'+{int((self.winfo_screenwidth() - self.winfo_width()) / 2)}'
                      f'+{int((self.winfo_screenheight() - self.winfo_height()) / 2)}')

    def set_progress(self, progress: int, progr_txt: str = None):
        self.var_progress.set(progress)
        if self.progress_text and progr_txt:
            self.lb_progress.config(text=progr_txt)
        self.progressb.update_idletasks()

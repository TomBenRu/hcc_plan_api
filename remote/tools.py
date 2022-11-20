import tkinter as tk


class PlaceholderEntry(tk.Entry):
    def __init__(self, master, placeholder='', show='', cnf={}, fg='black',
                 fg_placeholder='grey50', *args, **kw):
        super().__init__(master, cnf={}, bg='white', *args, **kw)
        self.fg = fg
        self.fg_placeholder = fg_placeholder
        self.placeholder = placeholder
        self.show = show
        self.bind('<FocusOut>', lambda event: self.fill_placeholder())
        self.bind('<FocusIn>', lambda event: self.clear_box())
        self.fill_placeholder()

    def clear_box(self):
        if not self.get() and super().get():
            self.config(fg=self.fg, show=self.show)
            self.delete(0, tk.END)

    def fill_placeholder(self):
        if not super().get():
            self.config(fg=self.fg_placeholder)
            self.insert(0, self.placeholder)
            self.config(show='')

    def get(self):
        content = super().get()
        if content == self.placeholder:
            return ''
        return content


if __name__ == '__main__':
    root = tk.Tk()

    entry1 = PlaceholderEntry(master=root, placeholder='Hallo', show='*')
    entry1.grid()
    entry2 = tk.Entry(master=root)
    entry2.grid()

    root.mainloop()
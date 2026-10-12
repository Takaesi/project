import tkinter as tk
from tkinter import messagebox, ttk

from .passwords import generate_password


class PasswordPrompt(tk.Toplevel):
    def __init__(self, parent, title, prompt):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        if parent.state() != "withdrawn":
            self.transient(parent)
        self.result = None

        frame = ttk.Frame(self, padding=15)
        frame.grid()
        ttk.Label(frame, text=prompt).grid(row=0, column=0, sticky="w")

        self.password = tk.StringVar(self)
        entry = ttk.Entry(frame, textvariable=self.password, show="•", width=34)
        entry.grid(row=1, column=0, pady=(8, 12))

        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, sticky="e")
        ttk.Button(buttons, text="Продолжить", command=self._submit).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(buttons, text="Отмена", command=self.destroy).pack(side="left")

        self.bind("<Return>", self._submit)
        self.bind("<Escape>", lambda event: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        self.grab_set()
        entry.focus_set()
        self.wait_window()

    def _submit(self, event=None):
        self.result = self.password.get()
        self.destroy()


class EntryDialog(tk.Toplevel):
    def __init__(self, parent, title, entry=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.result = None
        entry = entry or {"site": "", "login": "", "password": "", "note": ""}

        frm = ttk.Frame(self, padding=15)
        frm.grid()

        self.site = tk.StringVar(value=entry["site"])
        self.login = tk.StringVar(value=entry["login"])
        self.password = tk.StringVar(value=entry["password"])
        self.show = tk.BooleanVar(value=False)

        ttk.Label(frm, text="Сайт / сервис:").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frm, textvariable=self.site, width=34).grid(
            row=0, column=1, columnspan=2
        )

        ttk.Label(frm, text="Логин:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frm, textvariable=self.login, width=34).grid(
            row=1, column=1, columnspan=2
        )

        ttk.Label(frm, text="Пароль:").grid(row=2, column=0, sticky="w", pady=4)
        self.pw_entry = ttk.Entry(frm, textvariable=self.password, width=34, show="•")
        self.pw_entry.grid(row=2, column=1, columnspan=2)

        ttk.Checkbutton(
            frm, text="Показать", variable=self.show, command=self._toggle
        ).grid(row=3, column=1, sticky="w")
        ttk.Button(frm, text="Сгенерировать", command=self._generate).grid(
            row=3, column=2, sticky="e"
        )

        ttk.Label(frm, text="Заметка:").grid(row=4, column=0, sticky="nw", pady=4)
        self.note = tk.Text(frm, width=34, height=4)
        self.note.grid(row=4, column=1, columnspan=2)
        self.note.insert("1.0", entry["note"])

        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=3, pady=(12, 0), sticky="e")
        ttk.Button(btns, text="Сохранить", command=self._ok).pack(side="left", padx=4)
        ttk.Button(btns, text="Отмена", command=self.destroy).pack(side="left")

        self.bind("<Return>", lambda e: None)
        self.bind("<Escape>", lambda e: self.destroy())
        self.grab_set()
        self.wait_window()

    def _toggle(self):
        self.pw_entry.config(show="" if self.show.get() else "•")

    def _generate(self):
        self.password.set(generate_password())
        self.show.set(True)
        self._toggle()

    def _ok(self):
        if not self.site.get().strip() or not self.password.get():
            messagebox.showwarning("Внимание", "Укажите сервис и пароль.", parent=self)
            return
        self.result = {
            "site": self.site.get().strip(),
            "login": self.login.get().strip(),
            "password": self.password.get(),
            "note": self.note.get("1.0", "end").strip(),
        }
        self.destroy()

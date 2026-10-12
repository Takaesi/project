import tkinter as tk
from tkinter import messagebox, ttk

from .config import CLIPBOARD_CLEAR_MS
from .dialogs import EntryDialog, PasswordPrompt
from .storage import Vault


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Менеджер паролей")
        self.geometry("720x460")
        self.minsize(620, 380)
        self.vault = Vault()
        self._visible = []
        self.clear_job = None

        self.withdraw()
        if not self._login():
            self.destroy()
            return
        self.deiconify()
        self._build_ui()
        self._refresh()

    def _login(self):
        if not self.vault.exists():
            messagebox.showinfo(
                "Первый запуск",
                "Придумайте мастер-пароль. Его невозможно восстановить — "
                "если забудете, данные будут потеряны.",
            )
            while True:
                p1 = PasswordPrompt(
                    self, "Мастер-пароль", "Новый мастер-пароль:"
                ).result
                if p1 is None:
                    return False
                if len(p1) < 8:
                    messagebox.showwarning("Слабый пароль", "Минимум 8 символов.")
                    continue
                p2 = PasswordPrompt(
                    self, "Мастер-пароль", "Повторите пароль:"
                ).result
                if p2 is None:
                    return False
                if p1 != p2:
                    messagebox.showerror("Ошибка", "Пароли не совпадают.")
                    continue
                self.vault.create(p1)
                return True

        for _ in range(5):
            password = PasswordPrompt(self, "Вход", "Мастер-пароль:").result
            if password is None:
                return False
            if self.vault.unlock(password):
                return True
            messagebox.showerror("Ошибка", "Неверный мастер-пароль.")
        return False

    def _build_ui(self):
        top = ttk.Frame(self, padding=(10, 10, 10, 0))
        top.pack(fill="x")
        ttk.Label(top, text="Поиск:").pack(side="left")
        self.search = tk.StringVar()
        self.search.trace_add("write", lambda *a: self._refresh())
        ttk.Entry(top, textvariable=self.search).pack(
            side="left", fill="x", expand=True, padx=6
        )

        mid = ttk.Frame(self, padding=10)
        mid.pack(fill="both", expand=True)
        cols = ("site", "login", "password")
        self.tree = ttk.Treeview(mid, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("site", text="Сервис")
        self.tree.heading("login", text="Логин")
        self.tree.heading("password", text="Пароль")
        self.tree.column("site", width=240)
        self.tree.column("login", width=240)
        self.tree.column("password", width=120)
        scrollbar = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")
        self.tree.bind("<Double-1>", lambda e: self._edit())

        bottom = ttk.Frame(self, padding=(10, 0, 10, 10))
        bottom.pack(fill="x")
        for text, command in [
            ("Добавить", self._add),
            ("Изменить", self._edit),
            ("Удалить", self._delete),
            ("Копировать пароль", self._copy_password),
            ("Копировать логин", self._copy_login),
        ]:
            ttk.Button(bottom, text=text, command=command).pack(
                side="left", padx=(0, 6)
            )

        self.status = tk.StringVar()
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w").pack(
            fill="x", side="bottom"
        )

    def _refresh(self):
        query = self.search.get().lower().strip() if hasattr(self, "search") else ""
        self.tree.delete(*self.tree.get_children())
        self._visible = []
        for index, entry in enumerate(self.vault.entries):
            if (
                query
                and query not in entry["site"].lower()
                and query not in entry["login"].lower()
            ):
                continue
            self._visible.append(index)
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(entry["site"], entry["login"], "••••••••"),
            )
        self.status.set(f"Записей: {len(self.vault.entries)}")

    def _selected_index(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Подсказка", "Сначала выберите запись.")
            return None
        return int(selection[0])

    def _add(self):
        dialog = EntryDialog(self, "Новая запись")
        if dialog.result:
            self.vault.entries.append(dialog.result)
            self.vault.save()
            self._refresh()

    def _edit(self):
        index = self._selected_index()
        if index is None:
            return
        dialog = EntryDialog(self, "Редактирование", self.vault.entries[index])
        if dialog.result:
            self.vault.entries[index] = dialog.result
            self.vault.save()
            self._refresh()

    def _delete(self):
        index = self._selected_index()
        if index is None:
            return
        name = self.vault.entries[index]["site"]
        if messagebox.askyesno("Удаление", f"Удалить запись «{name}»?"):
            del self.vault.entries[index]
            self.vault.save()
            self._refresh()

    def _copy(self, text, what):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status.set(f"{what} скопирован. Буфер очистится через 20 секунд.")
        if self.clear_job:
            self.after_cancel(self.clear_job)
        self.clear_job = self.after(CLIPBOARD_CLEAR_MS, self._clear_clipboard)

    def _clear_clipboard(self):
        self.clipboard_clear()
        self.status.set("Буфер обмена очищен.")

    def _copy_password(self):
        index = self._selected_index()
        if index is not None:
            self._copy(self.vault.entries[index]["password"], "Пароль")

    def _copy_login(self):
        index = self._selected_index()
        if index is not None:
            self._copy(self.vault.entries[index]["login"], "Логин")

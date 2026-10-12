import flet as ft

from .entities import Entry
from .passwords import PasswordGenerator
from .storage import Vault


class LoginDialog(ft.AlertDialog):
    def __init__(self, page, vault, on_success, on_cancel):
        is_new_vault = not vault.exists()
        password_input = ft.TextField(
            label="Новый мастер-пароль" if is_new_vault else "Мастер-пароль",
            password=True,
            can_reveal_password=True,
            autofocus=True,
            on_submit=self._authenticate,
        )
        repeat_input = ft.TextField(
            label="Повторите мастер-пароль",
            password=True,
            can_reveal_password=True,
            visible=is_new_vault,
            on_submit=self._authenticate,
        )
        error_label = ft.Text("", color="#b42318")
        content = ft.Column(
            controls=[
                ft.Text(
                    "Мастер-пароль нельзя восстановить."
                    if is_new_vault
                    else "Введите мастер-пароль для доступа к хранилищу."
                ),
                password_input,
                repeat_input,
                error_label,
            ],
            tight=True,
            width=380,
            spacing=12,
        )
        super().__init__(
            modal=True,
            title=ft.Text(
                "Создание хранилища" if is_new_vault else "Вход в хранилище"
            ),
            content=content,
            actions=[
                ft.TextButton("Отмена", on_click=self._cancel),
                ft.FilledButton("Продолжить", on_click=self._authenticate),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=self._dismiss,
        )
        self._page = page
        self._vault = vault
        self._on_success = on_success
        self._on_cancel = on_cancel
        self.is_new_vault = is_new_vault
        self._authenticated = False
        self._cancelled = False
        self.password_input = password_input
        self.repeat_input = repeat_input
        self.error_label = error_label

    def _authenticate(self, event=None):
        password = self.password_input.value or ""
        if self.is_new_vault:
            if len(password) < 8:
                self.error_label.value = "Минимальная длина мастер-пароля — 8 символов."
                self.update()
                return
            if password != (self.repeat_input.value or ""):
                self.error_label.value = "Пароли не совпадают."
                self.update()
                return
            try:
                self._vault.create(password)
            except OSError as error:
                self.error_label.value = f"Не удалось создать хранилище: {error}"
                self.update()
                return
            self._authenticated = True
            self._page.pop_dialog()
            self._on_success()
            return

        try:
            unlocked = self._vault.unlock(password)
        except (OSError, ValueError) as error:
            self.error_label.value = f"Ошибка хранилища: {error}"
            self.update()
            return
        if unlocked:
            self._authenticated = True
            self._page.pop_dialog()
            self._on_success()
            return
        self.password_input.value = ""
        self.error_label.value = "Неверный мастер-пароль."
        self.update()

    def _cancel(self, event=None):
        self._cancelled = True
        self._page.pop_dialog()
        self._on_cancel()

    def _dismiss(self, event=None):
        if not self._authenticated and not self._cancelled:
            self._cancelled = True
            self._on_cancel()


class EntryDialog(ft.AlertDialog):
    def __init__(self, page, on_save, entry=None):
        source = entry if isinstance(entry, Entry) else Entry()
        generator = PasswordGenerator()
        site_input = ft.TextField(
            label="Сервис",
            value=source.site,
            hint_text="Например, example.com",
            autofocus=True,
        )
        login_input = ft.TextField(
            label="Логин",
            value=source.login,
            hint_text="Имя пользователя или электронная почта",
        )
        password_input = ft.TextField(
            label="Пароль",
            value=source.password,
            password=True,
            can_reveal_password=True,
        )
        note_input = ft.TextField(
            label="Заметка",
            value=source.note,
            multiline=True,
            min_lines=2,
            max_lines=4,
        )
        length_input = ft.Slider(
            min=8,
            max=64,
            divisions=56,
            value=20,
            label="{value}",
            on_change=self._update_length,
        )
        length_label = ft.Text("Длина пароля: 20")
        digits_option = ft.Checkbox(label="Цифры", value=True)
        symbols_option = ft.Checkbox(label="Символы", value=True)
        error_label = ft.Text("", color="#b42318")
        form = ft.Column(
            controls=[
                site_input,
                login_input,
                password_input,
                ft.Row(
                    [
                        length_label,
                        ft.OutlinedButton(
                            "Сгенерировать пароль",
                            icon=ft.Icons.AUTORENEW,
                            on_click=self._generate_password,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                length_input,
                ft.Row([digits_option, symbols_option]),
                note_input,
                error_label,
            ],
            tight=True,
            width=500,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )
        super().__init__(
            modal=True,
            title=ft.Text("Новая запись" if entry is None else "Редактирование записи"),
            content=form,
            actions=[
                ft.TextButton("Отмена", on_click=self._cancel),
                ft.FilledButton("Сохранить", on_click=self._save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page = page
        self._on_save = on_save
        self._generator = generator
        self.site_input = site_input
        self.login_input = login_input
        self.password_input = password_input
        self.note_input = note_input
        self.length_input = length_input
        self.length_label = length_label
        self.digits_option = digits_option
        self.symbols_option = symbols_option
        self.error_label = error_label

    def _update_length(self, event):
        self.length_label.value = f"Длина пароля: {int(event.control.value)}"
        self.update()

    def _generate_password(self, event=None):
        self._generator.length = int(self.length_input.value)
        self._generator.digits = bool(self.digits_option.value)
        self._generator.symbols = bool(self.symbols_option.value)
        self.password_input.value = self._generator.generate()
        self.update()

    def _save(self, event=None):
        site = (self.site_input.value or "").strip()
        password = self.password_input.value or ""
        if not site or not password:
            self.error_label.value = "Укажите сервис и пароль."
            self.update()
            return
        entry = Entry(
            site,
            self.login_input.value or "",
            password,
            self.note_input.value or "",
        )
        self._page.pop_dialog()
        self._on_save(entry)

    def _cancel(self, event=None):
        self._page.pop_dialog()

import asyncio
import atexit
import logging

import flet as ft

from .config import CLIPBOARD_CLEAR_MS
from .dialogs import EntryDialog, LoginDialog
from .entities import Entity, Entry
from .passwords import PasswordGenerator
from .reports import ReportWriter, SessionReport
from .storage import Vault


class SearchField(ft.TextField):
    def __init__(self, on_change):
        super().__init__(
            label="Поиск",
            hint_text="Сервис или логин",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            on_change=on_change,
            dense=True,
        )
        self._mounted = False

    def did_mount(self):
        super().did_mount()
        self._mounted = True

    def will_unmount(self):
        self._mounted = False
        super().will_unmount()


class EntryTable(ft.DataTable):
    def __init__(self, on_select, on_edit):
        super().__init__(
            columns=[
                ft.DataColumn(ft.Text("Сервис")),
                ft.DataColumn(ft.Text("Логин")),
                ft.DataColumn(ft.Text("Пароль")),
            ],
            rows=[],
            show_checkbox_column=True,
            heading_row_color="#e9eef7",
            data_row_min_height=54,
            data_row_max_height=64,
            column_spacing=40,
            expand=True,
        )
        self._on_select_entry = on_select
        self._on_edit_entry = on_edit
        self._mounted = False

    def did_mount(self):
        super().did_mount()
        self._mounted = True

    def will_unmount(self):
        self._mounted = False
        super().will_unmount()

    def replace_entries(self, indexed_entries):
        self.rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(
                        ft.Text(entry.site),
                        on_tap=lambda event, entry_index=index: self._on_select_entry(
                            entry_index
                        ),
                        on_double_tap=lambda event, entry_index=index: self._on_edit_entry(
                            entry_index
                        ),
                    ),
                    ft.DataCell(
                        ft.Text(entry.login or "—"),
                        on_tap=lambda event, entry_index=index: self._on_select_entry(
                            entry_index
                        ),
                        on_double_tap=lambda event, entry_index=index: self._on_edit_entry(
                            entry_index
                        ),
                    ),
                    ft.DataCell(
                        ft.Text("••••••••"),
                        on_tap=lambda event, entry_index=index: self._on_select_entry(
                            entry_index
                        ),
                    ),
                ],
                selected=False,
                on_select_change=lambda event, entry_index=index: self._on_select_entry(
                    entry_index
                ),
                data=index,
            )
            for index, entry in indexed_entries
        ]
        if self._mounted:
            self.update()


class GeneratorPanel(ft.Container):
    def __init__(self, on_generate):
        length = ft.Slider(
            min=8,
            max=64,
            divisions=56,
            value=20,
            label="{value}",
        )
        digits = ft.Checkbox(label="Цифры", value=True)
        symbols = ft.Checkbox(label="Символы", value=True)
        output = ft.TextField(
            label="Новый пароль",
            password=True,
            can_reveal_password=True,
            read_only=True,
            expand=True,
            dense=True,
        )
        generate_button = ft.FilledButton(
            "Сгенерировать",
            icon=ft.Icons.AUTORENEW,
            on_click=self._generate,
        )
        content = ft.Column(
            [
                ft.Text("Генератор паролей", size=17, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.Text("Длина"),
                        length,
                        digits,
                        symbols,
                        generate_button,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    wrap=True,
                ),
                output,
            ],
            spacing=12,
        )
        super().__init__(
            content=content,
            padding=18,
            border_radius=12,
            bgcolor="#ffffff",
            border=ft.Border.all(1, "#d8deea"),
        )
        self._on_generate = on_generate
        self._mounted = False
        self.length = length
        self.digits = digits
        self.symbols = symbols
        self.output = output
        self.generate_button = generate_button

    def did_mount(self):
        super().did_mount()
        self._mounted = True

    def will_unmount(self):
        self._mounted = False
        super().will_unmount()

    def _generate(self, event=None):
        self._on_generate(
            int(self.length.value),
            bool(self.digits.value),
            bool(self.symbols.value),
        )

    def set_password(self, value):
        self.output.value = value
        self.update()


class MainPage(Entity):
    def __init__(self, page, vault, report_writer=None, report=None, clipboard=None):
        self.page = page
        self.vault = vault
        self.report_writer = (
            report_writer if report_writer is not None else ReportWriter()
        )
        self.report = report if report is not None else SessionReport()
        self.clipboard = clipboard if clipboard is not None else ft.Clipboard()
        self.selected_index = None
        self._last_copied_value = ""
        self._report_written = False
        self.generator = PasswordGenerator()
        self.status = ft.Text(size=12, color="#526078")
        self.search = SearchField(self._filter_entries)
        self.entries_table = EntryTable(self._select_entry, self._edit_entry)
        self.generator_panel = GeneratorPanel(self._generate_password)
        self._refresh_entries()
        self._build()

    def identity(self):
        return self.report.started_at, str(self.report_writer.path)

    def _build(self):
        self.page.title = "Менеджер паролей"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = "#f5f7fb"
        self.page.padding = 24
        self.page.window.width = 1060
        self.page.window.height = 790
        self.page.window.min_width = 760
        self.page.window.min_height = 580
        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary="#4169e1",
                on_primary="#ffffff",
                surface="#ffffff",
            )
        )

        title = ft.Text("Мои пароли", size=30, weight=ft.FontWeight.BOLD)
        subtitle = ft.Text(
            "Зашифрованное локальное хранилище",
            size=14,
            color="#68748a",
        )
        add_button = ft.FilledButton(
            "Добавить запись",
            icon=ft.Icons.ADD,
            on_click=self._add_entry,
        )
        search_row = ft.Row(
            [self.search, add_button],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=14,
        )

        self.edit_button = ft.OutlinedButton(
            "Изменить",
            icon=ft.Icons.EDIT_OUTLINED,
            on_click=self._edit_selected,
        )
        self.delete_button = ft.OutlinedButton(
            "Удалить",
            icon=ft.Icons.DELETE_OUTLINE,
            on_click=self._delete_entry,
        )
        self.copy_login_button = ft.OutlinedButton(
            "Копировать логин",
            icon=ft.Icons.CONTENT_COPY,
            on_click=self._copy_login,
        )
        self.copy_password_button = ft.OutlinedButton(
            "Копировать пароль",
            icon=ft.Icons.KEY,
            on_click=self._copy_password,
        )
        actions = ft.Row(
            [
                self.edit_button,
                self.delete_button,
                self.copy_login_button,
                self.copy_password_button,
            ],
            wrap=True,
            spacing=8,
        )
        table_card = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Сохранённые записи", size=18, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            self.status,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=1, color="#e5eaf2"),
                    ft.Row([self.entries_table], scroll=ft.ScrollMode.AUTO, expand=True),
                    actions,
                ],
                expand=True,
                spacing=14,
            ),
            padding=20,
            border_radius=12,
            bgcolor="#ffffff",
            border=ft.Border.all(1, "#d8deea"),
            expand=True,
        )
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        title,
                        subtitle,
                        search_row,
                        table_card,
                        self.generator_panel,
                        ft.Text(
                            "Отчёт сессии сохраняется в activity_report.json при закрытии.",
                            size=11,
                            color="#7c879a",
                        ),
                    ],
                    expand=True,
                    spacing=14,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                alignment=ft.Alignment.TOP_CENTER,
                expand=True,
                width=1180,
            )
        )

    def _refresh_entries(self):
        query = (self.search.value or "").strip().casefold()
        indexed_entries = []
        for index, entry in enumerate(self.vault.entries):
            if query and query not in entry.site.casefold() and query not in entry.login.casefold():
                continue
            indexed_entries.append((index, entry))
        self.entries_table.replace_entries(indexed_entries)
        self.status.value = (
            f"{len(indexed_entries)} из {len(self.vault.entries)} записей"
        )
        if self.entries_table._mounted:
            self.status.update()

    def _filter_entries(self, event=None):
        self.selected_index = None
        self._refresh_entries()

    def _select_entry(self, index):
        self.selected_index = index
        for row in self.entries_table.rows:
            row.selected = row.data == index
        self.entries_table.update()

    def _selected_entry(self):
        if self.selected_index is None:
            self._show_status("Сначала выберите запись.")
            return None
        if self.selected_index >= len(self.vault.entries):
            self.selected_index = None
            self._show_status("Запись больше недоступна. Обновите список.")
            return None
        return self.vault.entries[self.selected_index]

    def _add_entry(self, event=None):
        self.page.show_dialog(EntryDialog(self.page, self._save_new_entry))

    def _save_new_entry(self, entry):
        self.vault.entries.add(entry)
        if not self._save_vault():
            self.vault.entries.remove(len(self.vault.entries) - 1)
            return
        self.report.add_event("entry_added", entry.site)
        self._refresh_entries()

    def _edit_selected(self, event=None):
        entry = self._selected_entry()
        if entry is not None:
            self._edit_entry(self.selected_index)

    def _edit_entry(self, index):
        if index is None or index >= len(self.vault.entries):
            return
        original = self.vault.entries[index]
        self.page.show_dialog(
            EntryDialog(
                self.page,
                lambda updated: self._save_edited_entry(index, original, updated),
                original,
            )
        )

    def _save_edited_entry(self, index, original, updated):
        self.vault.entries.replace(index, updated)
        if not self._save_vault():
            self.vault.entries.replace(index, original)
            return
        self.report.add_event("entry_edited", updated.site)
        self._refresh_entries()

    def _delete_entry(self, event=None):
        entry = self._selected_entry()
        if entry is None:
            return
        confirmation = ft.AlertDialog(
            modal=True,
            title=ft.Text("Удалить запись?"),
            content=ft.Text(f"Запись «{entry.site}» будет удалена."),
            actions=[
                ft.TextButton("Отмена", on_click=lambda _: self.page.pop_dialog()),
                ft.FilledButton(
                    "Удалить",
                    on_click=lambda _: self._confirm_delete(self.selected_index, entry),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(confirmation)

    def _confirm_delete(self, index, entry):
        self.page.pop_dialog()
        self.vault.entries.remove(index)
        if not self._save_vault():
            self.vault.entries.insert(index, entry)
            return
        self.selected_index = None
        self.report.add_event("entry_deleted", entry.site)
        self._refresh_entries()

    def _save_vault(self):
        try:
            self.vault.save()
        except OSError as error:
            self._show_status(f"Не удалось сохранить хранилище: {error}")
            return False
        return True

    def _copy_login(self, event=None):
        entry = self._selected_entry()
        if entry is not None:
            self.page.run_task(self._copy_to_clipboard, entry.login, "Логин")

    def _copy_password(self, event=None):
        entry = self._selected_entry()
        if entry is not None:
            self.page.run_task(self._copy_to_clipboard, entry.password, "Пароль")

    async def _copy_to_clipboard(self, value, label):
        try:
            await self.clipboard.set(value)
        except (OSError, RuntimeError) as error:
            self._show_status(f"Не удалось скопировать: {error}")
            return
        self._last_copied_value = value
        self.report.add_event(f"{label.lower()}_copied")
        self._show_status(f"{label} скопирован. Буфер очистится через 20 секунд.")
        self.page.run_task(self._clear_clipboard_after, value)

    async def _clear_clipboard_after(self, copied_value):
        await asyncio.sleep(CLIPBOARD_CLEAR_MS / 1000)
        try:
            current_value = await self.clipboard.get()
            if current_value == copied_value and copied_value == self._last_copied_value:
                await self.clipboard.set("")
                self._last_copied_value = ""
                self._show_status("Буфер обмена очищен.")
        except (OSError, RuntimeError) as error:
            self._show_status(f"Не удалось очистить буфер обмена: {error}")

    def _generate_password(self, length, digits, symbols):
        self.generator.length = length
        self.generator.digits = digits
        self.generator.symbols = symbols
        self.generator_panel.set_password(self.generator.generate())
        self.report.add_event("password_generated")

    def _show_status(self, message):
        self.status.value = message
        self.status.update()

    def _on_window_event(self, event):
        if event.type == ft.WindowEventType.CLOSE:
            self._finish_session()

    def _finish_session(self, event=None):
        if self._report_written:
            return
        self._report_written = True
        self.report.add_event("session_closed", "Приложение закрыто")
        self.report.finish()
        try:
            self.report_writer.write(self.report)
        except OSError as error:
            self._report_written = False
            logging.exception("Не удалось сохранить JSON-отчёт: %s", error)
            self.status.value = f"Не удалось сохранить JSON-отчёт: {error}"

    def __eq__(self, other):
        return isinstance(other, MainPage) and self.identity() == other.identity()

    def __repr__(self):
        return f"MainPage(session={self.report.started_at!r})"

    def __str__(self):
        return "Окно менеджера паролей"


class PasswordManagerApp(Entity):
    def __init__(self, page, vault=None, report_writer=None, clipboard=None):
        self.page = page
        self.vault = vault if vault is not None else Vault()
        self.report_writer = (
            report_writer if report_writer is not None else ReportWriter()
        )
        self.report = SessionReport()
        self.report.add_event("session_started", "Приложение открыто")
        self.clipboard = clipboard if clipboard is not None else ft.Clipboard()
        self.main_page = None
        self._report_written = False
        self.page.on_close = self._finish_session
        self.page.on_disconnect = self._finish_session
        self.page.window.on_event = self._on_window_event
        self.page.title = "Менеджер паролей"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = "#f5f7fb"
        self.page.padding = 24
        atexit.register(self._finish_session)

    def identity(self):
        return self.report.started_at, str(self.report_writer.path)

    def start(self):
        self._show_login()

    def _show_login(self):
        self.page.clean()
        self.page.show_dialog(
            LoginDialog(
                self.page,
                self.vault,
                self._open_vault,
                self._login_cancelled,
            )
        )

    def _open_vault(self):
        self.report.add_event("vault_unlocked")
        self.page.clean()
        self.main_page = MainPage(
            self.page,
            self.vault,
            self.report_writer,
            self.report,
            self.clipboard,
        )

    def _login_cancelled(self):
        self.page.clean()
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.LOCK_OUTLINE, size=48, color="#4169e1"),
                        ft.Text("Вход отменён", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("Откройте форму входа, чтобы продолжить."),
                        ft.FilledButton(
                            "Вернуться ко входу",
                            icon=ft.Icons.LOCK_OPEN,
                            on_click=lambda event: self._show_login(),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=16,
                ),
                alignment=ft.Alignment.CENTER,
                expand=True,
            )
        )

    def _on_window_event(self, event):
        if event.type == ft.WindowEventType.CLOSE:
            self._finish_session()

    def _finish_session(self, event=None):
        if self.main_page is not None:
            self.main_page._finish_session(event)
            return
        if self._report_written:
            return
        self._report_written = True
        self.report.add_event("session_closed", "Приложение закрыто")
        self.report.finish()
        try:
            self.report_writer.write(self.report)
        except OSError as error:
            self._report_written = False
            logging.exception("Не удалось сохранить JSON-отчёт: %s", error)

    def __eq__(self, other):
        return isinstance(other, PasswordManagerApp) and self.identity() == other.identity()

    def __repr__(self):
        return f"PasswordManagerApp(session={self.report.started_at!r})"

    def __str__(self):
        return "Менеджер паролей"

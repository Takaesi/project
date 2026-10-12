import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import flet as ft

from password_manager.app import (
    EntryTable,
    GeneratorPanel,
    MainPage,
    PasswordManagerApp,
    SearchField,
)
from password_manager.dialogs import EntryDialog, LoginDialog
from password_manager.entities import Entry
from password_manager.reports import ReportWriter
from password_manager.storage import Vault


class FakePage:
    def __init__(self):
        self.window = SimpleNamespace()
        self.controls = []

    def add(self, *controls):
        self.controls.extend(controls)


class FletApplicationTests(unittest.TestCase):
    def test_three_flet_components_override_lifecycle_methods(self):
        search = SearchField(lambda event: None)
        table = EntryTable(lambda index: None, lambda index: None)
        generator = GeneratorPanel(lambda length, digits, symbols: None)

        self.assertIsInstance(search, ft.TextField)
        self.assertIsInstance(table, ft.DataTable)
        self.assertIsInstance(generator, ft.Container)
        self.assertIsNot(SearchField.did_mount, ft.TextField.did_mount)
        self.assertIsNot(EntryTable.did_mount, ft.DataTable.did_mount)
        self.assertIsNot(GeneratorPanel.did_mount, ft.Container.did_mount)

    def test_login_and_entry_dialogs_call_domain_methods(self):
        class DialogPage:
            def __init__(self):
                self.closed_dialogs = 0

            def pop_dialog(self):
                self.closed_dialogs += 1

        with tempfile.TemporaryDirectory() as directory:
            page = DialogPage()
            vault = Vault(Path(directory) / "vault.bin")
            authenticated = []
            login = LoginDialog(page, vault, lambda: authenticated.append(True), lambda: None)
            login.password_input.value = "test-master-password"
            login.repeat_input.value = "test-master-password"
            login._authenticate()
            self.assertTrue(vault.exists())
            self.assertEqual(authenticated, [True])
            self.assertEqual(page.closed_dialogs, 1)

            saved = []
            dialog = EntryDialog(page, saved.append)
            dialog.site_input.value = "example.com"
            dialog.login_input.value = "alice"
            dialog.password_input.value = "secret"
            dialog._save()
            self.assertEqual(saved[0], Entry("example.com", "alice", "secret"))

    def test_main_page_filters_records_and_saves_close_report(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = Vault(Path(directory) / "vault.bin")
            vault.create("test-master-password")
            vault.entries.add(Entry("example.com", "alice", "secret"))
            vault.entries.add(Entry("another.example", "bob", "secret"))
            report_path = Path(directory) / "activity_report.json"
            page = FakePage()
            main_page = MainPage(
                page,
                vault,
                ReportWriter(report_path),
                clipboard=object(),
            )

            main_page.search.value = "alice"
            main_page._filter_entries()
            self.assertEqual(len(main_page.entries_table.rows), 1)
            self.assertEqual(
                main_page.entries_table.rows[0].cells[0].content.value,
                "example.com",
            )

            main_page._finish_session()
            self.assertTrue(report_path.exists())

    def test_app_manager_and_page_are_user_defined_entities(self):
        with tempfile.TemporaryDirectory() as directory:
            page = FakePage()
            manager = PasswordManagerApp(
                page,
                vault=Vault(Path(directory) / "vault.bin"),
                report_writer=ReportWriter(Path(directory) / "report.json"),
                clipboard=object(),
            )
            self.assertEqual(manager, manager)
            self.assertIn("Менеджер паролей", str(manager))
            manager._finish_session()


if __name__ == "__main__":
    unittest.main()

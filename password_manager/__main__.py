import flet as ft

from .app import PasswordManagerApp


def main(page: ft.Page):
    application = PasswordManagerApp(page)
    application.start()


def run():
    ft.run(
        main,
        view=ft.AppView.WEB_BROWSER,
        host="127.0.0.1",
        port=8550,
    )


if __name__ == "__main__":
    run()

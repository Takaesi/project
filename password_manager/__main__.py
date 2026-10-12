from .app import App


def main():
    app = App()
    if app.winfo_exists():
        app.mainloop()


if __name__ == "__main__":
    main()

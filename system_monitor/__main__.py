"""Allow running as: python -m system_monitor"""

from system_monitor.ui.app import SystemMonitorApp


def main() -> None:
    app = SystemMonitorApp()
    app.mainloop()


if __name__ == "__main__":
    main()

"""Entry point for Tools CLI."""

from cli.app import ToolsApp


def main() -> None:
    """Run the Tools CLI application."""
    app = ToolsApp()
    app.run()


if __name__ == "__main__":
    main()


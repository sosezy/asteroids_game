"""Точка входа для запуска игры «Астероиды»."""

from src.game import AsteroidsGame


def main() -> None:
    """Создать экземпляр игры и запустить главный цикл."""
    game = AsteroidsGame()
    game.run()


if __name__ == "__main__":
    main()
class GameStats:
    """Отслеживает статистику игры"""
    def __init__(self, ai_game):
        self.settings = ai_game.settings
        self.reset_stats()

    def reset_stats(self):
        """Инициализирует статистику, изменяющиеся в ходе игры"""
        self.ships_left = self.settings.ship_limit
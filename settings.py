class Settings:
    """Класс для хранения всех настроек игры Alien Invasion."""
    def __init__(self):
        """Инициирует настройки игры."""
        # Параметры экрана
        self.screen_width = 1200
        self.screen_height = 800
        self.bg_color = (0, 0, 0)

        # Настройки корабля
        self.ship_speed_factor = 1.5
        self.ship_limit = 2

        # Параметры снаряда
        self.bullet_speed = 1.5
        self.bullet_width = 5
        self.bullet_height = 15
        self.bullet_color = (127, 255, 212)
        self.bullets_allowed = 5

        #Настройка пришельцев
        self.alien_speed = 0.5
        self.fleet_drop_speed = 5
        self.fleet_direction = 1
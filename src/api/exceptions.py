class GameException(Exception):
    def __init__(self, game, msg=None):
        super().__init__(msg)
        self.game = game

class InvalidClearException(GameException):
    pass

class GameNotFoundException(GameException):
    pass

class InvalidGameSettingsException(GameException):
    pass
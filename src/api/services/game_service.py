import random
import datetime
from models import db, Game
from exceptions import InvalidClearException, InvalidGameSettingsException

class GameService:

    def __init__(self, game: Game = None):
        if game:
            self.game = game
    
    def start_game(self, user_id: int, rows: int = 10, columns: int = 10, mines: int = 20):
        self.game = Game()
        self.game.status = "started"
        self.game.user_id = user_id
        self._generate_board(rows, columns, mines)


    def _is_cell_valid(self, row: int, column: int):
        if self.game.status != "started":
            raise InvalidClearException(game, "Cannot clear cells on an inactive game")
        if row not in range(self.game.rows) or column not in range(self.game.columns):
            raise InvalidClearException(game, "Cannot clear cells outside of minefield")


    def clear(self, row: int, column: int):
        self._is_cell_valid(row, column)
        
        if not self.game.start_time:
            self.game.start_time = datetime.datetime.utcnow()
        
        if self.game.board[row][column]["status"] in  ("U","F"):
            return
        
        if self.game.board[row][column]["value"]==-1:
            self.game.board[row][column]["status"] = "U"
            self.game.status = "lost"
            self.game.end_time = datetime.datetime.utcnow()
        else:
            self._clear_adjacents(row, column)
            if self.is_complete():
                self.game.status = "won"
                self.game.end_time = datetime.datetime.utcnow()


    def _clear_adjacents(self, row: int, column: int):
        if row<0 or column<0 or row>=self.game.rows or column>=self.game.columns:
            return
        if self.game.board[row][column]["status"] in ("U","F"):
            return
        cell_value = self.game.board[row][column]["value"]
        if cell_value != -1:
            self.game.board[row][column]["status"] = "U"
            if cell_value == 0:
                for r in range(row-1, row+2):
                    for c in range(column-1,column+2):
                        if not (r==row and c==column):
                            self._clear_adjacents(r, c)


    def toggle(self, row: int, column: int):
        self._is_cell_valid(row, column)
        values = ["C", "F", "?"]
        status = self.game.board[row][column]["status"]
        if status != "U":
            self.game.board[row][column]["status"] = values[(values.index(status)+1) % len(values)]


    def is_complete(self):
        for row in self.game.board:
            for column in row:
                if column["value"] !=-1 and column["status"] != "U":
                    return False
        return True
        

    def _generate_board(self, rows: int, columns: int, mines: int):
        if rows*columns <= mines:
            raise InvalidGameSettingsException(self.game, "Number of mines must be less than the total board size")
        if rows <= 0 or columns <= 0 or mines <= 0:
            raise InvalidGameSettingsException(self.game, "All values must be greater than zero")
        self.game.rows = rows
        self.game.columns = columns
        self.game.mines_left = mines
        self.game.board = [[{"value": 0, "status": "C"} for y in range(columns)] for x in range(rows)]
        self._place_mines(rows, columns, mines)
        self._calculate_values(rows, columns)

    def _place_mines(self, rows: int, columns: int, mines: int):
        row_count = len(self.game.board)
        column_count = len(self.game.board[0])

        while mines>0:
            #TODO: Account for retries to avoid bogosort kind of problems
            target_row = random.randint(0,row_count-1)
            target_column = random.randint(0,column_count-1)
            if self.game.board[target_row][target_column]["value"] == 0:
                self.game.board[target_row][target_column]["value"] = -1
                mines -= 1

    def _calculate_values(self, rows: int, columns: int):
        for (i,row) in enumerate(self.game.board):
            for (j,col) in enumerate(row):
                if(col["value"]==-1):
                    continue

                count = 0
                for r in range(i-1,i+2):
                    for c in range(j-1,j+2):
                        if r>=0 and r<rows and c>=0 and c<columns and not (r==i and c==j):
                            if(self.game.board[r][c]["value"]==-1):
                                count += 1
                col["value"] = count

    def _mask_board(self):
        rows = []
        for row in self.game.board:
            columns = []
            for column in row:
                if column["status"] == "U":
                    columns.append(column["value"])
                else:
                    columns.append(column["status"])
            rows.append(columns)

        return rows

    def encode_game_info(self):
        return {
            "id": self.game.id,
            "start_time": self.game.start_time,
            "end_time": self.game.end_time,
            "mines_left": self.game.mines_left,
            "status": self.game.status,
            "board": self._mask_board()
        }
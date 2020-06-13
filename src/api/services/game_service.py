import random
from models import db,Game

class GameService:

    def __init__(self, game: Game = None):
        if game:
            self.game = game
    
    def start_game(self, user_id):
        self.game = Game()
        self.game.status = "started"
        self.game.user_id = user_id
        self._generate_board()

    def _generate_board(self, rows:int = 10, columns: int = 10, mines: int = 5):
        #TODO: check that mine count does not exceed (rows*columns)-1
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
            "mines_left": self.game.mines_left,
            "status": self.game.status,
            "board": self._mask_board()
        }
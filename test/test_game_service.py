import pytest

from services.game_service import GameService
from models import Game

def get_mock_game():
    mock_game = Game()
    mock_game.id = 1337
    mock_game.status = "started"
    mock_game.user_id = 1
    return mock_game


def test_start_game_should_populate_game_object():
    service = GameService()
    service.start_game(1)
    game = service.game
    assert game.columns>0
    assert game.rows>0
    assert game.mines_left>0
    assert game.board != None
    assert game.user_id == 1

def test_generate_board():
    mock_game = get_mock_game()

    service = GameService(mock_game)
    service._generate_board(20,20,10)

    assert len(mock_game.board)==20
    assert len(mock_game.board[0])==20

    covered_count = 0
    for row in mock_game.board:
        for column in row:
            if column["status"] == "C":
                covered_count += 1

    assert covered_count == 20*20

def test_place_mines():
    mock_game = get_mock_game()

    service = GameService(mock_game)
    service._generate_board(10,10,4)

    mine_count = 0
    for row in mock_game.board:
        for column in row:
            if column["value"]==-1:
                mine_count += 1
    assert mine_count == 4
            

def test_calculate_values():
    mock_game = get_mock_game

    service = GameService(mock_game)
    service._generate_board(5,5,4)

    mock_board_mines = [[-1, 0, 0, 0, 0],
                        [-1, 0, -1, 0, 0],
                        [-1, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0]
                        ]
    
    mock_board = []

    for row in mock_board_mines:
        mock_row = []
        for column in row:
            mock_row.append({"value": column, "status": "C"})
        mock_board.append(mock_row)

    mock_game.board = mock_board

    service._calculate_values(5, 5)

    values = []
    for row in mock_board:
        row_values = []
        for column in row:
            row_values.append(column["value"])
        values.append(row_values)

    expected_values = [[-1, 3, 1, 1, 0], 
                        [-1, 4, -1, 1, 0], 
                        [-1, 3, 1, 1, 0], 
                        [1, 1, 0, 0, 0], 
                        [0, 0, 0, 0, 0]
                        ]

    assert values==expected_values

def test_mask_board():
    mock_game = get_mock_game()
    service = GameService(mock_game)
    service.start_game(1)
    board = service.game.board
    board[0][0]["status"] = "U"
    board[1][1]["status"] = "F"
    board[2][2]["status"] = "?"

    masked = service._mask_board()

    assert isinstance(masked[0][0], int)
    assert masked[1][1]=="F"
    assert masked[2][2]=="?"
    assert masked[3][3]=="C"


def test_encode_game_info():
    service = GameService(get_mock_game())
    service._generate_board()
    encoded = service.encode_game_info()

    assert isinstance(encoded["board"], list)
    assert encoded["status"] == "started"
    assert encoded["mines_left"] == 5
    assert encoded["id"] == 1337
    


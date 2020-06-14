import pytest

from app import app, db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client


def register(client, email: str, password: str):
    return client.post('/register', json=dict(
        email=email,
        password=password
    ), follow_redirects=True)

def authenticate(client, email: str, password: str):
    return client.post('/authenticate', json=dict(
        email=email,
        password=password
    ), follow_redirects=True)

def get_token(client, email: str, password: str):
    response = authenticate(client, "ale@gmail.com", "bananasurf123")
    return response.json["token"]

def start_game(client):
    token = get_token(client, "ale@gmail.com", "bananasurf123")
    return client.post('/games',headers={"x-access-tokens": token})

def retrieve_game(client, game_id: int):
    token = get_token(client, "ale@gmail.com", "bananasurf123")
    return client.get(f'/games/{game_id}', headers={"x-access-tokens": token})

def list_games(client):
    token = get_token(client, "ale@gmail.com", "bananasurf123")
    return client.get('/games', headers={"x-access-tokens": token})

def clear_cell(client, game_id: int, row:int, column:int):
    token = get_token(client, "ale@gmail.com", "bananasurf123")
    return client.post(f'/games/{game_id}/clear',json={"row": row, "column": column}, headers={"x-access-tokens": token})

def toggle_cell(client, game_id: int, row:int, column:int):
    token = get_token(client, "ale@gmail.com", "bananasurf123")
    return client.post(f'/games/{game_id}/toggle',json={"row": row, "column": column}, headers={"x-access-tokens": token})


def test_register(client):
    response = register(client, "ale@gmail.com", "bananasurf123")
    assert response.status_code==200
    assert "id" in response.json["user"]

def test_register_should_fail_if_email_exists(client):
    response = register(client, "ale@gmail.com", "bananasurf123333")
    assert response.status_code==400
    assert "That email is already registered." == response.json["email"]

def test_register_should_fail_if_empty_email_or_password(client):
    response = register(client, "", "turboPunk01938")
    assert response.status_code==400
    assert "Not a valid email address." in response.json["email"]

    response = register(client, None, "turboPunk01938")
    assert response.status_code==400
    assert "Field may not be null." in response.json["email"]

    response = register(client, "bananas@pyjamas.com", None)
    assert response.status_code==400
    assert "Field may not be null." in response.json["password"]

def test_authenticate(client):
    response = authenticate(client, "ale@gmail.com", "bananasurf123")
    assert response.status_code==200
    assert "token" in response.json

def test_authenticate_wrong_credentials(client):
    response = authenticate(client, "wrong@email.com", "bananasurf123")
    assert response.status_code == 401
    assert "Authentication failed." == response.json["message"]

    response = authenticate(client, "ale@gmail.com", "WrongPassword")
    assert response.status_code == 401

def test_authenticate_missing_credentials(client):
    response = authenticate(client, None, None)
    assert response.status_code == 400
    assert "Field may not be null." in response.json["email"]
    assert "Field may not be null." in response.json["password"]


def test_start_new_game(client):
    response = start_game(client)
    assert "id" in response.json
    assert "board" in response.json
    assert response.json["status"] == "started"

def test_retrieve_game(client):
    response = start_game(client)
    game_id = response.json["id"]
    
    response = retrieve_game(client, game_id)

    assert response.json["id"] == game_id
    assert "board" in response.json

def test_list_games(client):
    response = list_games(client)

    assert "games" in response.json
    first = response.json["games"][0]
    assert "id" in first and isinstance(first["id"], int)
    assert "status" in first

def test_clear_cell(client):
    response = start_game(client)
    game_id = response.json["id"]

    game_data = retrieve_game(client, game_id)
    initial_board = game_data.json["board"]
    
    clear_response = clear_cell(client, game_id, 0, 0)
    
    new_board = clear_response.json["board"]

    assert initial_board[0][0] != new_board[0][0]
    assert new_board[0][0] != "C"

def test_toggle_cell(client):
    response = start_game(client)
    game_id = response.json["id"]

    game_data = retrieve_game(client, game_id)
    initial_board = game_data.json["board"]
    
    assert initial_board[0][0] == "C"
    
    toggle_response = toggle_cell(client, game_id, 0, 0)
    new_board = toggle_response.json["board"]

    assert new_board[0][0] == "F"
    

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

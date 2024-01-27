# tests/test_routes.py
import flaskr
import pytest

@pytest.fixture
def client():
    app = flaskr.create_app(test_config={'TESTING': True})
    with app.test_client() as client:
        yield client

def test_home_page(client):
    response = client.get('/hello')
    assert response.status_code == 200
    assert b'Hello, World!' in response.data

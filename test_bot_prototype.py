import pytest
from flask.testing import FlaskClient

import bot_prototype


@pytest.fixture
def client() -> FlaskClient:
    """Returns a client which can be used to test the HTTP API."""
    bot_prototype.app.config["TESTING"] = True

    with bot_prototype.app.test_client() as client:
        yield client


def test_send_message(client: FlaskClient):
    response = client.post("/user/test/message", json={"text": "Hello"})

    assert response.status_code == 200
    response_body = response.json

    assert len(response_body) == 2
    assert response_body[0] == "Welcome! Let me tell you a joke."


def test_retrieve_history(client: FlaskClient):
    client.post("/user/test_retrieve/message", json={"text": "Hello"})

    response = client.get("/user/test_retrieve/message")
    assert response.status_code == 200
    history = response.json

    assert len(history) == 3

    assert history[0] == {"message": "Hello", "type": "user"}
    assert history[1] == {"message": "Welcome! Let me tell you a joke.", "type": "bot"}
    assert history[2]["type"] == "bot"

    # Below are added tests
    client.post("/user/test_retrieve/message", json={"text": "Tell me more"})
    response2 = client.get("/user/test_retrieve/message")

    assert response2.status_code == 200
    history2 = response2.json
    assert len(history2) == 5
    assert history2[3] == {"message": "Tell me more", "type": "user"}
    assert history2[4]["type"] == "bot"

    client.post()
    response3 = client.get("/user/test1/message")
    history3 = response3.json

    assert response3.status_code == 404
    assert bool(history3) is False


class TestFinder:
    def __init__(self, client):
        self.case1 = "Chocolate"
        self.case2 = "bibi"
        self.case3 = "bi"

        self.response1 = client.post("/user/test_finder/message?bot_type=jokeFinder", json={"text": self.case1})
        self.response2 = client.post("/user/test_finder/message?bot_type=jokeFinder", json={"text": self.case2})
        self.response3 = client.post("/user/test_finder/message?bot_type=jokeFinder", json={"text": self.case3})

        self.response4 = client.get("/user/test_finder/message")

    def get_response_bodies(self):
        return {
            "1": self.response1.json,
            "2": self.response2.json,
            "3": self.response3.json,
            "4": self.response4.json,
        }


def test_send_finder_message(client: FlaskClient):
    o = TestFinder(client)
    bodies = o.get_response_bodies()
    assert o.response1.status_code == 200
    assert bodies["1"][0] == f"Welcome! Let me find you jokes about {o.case1}"
    assert len(bodies["1"]) == 2
    assert bodies["2"][0] == "Sorry! No jokes found. Try another word."
    assert bodies["3"][0] == "You have an invalid input, please try again. Size must be between 3 and 120."


def test_retrieve_finder_history(client: FlaskClient):
    o = TestFinder(client)
    re = o.response4
    body = o.get_response_bodies()["4"]

    assert re.status_code == 200


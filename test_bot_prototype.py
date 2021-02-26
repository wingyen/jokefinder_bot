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


# ------ Tests for ChuckNorrisJokeFinderBot, here I organise tests differently ------

scenario1 = ("Joke Exists", {"text": "Chocolate"})
scenario2 = ("Joke Not Found", {"text": "bibi"})
scenario3 = ("Invalid Input", {"text": "bi"})

joke_finder_route = "/user/test_finder/message?bot_type=jokeFinder"

def test_joke_finder_scenario1(client: FlaskClient):
    text = scenario1[1]["text"]
    re = client.post(joke_finder_route, json={"text": text})
    assert re.status_code == 200
    assert re.json[0] == f"Welcome! Let me find you jokes about {text}"


def test_joke_finder_scenario2(client: FlaskClient):
    text = scenario2[1]["text"]
    re = client.post(joke_finder_route, json={"text": text})
    assert re.status_code == 200
    assert re.json[0] == f"Sorry! No jokes found. Try another word."


def test_joke_finder_scenario3(client: FlaskClient):
    text = scenario3[1]["text"]
    re = client.post(joke_finder_route, json={"text": text})
    assert re.status_code == 200
    assert re.json[0] == f"You have an invalid input, please try again. Size must be between 3 and 120."

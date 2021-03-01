from collections import defaultdict
from contextlib import contextmanager
from typing import Text, Dict, List, Generator
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

inmemory_storage = defaultdict(list)


class Dialog(object):
    def __init__(
            self, dialog_id: Text, old_events: List[Dict]
    ) -> None:
        """Creates a dialog.

        Args:
            old_events: Events which happened earlier in this dialog.
        """
        self.dialog_id = dialog_id
        self.dialog_events = old_events
        self.number_old_events = len(old_events)

    def add_user_message(self, message: Text) -> None:
        self.dialog_events.append({"type": "user", "message": message})

    def add_bot_message(self, bot_messages: Text) -> None:
        self.dialog_events.append({"type": "bot", "message": bot_messages})

    def new_events_dict(self) -> List[Dict]:
        return self.dialog_events[self.number_old_events:]


@contextmanager
def dialog_persistence(conversation_id: Text) -> Generator[Dialog, None, None]:
    """Provides dialog history for a certain dialog.

    Saves any new events to the dialog storage when the context manager is exited.

    Args:
        conversation_id: The ID of the dialog. This is usually the same as the
            username.

    Returns:
        Conversation from the dialog storage.
    """
    old_conversation_events = inmemory_storage[conversation_id]
    conversation = Dialog(conversation_id, old_conversation_events)

    yield conversation


# random jokes
class ChuckNorrisRandomBot:
    def handle_message(self, message_text: Text, dialog: Dialog) -> None:
        dialog.add_user_message(message_text)

        if len(dialog.dialog_events) <= 1:
            dialog.add_bot_message(f"Welcome! Let me tell you a joke.")

        joke = self.retrieve_joke()
        dialog.add_bot_message(joke)

    def retrieve_joke(self) -> Text:
        response = requests.get("https://api.chucknorris.io/jokes/random")
        return response.json()["value"]

# Search for jokes
class ChuckNorrisJokeFinderBot:
    def handle_message(self, message_text: Text, dialog: Dialog) -> None:
        dialog.add_user_message(message_text)
        self.process_finder_message(message_text, dialog)

    def process_finder_message(self, message_text: Text, dialog: Dialog) -> None:
        message_size = len(message_text)
        conversation_size = len(dialog.dialog_events)

        if conversation_size <= 1:
            dialog.add_bot_message(f"Welcome! Let me find you jokes about {message_text}")

        if message_size in range(3, 121):
            """If message size is not between 3 and 120, 
            the api will return status 400 with error: Bad request
            """
            jokes = self.finder_retrieve_joke(message_text)
            if jokes:
                for joke in jokes:
                    dialog.add_bot_message(joke)
            else:
                dialog.add_bot_message("Sorry! No jokes found. Try another word.")
        else:
            dialog.add_bot_message("You have an invalid input, please try again. Size must be between 3 and 120.")

    def finder_retrieve_joke(self, message: Text) -> List:
        response = requests.get(f"https://api.chucknorris.io/jokes/search?query={message}")
        data = response.json()["result"]
        joke_list = []
        if data:
            joke_list.append([i["value"] for i in data])

        return joke_list


class BotFactory:
    def __init__(self, query_val: Text) -> None:
        self.query_val = query_val

    def choose_bot(self):
        if self.query_val == "jokeFinder":
            return ChuckNorrisJokeFinderBot()
        return ChuckNorrisRandomBot()


@app.route("/user/<dialog_id>/message", methods=["POST"])
def handle_user_message(dialog_id: Text) -> Text:
    """Returns a bot response for an incoming user message.

    :param dialog_id: : The id which serves as unique dialog ID.
        
    """
    message_text = request.json["text"]
    query_arg = request.args.get("bot_type", "")
    factory = BotFactory(query_arg)
    bot = factory.choose_bot()

    with dialog_persistence(dialog_id) as dialog:
        bot.handle_message(message_text, dialog)

        bot_responses = [
            x["message"] for x in dialog.new_events_dict() if x["type"] == "bot"
        ]

        return jsonify(bot_responses)


@app.route("/user/<username>/message", methods=["GET"])
def retrieve_conversation_history(username: Text) -> Text:
    """Returns all dialog events for a user's dialog.

    Args:
        username: The username which serves as unique dialog ID.

    Returns:
        All events in this dialog, which includes user and bot messages.
    """
    history = inmemory_storage[username]
    if history:
        return jsonify(history)
    else:
        return "[]", 404


if __name__ == "__main__":
    print("Serveris running")
    app.run(debug=True)

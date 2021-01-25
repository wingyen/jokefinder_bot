from collections import defaultdict
from contextlib import contextmanager
from typing import Text, Dict, List, Generator
import math
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

inmemory_storage = defaultdict(list)

class Conversation(object):
    def __init__(
        self, conversation_id: Text, old_conversation_events: List[Dict]
    ) -> None:
        """Creates a conversation.

        Args:
            old_conversation_events: Events which happened earlier in this conversation.
        """
        self.conversation_id = conversation_id
        self.conversation_events = old_conversation_events
        self.number_old_events = len(old_conversation_events)

    def addd_user_message(self, message: Text) -> None:
        self.conversation_events.append({"type": "user", "message": message})

    def add_bot_message(self, bot_messages: Text) -> None:
        self.conversation_events.append({"type": "bot", "message": bot_messages})

    def new_events_dict(self) -> List[Dict]:
        return self.conversation_events[self.number_old_events :]

@contextmanager
def conversationPersistence(
    conversation_id: Text,
) -> Generator[Conversation, None, None]:
    """Provides conversation history for a certain conversation.

    Saves any new events to the conversation storage when the context manager is exited.

    Args:
        conversation_id: The ID of the conversation. This is usually the same as the
            username.

    Returns:
        Conversation from the conversation storage.
    """
    old_conversation_events = inmemory_storage[conversation_id]
    # if old_conversation_events is None:
    #     old_conversation_events = []
    conversation = Conversation(conversation_id, old_conversation_events)

    yield conversation

    inmemory_storage[conversation_id] += conversation.new_events_dict()

class ChuckNorrisBot:
    def handle_message(self, message_text: Text, conversation: Conversation) -> None:
        conversation.addd_user_message(message_text)

        if len(conversation.conversation_events) <= 1:
            conversation.add_bot_message(f"Welcome! Let me tell you a joke.")

        joke = self.retrieve_joke()
        conversation.add_bot_message(joke)

    def retrieve_joke(self) -> Text:
        response = requests.get("https://api.chucknorris.io/jokes/random")

        return response.json()["value"]

@app.route("/user/<username>/message", methods=["POST"])
def handle_user_message(username: Text) -> Text:
    """Returns a bot response for an incoming user message.

    Args:
        username: The username which serves as unique conversation ID.

    Returns:
        The bot's responses.
    """
    message_text = request.json["text"]

    f = ChuckNorrisBot()

    with conversationPersistence(username) as conversation:
        f.handle_message(message_text, conversation)

        bot_responses = [
            x["message"] for x in conversation.new_events_dict() if x["type"] == "bot"
        ]

        return jsonify(bot_responses)

@app.route("/user/<username>/message", methods=["GET"])
def retrieve_conversation_history(username: Text) -> Text:
    """Returns all conversation events for a user's conversation.

    Args:
        username: The username which serves as unique conversation ID.

    Returns:
        All events in this conversation, which includes user and bot messages.
    """
    history = inmemory_storage[username]
    if history:
        return jsonify(history)
    else:
        return jsonify(history), 404

if __name__ == "__main__":
    print("Serveris running")
    app.run(debug=True)

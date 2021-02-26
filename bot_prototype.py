from collections import defaultdict
from contextlib import contextmanager
from typing import Text, Dict, List, Generator
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

    def add_user_message(self, message: Text) -> None:
        self.conversation_events.append({"type": "user", "message": message})

    def add_bot_message(self, bot_messages: Text) -> None:
        self.conversation_events.append({"type": "bot", "message": bot_messages})

    def new_events_dict(self) -> List[Dict]:
        return self.conversation_events[self.number_old_events:]


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


# random jokes
class ChuckNorrisBot:
    def handle_message(self, message_text: Text, conversation: Conversation) -> None:
        conversation.add_user_message(message_text)

        if len(conversation.conversation_events) <= 1:
            conversation.add_bot_message(f"Welcome! Let me tell you a joke.")

        joke = self.retrieve_joke()
        conversation.add_bot_message(joke)

    def retrieve_joke(self) -> Text:
        response = requests.get("https://api.chucknorris.io/jokes/random")
        return response.json()["value"]

# Search for jokes
class ChuckNorrisJokeFinderBot:
    def handle_message(self, message_text: Text, conversation: Conversation) -> None:
        conversation.add_user_message(message_text)
        self.process_finder_message(message_text, conversation)

    def process_finder_message(self, message_text: Text, conversation: Conversation) -> None:
        message_size = len(message_text)
        conversation_size = len(conversation.conversation_events)

        if conversation_size <= 1:
            conversation.add_bot_message(f"Welcome! Let me find you jokes about {message_text}")

        if message_size in range(3, 121):
            """If message size is not between 3 and 120, 
            the api will return status 400 with error: Bad request
            """
            jokes = self.finder_retrieve_joke(message_text)
            if jokes:
                for joke in jokes:
                    conversation.add_bot_message(joke)
            else:
                conversation.add_bot_message("Sorry! No jokes found. Try another word.")
        else:
            conversation.add_bot_message("You have an invalid input, please try again. Size must be between 3 and 120.")

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
        return ChuckNorrisBot()


@app.route("/user/<username>/message", methods=["POST"])
def handle_user_message(username: Text) -> Text:
    """Returns a bot response for an incoming user message.

    Args:
        username: The username which serves as unique conversation ID.

    Returns:
        The bot's responses.
    """
    message_text = request.json["text"]
    query_arg = request.args.get("bot_type", "")
    factory = BotFactory(query_arg)
    bot = factory.choose_bot()

    with conversationPersistence(username) as conversation:
        bot.handle_message(message_text, conversation)

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
        return "[]", 404


if __name__ == "__main__":
    print("Serveris running")
    app.run(debug=True)

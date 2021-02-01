## Rasa Bot Prototype

### Part 1: Fix the failing test
* Task 1:
    The generator in function 'conversationPersistence' will store a list of items in local storage temporary, don't need to duplicate the items.
    in line 56, it duplicates/adds on in-memory storage with the same conversation, thus 'test_retrieve_history' returns the double amount of conversations.
* Task 2: delete line 58, 'inmemory_storage[conversation_id] += conversation.new_events_dict()'

### Part 2: Code Review
* Task 1:
    - in line 32: no space before colon
    - delete un-used imports
    - delete comments in code. unless you have a good reason to leave it there, you can comment the reason additionally
    - function name "addd_user_message" has to be corrected as it was a spelling mistake -> "add_user_message"
    - should use lowercase with words separated by underscores when naming functions, like `conversationPersistence()`
    - in tests, you can have test classes to make post responses reusable for same bot.
* Task 2:
    - the `else` branch and continuous conversations in retrieve_conversation_history are not covered by the test.
    - added tests below the old code in 'test_retrieve_history'

###Part 3:
FYI: Also added tests for ChuckNorrisJokeFinderBot

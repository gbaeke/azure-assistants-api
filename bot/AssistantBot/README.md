# Echo bot with Assistant API modifications

This is an echo bot based on the quickstart on Azure Learn. Some things were added:

- assistant.py: initialise the in-memory vector store and provide helpers to work with assistants
- bot.py: modified echo bot to create a thread and add messages to it

Ensure you use `pip install -r requirements.txt` to install the required packages from both the AssistantBot folder as the bot folder.

Simply run `python app.py` to start the bot and connect the **Bot Framework Emulator** to `http://localhost:3978/api/messages`.
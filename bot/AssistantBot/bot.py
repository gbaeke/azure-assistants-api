# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount
import assistant


class MyBot(ActivityHandler):
    # See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.

    # add property to store thread id
    thread_id = None
    message_count = 0

    async def on_message_activity(self, turn_context: TurnContext):
        # add message to thread
        run = assistant.send_message(self.thread_id, turn_context.activity.text)
        if run is None:
            print("Result of send_message is None")
        tool_check = assistant.check_for_tools(run, self.thread_id)
        if tool_check:
            print("Tools ran...")
        else:
            print("No tools ran...")
        message = assistant.return_message(self.thread_id)

        await turn_context.send_activity(message)

        # increase message count
        self.message_count += 1
        await turn_context.send_activity("Message count: " + str(self.message_count))

    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                # Create a new thread
                self.thread_id = assistant.create_thread()
                self.message_count = 0
                await turn_context.send_activity("Hello. Thread id is: " + self.thread_id)

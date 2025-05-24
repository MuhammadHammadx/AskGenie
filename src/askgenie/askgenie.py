import chainlit as cl
from agents import (
    Agent,
    Runner,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)
from my_secrets import Secrets
from typing import cast
import json

secrets = Secrets()


@cl.on_chat_start
async def start():
    msg = cl.Message(content="Welcome to the chatbot!, I am here to help you.")
    await msg.send()

    external_client = AsyncOpenAI(
        base_url=secrets.gemini_api_url,
        api_key=secrets.gemini_api_key,
    )
    set_tracing_disabled(True)

    agent = Agent(
        name="AskGenie",
        instructions= "You are AskGenie, a smart, professional, and helpful AI assistant. "
                      "Answer user questions clearly and thoroughly, just like GPT-4. "
                      "Use natural, friendly, and informative language. Be concise but not overly brief—include enough detail to be genuinely helpful. "
                      "Adapt your response length based on the complexity of the question. If clarification is needed, ask follow-up questions before answering.",
        model=OpenAIChatCompletionsModel(
            openai_client=external_client,
            model=secrets.gemini_api_model,
        ),
    )

    cl.user_session.set("agent", agent)
    cl.user_session.set("chat_history", [])


@cl.on_message
async def main(message: cl.Message):
    msg = cl.Message(content="Thinking...")
    await msg.send()

    agent = cast(Agent, cl.user_session.get("agent"))
    chat_history: list = cl.user_session.get("chat_history") or []
    chat_history.append(
        {
            "role": "user",
            "content": message.content,
        }
    )

    try:
        result = Runner.run_sync(
            starting_agent=agent,
            input=chat_history,
        )
        msg.content = result.final_output
        cl.user_session.set("chat_history", result.to_input_list())
        await msg.update()
    except Exception as e:
        msg.content = (
            "An error occurred while processing your request. Please try again."
        )
        await msg.update()

@cl.on_chat_end
def end():
    chat_history: list = cl.user_session.get("chat_history") or []
    with open("chat_history.json", "w") as f:
        json.dump(chat_history, f, indent=4)
    
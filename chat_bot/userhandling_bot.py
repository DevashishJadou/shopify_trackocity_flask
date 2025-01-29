from openai import OpenAI
import os
import time

from flask import jsonify, request
from flask_cors import cross_origin
from .mongo_bot import chatbot_cd


openai_api_key = os.environ.get('_OPENAI_KEY_USER')
client = OpenAI(api_key=openai_api_key)


thread = client.beta.threads.create()

message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="I need to solve the equation `3x + 11 = 14`. Can you help me?",
)


run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id='asst_dXieZxw5u3diVp4ghC80ifJ1',
)



def wait_on_run(run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

run = wait_on_run(run, thread)

messages = client.beta.threads.messages.list(thread_id=thread.id)


@chatbot_cd.route('/website', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['POST', 'OPTIONS'], headers=['Content-Type'])
def sample():
    return None

import agent

agent = agent.Agent()

stream = agent.chat("my name is john", lambda x: print(str(x)))
if stream is not None:
    for message in stream:
        print(str(message))
agent.clear_chat()
stream = agent.chat("what is my name?", lambda x: print(str(x)))
if stream is not None:
    for message in stream:
        print(str(message))
from queue import Queue

recent_conversations = Queue(maxsize=6)

for i in range(10):
    recent_conversations.put(i)
    print(recent_conversations)


class MemoryQueue:
    """
    Simple memory queue with fixed size.
    """
    def __init__(self, size=6):
        self.memory = []
        self.size = size

    def add(self, msg):
        if len(self.memory) == self.size:
            self.memory.pop(0)
        self.memory.append(msg)

    def get_all(self):
        return self.memory

    def get(self, idx:int):
        return self.memory[idx]

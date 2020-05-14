

class Queue:
    def __init__(self, items=[]):
        self.queue = items


    def pop(self):
        item = self.queue[-1]
        self.queue = self.queue[:-1]
        return item


    def insert(self, item):
        self.queue = [item] + self.queue

    
    def isEmpty(self):
        return len(self.queue) == 0
    
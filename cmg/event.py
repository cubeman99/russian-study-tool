import threading
import queue


class Event:
    event_queue = queue.Queue()

    def __init__(self, *arg_types):
        self.__handlers = []
        self.__arg_types = tuple(arg_types)

    def get_types(self) -> list:
        return self.__arg_types

    def emit(self, *args):
        if threading.current_thread() is threading.main_thread():
            for handler in self.__handlers:
                handler(*args)
        else:
            # Events emitted on a background thread must be queued to
            # run on the main thread
            self.event_queue.put((self, args, list(self.__handlers)))

    def connect(self, handler) -> str:
        self.__handlers.append(handler)

    def disconnect(self, handler):
        self.__handlers.remove(handler)

import threading


class CallOnExit:
    def __init__(self, function):
        self.__function = function
        
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__function()

# https://www.oreilly.com/library/view/python-cookbook/0596001673/ch06s04.html
# Allowing Multithreaded Read Access While Maintaining a Write Lock
# Credit: Sami Hangaslammi
class ReadWriteLock:
    """
    A lock object that allows many simultaneous "read locks", but
    only one "write lock."
    """

    def __init__(self):
        self.__read_ready = threading.Condition(threading.RLock())
        self.__readers = 0

    def acquire_read(self):
        """
        Acquire a read lock. Blocks only if a thread has
        acquired the write lock.
        """
        self.__read_ready.acquire()
        try:
            self.__readers += 1
        finally:
            self.__read_ready.release()
        return CallOnExit(self.release_read)

    def release_read(self):
        """
        Release a read lock.
        """
        self.__read_ready.acquire()
        try:
            self.__readers -= 1
            if not self.__readers:
                self.__read_ready.notifyAll()
        finally:
            self.__read_ready.release()

    def acquire_write(self):
        """
        Acquire a write lock. Blocks until there are no
        acquired read or write locks.
        """
        self.__read_ready.acquire()
        while self.__readers > 0:
            self.__read_ready.wait()
        return CallOnExit(self.release_write)

    def release_write(self):
        """
        Release a write lock.
        """
        self.__read_ready.release()

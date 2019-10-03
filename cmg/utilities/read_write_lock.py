import threading
import traceback


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

    def __init__(self, verbose=False):
        self.__read_ready = threading.Condition(threading.RLock())
        self.__readers = 0
        self.__verbose = verbose

    def acquire_read(self):
        """
        Acquire a read lock. Blocks only if a thread has
        acquired the write lock.
        """
        self.__read_ready.acquire()
        try:
            self.__readers += 1
        finally:
            if self.__verbose:
                print("ACQUIRED READER: " + str(self.__readers))
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
            if self.__verbose:
                print("RELEASED READER: " + str(self.__readers))
            self.__read_ready.release()

    def acquire_write(self):
        """
        Acquire a write lock. Blocks until there are no
        acquired read or write locks.
        """
        self.__read_ready.acquire()
        if self.__verbose:
            print("ACQUIRED WRITE: " + str(self.__readers))
        while self.__readers > 0:
            if self.__verbose:
                traceback.print_stack()
            self.__read_ready.wait()
        return CallOnExit(self.release_write)

    def release_write(self):
        """
        Release a write lock.
        """
        if self.__verbose:
            print("RELEASED WRITE: " + str(self.__readers))
        self.__read_ready.release()

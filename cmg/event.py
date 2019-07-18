
class Event:
  def __init__(self, *arg_types):
    self.__handlers = []
    self.__arg_types = tuple(arg_types)

  def get_types(self) -> list:
    return self.__arg_types

  def emit(self, *args):
    for handler in self.__handlers:
      handler(*args)

  def connect(self, handler) -> str:
    self.__handlers.append(handler)

  def disconnect(self, handler):
    self.__handlers.remove(handler)
      
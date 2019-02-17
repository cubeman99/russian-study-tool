import sys
import re
import os
import traceback
import time
import inspect
import argparse
import colorama
colorama.init()
from colorama import Fore, Back, Style

COLOR_PASS = Fore.GREEN
COLOR_FAIL = Fore.RED

COLORS = {"test_pass": COLOR_PASS,
          "test_fail": COLOR_FAIL}

def plural(word, list):
  if len(list) != 1:
    return word + "s"
  else:
    return word

current_test = None

from .utils import *


def color_print(text):
  index = 0
  for match in re.finditer("{(?P<color>[_A-Za-z0-9]*)}", text):
    color_name = match.group("color")
    color = Style.RESET_ALL
    if color_name in COLORS:
      color = COLORS[color_name]

    sys.stdout.write(text[index:match.start()])
    sys.stdout.flush()
    index = match.end()

    sys.stdout.write(color)
    #set_text_color(color)

  sys.stdout.write(text[index:])
  sys.stdout.flush()


class Test:
  def __init__(self, test_case, test_name, test_func):
    self.test_case = test_case
    self.name = test_name
    self.test_func = test_func
    self.pass_count = 0
    self.fail_count = 0
    self.passed = True
    self.description = self.test_func.__doc__
    if self.description == None:
      self.description = ""

  def __str__(self):
    return "%s.%s" %(self.test_case.name, self.name)

  def expect(self, result, error_name="error"):
    if result:
      self.pass_count += 1
    else:
      self.fail_count += 1
      frame = inspect.stack()[2]
      color_print("%s(%d): %s: %s\n" %(frame.filename,
        frame.lineno, error_name,
        frame.code_context[0].lstrip().rstrip()))
    return result

  def run(self):
    color_print("{test_pass}[ RUN      ]{} %s\n" %(self))

    global current_test
    current_test = self

    self.pass_count = 0
    self.fail_count = 0

    self.test_case.test = self
    self.start_time = time.time()

    exception = None

    try:
      self.test_func()
    except Exception as e:
      exception = e
      self.fail_count += 1
      traceback.print_exc()

    self.end_time = time.time()
    self.elapsed = self.end_time - self.start_time
    self.test_case.test = None

    self.passed = (self.fail_count == 0)

    if self.passed:
      color_print("{test_pass}[       OK ]{}")
    else:
      color_print("{test_fail}[  FAILED  ]{}")

    color_print(" %s (%d ms)\n" %(self, self.elapsed))

    return self.passed


def is_a_test_function(name):
  return name.startswith("test_") and\
      name not in ("test_setup", "test_cleanup")

def expect(condition):
  if not current_test.expect(condition):
    color_print("  Actual: %r\n" %(condition))
    color_print("Expected: %r\n" %(True))

def expect_true(condition):
  if not current_test.expect(condition):
    color_print("  Actual: %r\n" %(condition))
    color_print("Expected: %r\n" %(True))

def expect_false(condition):
  if not current_test.expect(not condition):
    color_print("  Actual: %r\n" %(condition))
    color_print("Expected: %r\n" %(False))

def expect_eq(actual, expected):
  if not current_test.expect(actual == expected):
    color_print("  Actual: %r\n" %(actual))
    color_print("Expected: %r\n" %(expected))

def expect_ne(actual, expected):
  if not current_test.expect(actual != expected):
    color_print("  Actual: %r\n" %(actual))
    color_print("Expected: %r\n" %(expected))

class TestCase:
  def __init__(self, module):
    self.name = module.__name__
    all_functions = inspect.getmembers(module, inspect.isfunction)
    self.setup_func = getattr(module, "test_setup", None)
    self.cleanup_func = getattr(module, "test_cleanup", None)

    self.tests = []
    for name, func in all_functions:
      if is_a_test_function(name):
        self.tests.append(Test(self, name, func))

  def setup(self):
    """
    Perform test case setup code.
    """
    if self.setup_func:
      self.setup_func()

  def cleanup(self):
    """
    Perform test case cleanup code.
    """
    if self.cleanup_func:
      self.cleanup_func()

  def expect(self, condition):
    if not self.test.expect(condition):
      color_print("  Actual: %r\n" %(condition))
      color_print("Expected: %r\n" %(True))

  def expect_true(self, condition):
    if not self.test.expect(condition):
      color_print("  Actual: %r\n" %(condition))
      color_print("Expected: %r\n" %(True))

  def expect_false(self, condition):
    if not self.test.expect(not condition):
      color_print("  Actual: %r\n" %(condition))
      color_print("Expected: %r\n" %(False))

  def expect_eq(self, actual, expected):
    if not self.test.expect(actual == expected):
      color_print("  Actual: %r\n" %(actual))
      color_print("Expected: %r\n" %(expected))

  def expect_ne(self, actual, expected):
    if not self.test.expect(actual != expected):
      color_print("  Actual: %r\n" %(actual))
      color_print("Expected: %r\n" %(expected))

  def expect_exception(self, exception, func):
    raised = False
    try:
      func()
    except exception:
      raised = True
    else:
      raised = False
    if not self.test.expect(raised, error_name="exception error"):
      color_print("  Actual: no exception\n")
      color_print("Expected: %s exception\n" %(
        exception.__name__))

  def main(self):
    tests = [Test(self, getattr(self, t)) for t in dir(self) if t.startswith("test_")]
    color_print("{test_pass}[==========]{} Running %d %s from %s\n" %(
      len(tests), plural("test", tests), self.__class__.__name__))

    start_time = time.time()
    self.setup()


    test_pass_count = 0
    test_fail_count = 0

    passed_tests = []
    failed_tests = []

    color_print("{test_pass}[----------]{} %d %s from %s\n" %(
      len(tests), plural("test", tests), self.name))

    for test in tests:
      passed = test.run()
      if passed:
        passed_tests.append(test)
      else:
        failed_tests.append(test)

    color_print("{test_pass}[----------]{} %d %s from %s\n" %(
      len(tests), plural("test", tests), self.name))


    self.cleanup()
    end_time = time.time()
    elapsed = end_time - start_time

    color_print("{test_pass}[==========]{} %d %s from %s ran. (%d ms total)\n" %(
      len(tests), plural("test", tests), self.name, elapsed))

    self.passed = (len(failed_tests) == 0)
    color_print("{test_pass}[  PASSED  ]{} %d %s.\n" %(
      len(passed_tests), plural("test", passed_tests)))
    if not self.passed:
      color_print("{test_fail}[  FAILED  ]{} %d %s, listed below:\n" %(
        len(failed_tests), plural("test", failed_tests)))
      for test in failed_tests:
        color_print("{test_fail}[  FAILED  ]{} %s\n" %(
          test))

def str_count(count, name):
  if isinstance(count, list):
    count = len(count)
  if isinstance(count, tuple):
    count = len(count)
  if count == 1:
    return "%d %s" %(count, name)
  else:
    return "%d %ss" %(count, name)

def run_all_tests(test_modules):
  if not isinstance(test_modules, list):
    test_modules = [test_modules]
  test_cases = [TestCase(module) for module in test_modules]

  all_tests = []
  for test_case in test_cases:
    all_tests += test_case.tests

  color_print("{test_pass}[==========]{} Running %s from %s.\n" %(
    str_count(all_tests, "test"),
    str_count(test_cases, "test case")))
  color_print("{test_pass}[----------]{} Global test environment setup.\n")

  passed_tests = []
  failed_tests = []

  for test_case in test_cases:

    color_print("{test_pass}[----------]{} %s from %s\n" %(
      str_count(test_case.tests, "test"),
      test_case.name))
    test_case.setup()

    for test in test_case.tests:
      passed = test.run()
      if passed:
        passed_tests.append(test)
      else:
        failed_tests.append(test)

    test_case.cleanup()
    color_print("{test_pass}[----------]{} %s from %s (%d ms)\n" %(
      str_count(test_case.tests, "test"),
      test_case.name, 0))

  color_print("{test_pass}[----------]{} Global test environment cleanup.\n")
  color_print("{test_pass}[==========]{} %s from %s ran.\n" %(
    str_count(passed_tests + failed_tests, "test"),
    str_count(test_cases, "test case")))

  passed = (len(failed_tests) == 0)
  color_print("{test_pass}[  PASSED  ]{} %s.\n" %(
    str_count(passed_tests, "test")))
  if not passed:
    color_print("{test_fail}[  FAILED  ]{} %s, listed below:\n" %(
      str_count(failed_tests, "test")))
    for test in failed_tests:
      color_print("{test_fail}[  FAILED  ]{} %s\n" %(
        test))

  return

  global_dict = dict(globals)#globals())

  test_cases = []
  for key, value in global_dict.items():
    if inspect.isclass(value) and issubclass(value, TestCase) and value != TestCase:
      test_case = value()
      test_case_tests = []
      for test in test_case.tests:
        if test_list == None or test.name in test_list:
          test_case_tests.append(test)
      if len(test_case_tests) > 0:
        test_cases.append(test_case)

  tests = []
  for test_case in test_cases:
    tests += test_case.tests

  color_print("{test_pass}[==========]{} Running %d %s from %d %s.\n" %(
    len(tests), plural("test", tests),
    len(test_cases), plural("test case", tests)))
  color_print("{test_pass}[----------]{} Global test environment setup.\n")


  passed_tests = []
  failed_tests = []

  for test_case in test_cases:
    test_case_tests = []
    for test in test_case.tests:
      if test_list == None or test.name in test_list:
        test_case_tests.append(test)

    color_print("{test_pass}[----------]{} %d %s from %s\n" %(
      len(test_case.tests), plural("test", test_case.tests),
      test_case.name))
    test_case.setup()

    for test in test_case_tests:
      passed = test.run()
      if passed:
        passed_tests.append(test)
      else:
        failed_tests.append(test)

    test_case.cleanup()
    color_print("{test_pass}[----------]{} %d %s from %s (%d ms)\n" %(
      len(test_case_tests), plural("test", test_case.tests),
      test_case.name, 0))

  color_print("{test_pass}[----------]{} Global test environment cleanup.\n")
  color_print("{test_pass}[==========]{} %d %s from %d %s ran.\n" %(
    len(passed_tests) + len(failed_tests), plural("test", tests),
    len(test_cases), plural("test case", tests)))

  passed = (len(failed_tests) == 0)
  color_print("{test_pass}[  PASSED  ]{} %d %s.\n" %(
    len(passed_tests), plural("test", passed_tests)))
  if not passed:
    color_print("{test_fail}[  FAILED  ]{} %d %s, listed below:\n" %(
      len(failed_tests), plural("test", failed_tests)))
    for test in failed_tests:
      color_print("{test_fail}[  FAILED  ]{} %s\n" %(
        test))

  if len(failed_tests) == 0:
    exit(0)
  else:
    exit(1)



def unit_test_main(globals):
  # Parse the command line arguments
  parser = argparse.ArgumentParser(description="Run the cardgame client.")
  parser.add_argument("host", metavar="HOST", type=str,
    default=DEFAULT_HOST, nargs="?",
    help="optional host IP address and optional port to connect to (in the format \"host:port\"). The default host is '%s' and the default port is %d." %(DEFAULT_HOST, DEFAULT_PORT))
  parser.add_argument("-p", "--prompt", action="store_true",
    help="prompt the user for the server's IP address")
  args = parser.parse_args()

  run_all_tests(globals)


import pygame
import time
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController
from cmg.application import *
from cmg.graphics import *
from cmg.input import *

class PedalControlApp:

  def __init__(self):
    self.done = False
    pygame.init()
    self.screen = pygame.display.set_mode([800, 600])
    pygame.display.set_caption("CMG")
    pygame.joystick.init()
    self.clock = pygame.time.Clock()
    self.keyboard = KeyboardController()
    self.mouse = MouseController()
    self.textPrint = TextPrint()
    self.joystick_ready = False
    
    self.input_steering = Input(index=0, name="Steering")
    self.input_middle = Input(index=1, name="Brake", reversed=True, max=1, min=-1)
    self.input_left = Input(index=2, name="Clutch", reversed=True, max=1, min=-1)
    self.input_right = Input(index=3, name="Gas", reversed=True, max=1, min=-1)
    self.axis_inputs = []
    self.axis_inputs += [self.input_steering, self.input_right, self.input_left, self.input_middle]
    self.inputs = self.axis_inputs + []

    self.binds = []
    hard_threshold = 0.7
    self.bind_left_soft = InputBind(self.input_left, min=0.05, max=hard_threshold)
    self.bind_left_hard = InputBind(self.input_left, min=hard_threshold)
    self.bind_right_soft = InputBind(self.input_right, min=0.05, max=hard_threshold)
    self.bind_right_hard = InputBind(self.input_right, min=hard_threshold)
    self.bind_middle = InputBind(self.input_middle, min=0.01)
    ms = self.bind_middle
    ls = self.bind_left_soft
    rs = self.bind_right_soft
    lh = self.bind_left_hard
    rh = self.bind_right_hard

    self.gestures = []
    soft_delay = 0.1
    hard_delay = 0.1
    self.gesture_ctrl_tab = self.add_gesture(bind=lh, exclude=rs | ms, name="Ctrl+Tab", delay=soft_delay, callback=self.ctrl_tab)
    self.gesture_ctrl_shift_tab = self.add_gesture(bind=lh, exclude=rs | ~ms, name="Ctrl+Shift+Tab", delay=soft_delay, callback=self.ctrl_shift_tab)
    #self.x = self.add_gesture(bind=rs, exclude=ls | ms, name="Scroll Down", delay=soft_delay)
    #self.x = self.add_gesture(bind=rs, exclude=ls | ~ms, name="Scroll Down", delay=soft_delay)
    self.gesture_home = self.add_gesture(bind=rh, exclude=ms | ~ls, name="Home", callback=self.home)
    self.gesture_end = self.add_gesture(bind=rh, exclude=ms | ls, name="End", callback=self.end)
    self.gesture_enter_mouse_mode = self.add_gesture(bind=ms & ls, name="Enter Mouse Mode", delay=0.05, callback=self.enter_mouse_mode)
    self.gestures = [self.gesture_ctrl_tab,
                     self.gesture_ctrl_shift_tab,
                     self.gesture_home,
                     self.gesture_end,
                     self.gesture_enter_mouse_mode]

    self.gesture_click = self.add_gesture(bind=ms & ~ls, name="Mouse Left Click", delay=0.05, callback=lambda: self.mouse.click(Button.left))
    self.gesture_exit_mouse_mode = self.add_gesture(bind=ms & ls, name="Exit Mouse Mode", delay=0.05, callback=self.exit_mouse_mode)
    self.mouse_mode_gestures = [self.gesture_click, self.gesture_exit_mouse_mode]
    self.mouse_mode = False

    self.mouse_dir = [1, 1]
    self.mouse_moving = [False, False]

    #self.x = self.add_gesture(bind=lh, exclude=rs, name="Left Hard", delay=hard_delay, callback=self.ctrl_tab)
    #self.x = self.add_gesture(bind=rs, exclude=ls, name="Right Soft", delay=soft_delay)
    #self.x = self.add_gesture(bind=rh, exclude=ls, name="Right Hard", delay=hard_delay)
    #self.x = self.add_gesture(bind=ls & rs, name="Both Soft", delay=soft_delay)
    #self.x = self.add_gesture(bind=lh & rh, name="Both Hard", delay=hard_delay)
    #self.x = self.add_gesture(bind=self.bind_middle, name="Back", delay=soft_delay)

    self.joystick = pygame.joystick.Joystick(0)
    self.joystick.init()

  def enter_mouse_mode(self):
    self.mouse_mode = True
    for gesture in self.gestures + self.mouse_mode_gestures:
      gesture.clear()
    d = 5
    s = 0.05
    self.mouse.move(d, 0)
    time.sleep(s)
    self.mouse.move(-d, -d)
    time.sleep(s)
    self.mouse.move(-d, d)
    time.sleep(s)
    self.mouse.move(d, d)
    time.sleep(s)
    self.mouse.move(0, -d)
    time.sleep(s)

  def exit_mouse_mode(self):
    self.mouse_mode = False
    for gesture in self.gestures + self.mouse_mode_gestures:
      gesture.clear()
    d = 2
    s = 0.05
    self.mouse.move(d, -d)
    time.sleep(s)
    self.mouse.move(-d * 2, 0)
    time.sleep(s)
    self.mouse.move(0, d * 2)
    time.sleep(s)
    self.mouse.move(d * 2, 0)
    time.sleep(s)
    self.mouse.move(-d, -d)
    time.sleep(s)

  def ctrl_shift_tab(self):
    self.keyboard.press(Key.ctrl_l)
    self.keyboard.press(Key.shift_l)
    self.keyboard.press(Key.tab)
    self.keyboard.release(Key.ctrl_l)
    self.keyboard.release(Key.shift_l)
    self.keyboard.release(Key.tab)

  def ctrl_tab(self):
    self.keyboard.press(Key.ctrl_l)
    self.keyboard.press(Key.tab)
    self.keyboard.release(Key.ctrl_l)
    self.keyboard.release(Key.tab)

  def page_up(self):
    self.keyboard.press(Key.page_up)
    self.keyboard.release(Key.page_up)

  def page_down(self):
    self.keyboard.press(Key.page_down)
    self.keyboard.release(Key.page_down)

  def end(self):
    self.keyboard.press(Key.end)
    self.keyboard.release(Key.end)
  def home(self):
    self.keyboard.press(Key.home)
    self.keyboard.release(Key.home)

  def add_gesture(self, **kwargs):
    gesture = Gesture(**kwargs)
    self.gestures.append(gesture)
    return gesture

  def quit(self):
    self.done = True

  def run(self):
    self.done = False
    while not self.done:
      # EVENT PROCESSING STEP
      keys = pygame.key.get_pressed()
      for event in pygame.event.get(): # User did something
        if event.type == pygame.QUIT:
          self.quit()
        elif event.type == pygame.KEYDOWN:
          if event.key == pygame.K_ESCAPE:
            self.quit()

      if not self.joystick_ready:
        for axis in range(self.joystick.get_numaxes()):
          if self.joystick.get_axis(axis) != 0:
            self.joystick_ready = True

      gestures = self.gestures
      if self.mouse_mode:
        gestures = self.mouse_mode_gestures

      if self.joystick_ready:
        for input in self.axis_inputs:
          input.update(self.joystick.get_axis(input.index))
        for gesture in gestures:
          gesture.update()

      if self.mouse_mode:
        
        movement = [0, 0]
        for axis, input in enumerate([self.input_left, self.input_right]):
          amount = input.get_amount()
          if self.mouse_moving[axis]:
            if amount < 0.05:
              self.mouse_dir[axis] = -self.mouse_dir[axis]
              self.mouse_moving[axis] = False
            else:
              movement[axis] = int(1 + amount * amount * 10) * self.mouse_dir[axis]
          elif amount >= 0.05:
            self.mouse_moving[axis] = True
        if any(self.mouse_moving):
          self.mouse.move(movement[0], movement[1])

      else:

        scroll_amount = self.input_right.get_amount() * self.input_right.get_amount() * 600
        scroll_amount = int(scroll_amount)
        if scroll_amount != 0:
          if self.input_left.get_amount() >= 0.01:
            if not self.gesture_home.reset:
              self.mouse.scroll(0, scroll_amount)  # up
          else:
            if not self.gesture_end.reset:
              self.mouse.scroll(0, -scroll_amount)  # down

      self.screen.fill(WHITE)
      self.textPrint.reset()

      mode_name = "Normal Mode"
      if self.mouse_mode:
        mode_name = "Mouse Mode"
      self.textPrint.print(self.screen, mode_name)
      self.textPrint.print(self.screen, "")

      for input in self.inputs:
        self.textPrint.print(self.screen, "Input '{}' = {:.4f}".format(input.name, input.amount))
      for gesture in self.gestures:
        percent = (100 * gesture.percent) if gesture.percent is not None else 0.0
        self.textPrint.print(self.screen, "Gesture '{}' = {}, {}, {:.0f}%".format(
          gesture.name, gesture.is_pressed(), gesture.is_down(), percent))

      pygame.display.flip()

      # Limit to 20 frames per second
      #time.sleep(0.05)
      self.clock.tick(60)
    
    pygame.quit()


if __name__ == "__main__":
  app = PedalControlApp()
  app.run()

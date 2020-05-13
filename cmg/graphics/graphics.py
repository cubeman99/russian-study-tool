import pygame
from pygame import Rect
from enum import IntFlag
import cmg
from cmg.color import Colors
from cmg.graphics.image import Image
from study_tool.russian.word import AccentedText


class Align(IntFlag):
    """
    Text align bit flags.
    """
    Center = 0x1
    Left = 0x2
    Right = 0x4
    Bottom = 0x8
    Top = 0x10
    Middle = 0x20
    TopLeft = Top | Left
    TopRight = Top | Right
    TopCenter = Top | Center
    BottomLeft = Bottom | Left
    BottomRight = Bottom | Right
    BottomCenter = Bottom | Center
    MiddleLeft = Middle | Left
    MiddleRight = Middle | Right
    Centered = Center | Middle


class Graphics:
    """
    Class used to draw graphics.
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.Font(None, 38)
        self.accent_input_chars = "'´`"
        self.accent_render_char = "´"
        self.__translation = cmg.Vec2(0, 0)
        self.__cached_text_bitmaps_prev = {}
        self.__cached_text_bitmaps = {}

    def get_viewport(self) -> pygame.Rect:
        return self.screen.get_rect()

    def is_rect_in_viewport(self, rect) -> bool:
        viewport = pygame.Rect(self.screen.get_rect())
        viewport.left -= self.__translation.x
        viewport.top -= self.__translation.y
        return viewport.colliderect(rect)

    def clear(self, color):
        self.screen.fill(tuple(color))

    def set_translation(self, x, y):
        self.__translation = cmg.Vec2(x, y)

    #-------------------------------------------------------------------------
    # Shapes
    #-------------------------------------------------------------------------

    def draw_image(self, image: cmg.Image, x, y=None):
        if isinstance(image, cmg.Image):
            image = image.get_surface()
        if isinstance(x, Rect):
            image = pygame.transform.scale(
                image, (x.width, x.height))
            self.blit(image, (x.left, x.top))
        elif y is None:
            self.blit(image, tuple(x))
        else:
            self.blit(image, (x, y))

    def draw_image_part(self, image, dest: tuple, source: Rect):
        self.screen.blit(source=image,
                         dest=(cmg.Vec2(dest) + self.__translation).totuple(),
                         area=source)

    def draw_rect(self, x, y=None, width=None, height=None, color=Colors.BLACK, thickness=1):
        if isinstance(x, pygame.Rect):
            rect = pygame.Rect(x)
        else:
            rect = pygame.Rect(x, y, width, height)
        rect.left += self.__translation.x
        rect.top += self.__translation.y
        pygame.draw.rect(self.screen, tuple(color), rect, thickness)

    def fill_rect(self, x, y=None, width=None, height=None, color=Colors.BLACK):
        if isinstance(x, pygame.Rect):
            rect = pygame.Rect(x)
        else:
            rect = pygame.Rect(x, y, width, height)
        rect.left += self.__translation.x
        rect.top += self.__translation.y
        if color.a < 255:
            if rect.width <= 0 or rect.height <= 0:
                raise Exception("Invalid rect size: {}x{}".format(rect.width, rect.height))
            s = pygame.Surface((rect.width, rect.height))
            s.set_alpha(color.a) 
            s.fill((color.r, color.g, color.b))
            self.screen.blit(s, (rect.left, rect.top))
        else:
            pygame.draw.rect(self.screen, tuple(color), rect, 0)

    #-------------------------------------------------------------------------
    # Text
    #-------------------------------------------------------------------------

    def measure_text(self, text, font=None):
        """
        Returns the width and height in pixels needed to render text with the
        given font.
        """
        if font is None:
            font = self.font
        if isinstance(font, cmg.Font):
            font = font.get_pygame_font()
        if isinstance(text, AccentedText):
            return cmg.Vec2(font.size(text.text))
        return cmg.Vec2(font.size(text))

    def get_font_to_fit(self, text, width: float,
                        fonts: list) -> pygame.font.Font:
        """
        Returns the largest font from a list of fonts that will allow the given
        text to fit within the specified width.
        """
        fonts = sorted(fonts, key=lambda font: font.get_height(), reverse=True)
        for font in fonts:
            w, _ = self.measure_text(text=text, font=font)
            if w <= width:
                return font
        return font

    def get_font_size_to_fit(self,
                             text,
                             min_font_size: int,
                             max_font_size: int,
                             width: float) -> int:
        """
        Returns the largest font from a list of fonts that will allow the given
        text to fit within the specified width.
        """
        assert max_font_size >= min_font_size
        for font_size in range(max_font_size, min_font_size, -1):
            font = cmg.Font(font_size)
            w, _ = font.measure(AccentedText(text).text)
            if w <= width:
                return font_size
        return min_font_size

    def draw_text(self, x, y, text, color=Colors.BLACK, font=None, align=Align.TopLeft, accented=True):
        """
        Draw accented text.
        """
        if accented:
            self.draw_accented_text(x, y, text, color, font=font, align=align)
        else:
            w, h = font.size(text)
            if Align.Center in align:
                x -= w / 2
            if Align.Middle in align:
                y -= h / 2
            if Align.Right in align:
                x -= w
            if Align.Bottom in align:
                y -= h

            # Draw text
            text_bitmap = font.render(text, True, tuple(color))
            self.blit(text_bitmap, (x, y))

    def get_accent_bitmap(self, font, color):
        return font.render(self.accent_render_char, True, tuple(color))

    def draw_accented_text(self, x, y, text, color=Colors.BLACK, font=None, align=Align.TopLeft):
        """
        Draw accented text.
        """
        if isinstance(font, cmg.Font):
            font = font.get_pygame_font()
        if font is None:
            font = self.font

        text = AccentedText(text)
        w, h = font.size(text.text)
        if Align.Center in align:
            x -= w / 2
        if Align.Middle in align:
            y -= h / 2
        if Align.Right in align:
            x -= w
        if Align.Bottom in align:
            y -= h

        text_bitmap = self.get_cached_text(
            text=repr(text), font=font, color=tuple(color))

        if not text_bitmap:
            # Draw text
            text_bitmap = font.render(text.text, True, tuple(color))

            # Draw accent marks
            if text.accents:
                accent_bitmap = self.get_accent_bitmap(font=font, color=color)
                accent_half_width = int(accent_bitmap.get_width() / 2)
                for accent_index in text.accents:
                    w1, _ = font.size(text.text[:accent_index])
                    w2, _ = font.size(text.text[:accent_index + 1])
                    center_x = (w2 + w1) / 2
                    text_bitmap.blit(accent_bitmap, (center_x - accent_half_width, 0))

            self.cache_text(bitmap=text_bitmap, font=font,
                            text=repr(text), color=tuple(color))

        self.blit(text_bitmap, cmg.Vec2(x, y))

    def blit(self, image, dest):
        self.screen.blit(image, (cmg.Vec2(dest) + self.__translation).totuple())

    def recache(self):
        self.__cached_text_bitmaps_prev = self.__cached_text_bitmaps
        self.__cached_text_bitmaps = {}

    def cache_text(self, bitmap, text, font, color):
        key = (text, self.get_font_key(font), color)
        self.__cached_text_bitmaps[key] = bitmap

    def get_cached_text(self, text, font, color):
        key = (text, self.get_font_key(font), color)
        result = self.__cached_text_bitmaps_prev.get(key, None)
        if result:
            self.__cached_text_bitmaps[key] = result
        return result

    def get_font_key(self, font):
        return (font.get_linesize(), font.get_bold(),
                font.get_italic(), font.get_underline())

# This is a simple class that will help us print to the self.screen
# It has nothing to do with the joysticks, just outputting the
# information.
class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 38)

    def print(self, screen, textString):
        textBitmap = self.font.render(textString, True, tuple(Colors.BLACK))
        screen.blit(textBitmap, [self.x, self.y])
        self.y += self.line_height

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 30

    def indent(self):
        self.x += 10

    def unindent(self):
        self.x -= 10

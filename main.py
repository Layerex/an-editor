#!/usr/bin/env python3

import sys
from abc import ABC, abstractmethod, abstractstaticmethod
from enum import auto, Enum
from typing import Callable, Iterable

import pygame
import pygame.locals


class Point:
    pass


class Cursor(Point):
    pass


class Buffer:
    pass


class Window:
    """То, в чём рисуется буфер."""

    pass


class Workspace:
    """Набор окон, как-либо расположенных."""

    pass


class Matcher:
    """Штука, которую можно вставлять в traits __неполного__ ивента, для того, чтобы проверять сложные условия.
    Должна уметь сравниваться с None и с ожидаемым типом."""

    def _eq(self, other) -> bool:
        pass

    def __eq__(self, other):
        return other != None and self._eq(other)

    def __ne__(self, other):
        return not self == other


class CharMatcher(Matcher):
    def _eq(self, other: str) -> bool:
        return len(other) == 1


class Event:
    """Ивенты могут быть полными и неполными.
    Отправлять можно только полные, привязывать же handle можно и к неполным,
    тогда незаданные свойства будут пропускаться при проверке."""

    def __init__(self, mute: bool = False):
        self.mute = mute

    def is_complete(self) -> bool:
        # Надо бы как-то кешировать результать этой функции и обновлять его при изменении ивента
        # А то медленно
        for value in self.traits().values():
            if value == None:
                return False
        return True

    def traits(self) -> dict:
        traits = {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith("__") and not callable(key)
        }
        del traits["mute"]
        return traits


class QuitEvent(Event):
    def __init__(self, mute: bool = False):
        super().__init__(mute)


class KeyDownEvent(Event):
    def __init__(self, key=None, modifiers=None, char=None, mute: bool = False):
        super().__init__(mute)
        self.key = key
        self.modifiers = modifiers
        self.char = char


class State(ABC):
    """Публичное состояние бекэнда, считываемое фронтэндом"""

    def __init__(self):
        pass


class Backend(State):
    def __init__(self):
        super().__init__()

    def char_typed_handle(self, event: KeyDownEvent) -> None:
        print(event.char)


class Frontend(ABC):
    @abstractmethod
    def _get_events(self) -> Iterable:
        pass

    # def handle_input(self, event_handler: EventHandler) -> None:
    def handle_input(self, event_handler) -> None:
        for low_level_event in self._get_events():
            event_handler.handle(self._convert_event(low_level_event))

    @abstractstaticmethod
    def _convert_event(self, low_level_event) -> Event:
        pass

    @abstractmethod
    def render(self, backend: Backend) -> None:
        pass


class PygameFrontend(Frontend):
    FPS = 60  # Надо бы VSync запилить
    BACKGROUND = 255, 255, 255
    SIZE = WIDTH, HEIGHT = 800, 600
    CAPTION = "An editor"

    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.window_surface = pygame.display.set_mode(self.SIZE)
        pygame.display.set_caption(self.CAPTION)

    def _get_events(self) -> Iterable:
        return (event for event in pygame.event.get())

    def _convert_event(self, low_level_event: pygame.event.Event) -> Event:
        if low_level_event.type == pygame.locals.QUIT:
            event = QuitEvent()
        elif low_level_event.type == pygame.locals.KEYDOWN:
            event = KeyDownEvent(
                low_level_event.key, low_level_event.mod, low_level_event.unicode
            )
        else:
            event = Event()
        return event

    def render(self, backend: Backend) -> None:
        self.window_surface.fill(self.BACKGROUND)

        pygame.display.flip()
        pygame.display.update()
        pygame.time.wait(1000 // self.FPS)


class EventHandler:
    """Вызывает каллбеки бекэнда"""

    def __init__(self):
        self._events = []

    def add(self, event_description: Event, handle: Callable[[Event], None]) -> None:
        self._events.append((event_description, handle))

    def mute(self, event: Event) -> None:
        pass

    def unmute(self, event: Event) -> None:
        pass

    def remove(self, event: Event) -> None:
        del self.events[event]

    def handle(self, event: Event) -> None:
        assert event.is_complete(), "Incomplete event emitted"
        if not event.mute:
            for event_description, handle in self._events:
                if not event_description.mute and type(event) == type(
                    event_description
                ):
                    event_traits = event.traits()
                    description_traits = event_description.traits()
                    for trait in description_traits:
                        if (
                            description_traits[trait] != None
                            and description_traits[trait] != event_traits[trait]
                        ):
                            break
                    else:
                        handle(event)


class Editor:
    def __init__(self):
        self.exit_condition = False
        self.backend = Backend()
        self.frontend = PygameFrontend()
        self.event_handler = EventHandler()

        self._setup_handlers()

    def run(self) -> None:
        while not self.exit_condition:
            self.update()
            self.render()

    def update(self) -> None:
        self.frontend.handle_input(self.event_handler)

    def render(self) -> None:
        self.frontend.render(self.backend)

    def _setup_handlers(self) -> None:
        self.event_handler.add(QuitEvent(), self.quit)
        self.event_handler.add(
            KeyDownEvent(None, None, CharMatcher()), self.backend.char_typed_handle
        )

    def quit(self, event) -> None:
        self.exit_condition = True


def main() -> None:
    editor = Editor()
    editor.run()


if __name__ == "__main__":
    main()

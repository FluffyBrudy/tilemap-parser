from typing import Any
import pygame
from pygame.typing import RectLike

if not pygame.get_init():
    pygame.init()

font = pygame.font.SysFont(None, 15)

_DEBUG_REFS = []


class Debug:
    @staticmethod
    def add(data: dict):
        _DEBUG_REFS.append(data)

    @staticmethod
    def clear():
        _DEBUG_REFS.clear()

    @staticmethod
    def change_font(size: int):
        global font
        font = pygame.font.SysFont(None, size)

    @staticmethod
    def draw_all(surface: pygame.Surface):
        """Draws all registered debug visuals."""
        if not _DEBUG_REFS:
            return

        # Sort by priority (high first)
        _DEBUG_REFS.sort(key=lambda d: d["priority"], reverse=True)

        # Draw stacked debug texts first
        text_refs = [d for d in _DEBUG_REFS if d.get("type") == "text"]
        if text_refs:
            spacing = font.get_height() + 4
            for i, d in enumerate(text_refs):
                surf = d["surf"]
                w, h = surface.get_size()
                rw, rh = surf.get_size()
                x = (w - rw) // 2
                # y = (h - rh) // 2 - i * spacing
                y = i * spacing
                surface.blit(surf, (x, y))

        other_refs = [d for d in _DEBUG_REFS if d.get("type") != "text"]
        drawn_rects = []
        for d in other_refs:
            rect = d["rect"]
            if not any(rect.colliderect(r) for r in drawn_rects):
                d["draw"](surface)
                drawn_rects.append(rect)

        _DEBUG_REFS.clear()


def pgdebug(text: Any, priority=0):
    textsurf = font.render(str(text), True, (255, 255, 255))
    Debug.add(
        {
            "type": "text",
            "surf": textsurf,
            "priority": priority,
        }
    )


def pgdebug_rect(surface: pygame.Surface, rect_like: RectLike, w=1, priority=0):
    rect = pygame.Rect(rect_like)

    if 0 < w < 10:
        pygame.draw.rect(surface, (255, 0, 0, 255), rect, w)
        return

    if w == 0:

        def draw_fn(surf: pygame.Surface):
            pygame.draw.rect(surf, (255, 0, 0, 255), rect, w)

        Debug.add(
            {
                "type": "rect",
                "rect": rect,
                "draw": draw_fn,
                "priority": priority,
            }
        )

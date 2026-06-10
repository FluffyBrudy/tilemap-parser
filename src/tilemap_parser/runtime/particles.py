from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

import pygame
from pygame import Rect, Surface

from ..parser.node_parse import ParsedNode
from ..parser.particle import ParticleSystemConfig

PARTICLE_TEXTURE_SIZE = 24
MAX_DT = 0.05


class ParticleEmitterNode:
    def __init__(self, parsed: ParsedNode) -> None:
        self.node_id = parsed.node_id
        self.name = parsed.name
        self.node_type = parsed.node_type
        self._rect = Rect(parsed.area.x, parsed.area.y, parsed.area.w, parsed.area.h)
        self.layer_name = parsed.layer_name
        self.group = parsed.group
        self.config = ParticleSystemConfig.from_dict(
            parsed.properties, name=parsed.name
        )

    @property
    def rect(self) -> Rect:
        return self._rect

    @rect.setter
    def rect(self, r: Rect) -> None:
        self._rect = r

    def __repr__(self) -> str:
        return (
            f"ParticleEmitterNode(id={self.node_id!r}, name={self.name!r}, "
            f"rect={self._rect}, layer={self.layer_name!r})"
        )


_TEXTURE_CACHE: Dict[str, Surface] = {}


def _make_circle_texture() -> Surface:
    s = Surface((PARTICLE_TEXTURE_SIZE, PARTICLE_TEXTURE_SIZE), pygame.SRCALPHA)
    cx = cy = PARTICLE_TEXTURE_SIZE // 2
    r = PARTICLE_TEXTURE_SIZE // 2 - 1
    for i in range(r, 0, -1):
        t = i / r
        alpha = int(255 * (1 - t * t))
        pygame.draw.circle(s, (255, 255, 255, alpha), (cx, cy), i)
    return s


def _make_square_texture() -> Surface:
    s = Surface((PARTICLE_TEXTURE_SIZE, PARTICLE_TEXTURE_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(
        s,
        (255, 255, 255, 255),
        Rect(2, 2, PARTICLE_TEXTURE_SIZE - 4, PARTICLE_TEXTURE_SIZE - 4),
        border_radius=2,
    )
    return s


def _make_diamond_texture() -> Surface:
    s = Surface((PARTICLE_TEXTURE_SIZE, PARTICLE_TEXTURE_SIZE), pygame.SRCALPHA)
    cx = PARTICLE_TEXTURE_SIZE // 2
    cy = PARTICLE_TEXTURE_SIZE // 2
    r = PARTICLE_TEXTURE_SIZE // 2 - 2
    points = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
    pygame.draw.polygon(s, (255, 255, 255, 255), points)
    return s


def _make_star_texture() -> Surface:
    s = Surface((PARTICLE_TEXTURE_SIZE, PARTICLE_TEXTURE_SIZE), pygame.SRCALPHA)
    cx = cy = PARTICLE_TEXTURE_SIZE // 2
    r = PARTICLE_TEXTURE_SIZE // 2 - 2
    points: List[Tuple[float, float]] = []
    for i in range(8):
        angle = math.pi * 2 * i / 8 - math.pi / 2
        radius = r if i % 2 == 0 else r * 0.4
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    pygame.draw.polygon(s, (255, 255, 255, 255), points)
    return s


def _make_sparkle_texture() -> Surface:
    s = Surface((PARTICLE_TEXTURE_SIZE, PARTICLE_TEXTURE_SIZE), pygame.SRCALPHA)
    cx = cy = PARTICLE_TEXTURE_SIZE // 2
    half = PARTICLE_TEXTURE_SIZE // 2
    for dx in range(-half, half):
        dist = abs(dx)
        alpha = max(0, int(180 * (1 - dist / half)))
        if alpha > 0:
            s.set_at((cx + dx, cy), (255, 255, 255, alpha))
            s.set_at((cx, cy + dx), (255, 255, 255, alpha))
    for r in range(2, 0, -1):
        alpha = int(200 * (1 - r / 3))
        pygame.draw.circle(s, (255, 255, 255, alpha), (cx, cy), r)
    return s


def _make_smoke_texture() -> Surface:
    s = Surface((PARTICLE_TEXTURE_SIZE, PARTICLE_TEXTURE_SIZE), pygame.SRCALPHA)
    cx = cy = PARTICLE_TEXTURE_SIZE // 2
    r_max = PARTICLE_TEXTURE_SIZE // 2 - 1
    for r in range(r_max, 0, -1):
        t = r / r_max
        alpha = int(100 * (1 - t**1.5))
        if alpha > 0:
            pygame.draw.circle(s, (255, 255, 255, alpha), (cx, cy), r)
    return s


def _make_heart_texture() -> Surface:
    s = Surface((PARTICLE_TEXTURE_SIZE, PARTICLE_TEXTURE_SIZE), pygame.SRCALPHA)
    cx = PARTICLE_TEXTURE_SIZE // 2
    cy = PARTICLE_TEXTURE_SIZE // 2
    points: List[Tuple[float, float]] = []
    for i in range(60):
        t = math.pi * 2 * i / 60
        x = 16 * math.sin(t) ** 3
        y = (
            13 * math.cos(t)
            - 5 * math.cos(2 * t)
            - 2 * math.cos(3 * t)
            - math.cos(4 * t)
        )
        points.append((cx + x * 0.7, cy - y * 0.7))
    pygame.draw.polygon(s, (255, 255, 255, 255), points)
    return s


def _get_base_texture(shape: str) -> Surface:
    if shape not in _TEXTURE_CACHE:
        makers = {
            "circle": _make_circle_texture,
            "square": _make_square_texture,
            "diamond": _make_diamond_texture,
            "star": _make_star_texture,
            "sparkle": _make_sparkle_texture,
            "smoke": _make_smoke_texture,
            "heart": _make_heart_texture,
        }
        maker = makers.get(shape, _make_circle_texture)
        _TEXTURE_CACHE[shape] = maker()
    return _TEXTURE_CACHE[shape]


_SCALED_CACHE: Dict[Tuple[str, int], Surface] = {}


def _interp_color(
    sc: Tuple[int, int, int, int],
    ec: Tuple[int, int, int, int],
    t: float,
    alpha_fade: str,
) -> Tuple[int, int, int, int]:
    r = int(sc[0] + (ec[0] - sc[0]) * t)
    g = int(sc[1] + (ec[1] - sc[1]) * t)
    b = int(sc[2] + (ec[2] - sc[2]) * t)
    a_start = sc[3]
    a_end = ec[3]
    if alpha_fade == "none":
        a = a_start
    elif alpha_fade == "fade_out":
        a = int(a_start + (a_end - a_start) * t)
    elif alpha_fade == "fade_in":
        a = int(a_end + (a_start - a_end) * t)
    else:
        mid = 0.5
        if t < mid:
            a = int(a_start + (255 - a_start) * (t / mid))
        else:
            a = int(255 + (a_end - 255) * ((t - mid) / mid))
    return (
        max(0, min(255, r)),
        max(0, min(255, g)),
        max(0, min(255, b)),
        max(0, min(255, a)),
    )


def _get_scaled_texture(shape: str, size_px: int) -> Surface:
    key = (shape, size_px)
    cached = _SCALED_CACHE.get(key)
    if cached is not None:
        return cached
    base = _get_base_texture(shape)
    w = max(1, size_px)
    scaled = pygame.transform.scale(base, (w, w))
    _SCALED_CACHE[key] = scaled
    return scaled


def clear_texture_caches() -> None:
    _SCALED_CACHE.clear()
    _TEXTURE_CACHE.clear()


class Particle:
    __slots__ = (
        "x",
        "y",
        "vx",
        "vy",
        "life",
        "max_life",
        "size",
        "start_size",
        "end_size",
        "start_color",
        "end_color",
        "rotation",
        "rotation_speed",
        "alpha_fade",
        "shape",
    )

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        lifetime: float,
        size: float,
        start_color: Tuple[int, int, int, int],
        end_color: Tuple[int, int, int, int],
        start_scale: float,
        end_scale: float,
        rotation_speed: float,
        alpha_fade: str,
        shape: str,
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = lifetime
        self.max_life = lifetime
        self.size = size
        self.start_size = size * start_scale
        self.end_size = size * end_scale
        self.start_color = start_color
        self.end_color = end_color
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = rotation_speed
        self.alpha_fade = alpha_fade
        self.shape = shape

    def update(self, dt: float, grav_x: float, grav_y: float) -> bool:
        self.life -= dt
        if self.life <= 0:
            return False
        self.vx += grav_x * dt
        self.vy += grav_y * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.rotation_speed * dt
        return True

    @property
    def progress(self) -> float:
        if self.max_life <= 0:
            return 1.0
        return max(0.0, 1.0 - self.life / self.max_life)

    @property
    def current_size(self) -> float:
        t = self.progress
        return self.start_size + (self.end_size - self.start_size) * t

    @property
    def current_color(self) -> Tuple[int, int, int, int]:
        return _interp_color(
            self.start_color, self.end_color, self.progress, self.alpha_fade
        )


class ParticleEmitter:
    def __init__(self, config: ParticleSystemConfig):
        self.config = config
        self.particles: List[Particle] = []
        self._pool: List[Particle] = []
        self.spawn_timer: float = 0.0

    def set_config(self, config: ParticleSystemConfig) -> None:
        self.config = config
        self.clear()

    def clear(self) -> None:
        self._pool.extend(self.particles)
        self.particles.clear()
        self.spawn_timer = 0.0

    def emit_burst(self, count: int, x: float, y: float, w: float, h: float) -> None:
        for _ in range(count):
            if len(self.particles) >= self.config.max_particles:
                break
            p = self._spawn(x, y, w, h)
            if p is not None:
                self.particles.append(p)

    def update(
        self, dt: float, area_x: float, area_y: float, area_w: float, area_h: float
    ) -> None:
        cfg = self.config
        if dt > MAX_DT:
            dt = MAX_DT
        if cfg.particle_size_min > cfg.particle_size_max:
            return

        max_p = cfg.max_particles
        self.spawn_timer += dt * cfg.spawn_rate
        while self.spawn_timer >= 1.0 and len(self.particles) < max_p:
            self.spawn_timer -= 1.0
            p = self._spawn(area_x, area_y, area_w, area_h)
            if p is not None:
                self.particles.append(p)

        grav_x = cfg.gravity_x
        grav_y = cfg.gravity_y
        alive = 0
        for i in range(len(self.particles)):
            p = self.particles[i]
            if p.update(dt, grav_x, grav_y):
                if alive != i:
                    self.particles[alive], self.particles[i] = (
                        self.particles[i],
                        self.particles[alive],
                    )
                alive += 1

        for i in range(alive, len(self.particles)):
            self._pool.append(self.particles[i])
        del self.particles[alive:]

    def _spawn(
        self, area_x: float, area_y: float, area_w: float, area_h: float
    ) -> Optional[Particle]:
        cfg = self.config
        emission = cfg.emission_shape

        if emission == "point":
            x = area_x + area_w / 2
            y = area_y + area_h / 2
        elif emission == "rect":
            x = area_x + random.uniform(0, area_w)
            y = area_y + random.uniform(0, area_h)
        elif emission == "circle":
            cx, cy = area_x + area_w / 2, area_y + area_h / 2
            radius = min(area_w, area_h) / 2
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(0, radius)
            x = cx + math.cos(angle) * dist
            y = cy + math.sin(angle) * dist
        else:
            x = area_x + random.uniform(0, area_w)
            y = area_y

        dir_val = cfg.direction
        half_spread = cfg.spread / 2
        if dir_val < 0:
            angle = random.uniform(0, math.pi * 2)
        else:
            angle = math.radians(dir_val + random.uniform(-half_spread, half_spread))

        speed = random.uniform(cfg.speed_min, cfg.speed_max)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed

        lifetime = random.uniform(cfg.lifetime_min, cfg.lifetime_max)
        size = random.uniform(cfg.particle_size_min, cfg.particle_size_max)

        sc = (
            cfg.start_color_r,
            cfg.start_color_g,
            cfg.start_color_b,
            cfg.start_color_a,
        )
        ec = (cfg.end_color_r, cfg.end_color_g, cfg.end_color_b, cfg.end_color_a)

        p = self._pool.pop() if self._pool else None
        if p is not None:
            p.x = x
            p.y = y
            p.vx = vx
            p.vy = vy
            p.life = lifetime
            p.max_life = lifetime
            p.size = size
            p.start_size = size * cfg.start_scale
            p.end_size = size * cfg.end_scale
            p.start_color = sc
            p.end_color = ec
            p.rotation = random.uniform(0, 360)
            p.rotation_speed = cfg.rotation_speed
            p.alpha_fade = cfg.alpha_fade
            p.shape = cfg.particle_shape
        else:
            p = Particle(
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                lifetime=lifetime,
                size=size,
                start_color=sc,
                end_color=ec,
                start_scale=cfg.start_scale,
                end_scale=cfg.end_scale,
                rotation_speed=cfg.rotation_speed,
                alpha_fade=cfg.alpha_fade,
                shape=cfg.particle_shape,
            )
        return p


class ParticleRenderer(ABC):
    @abstractmethod
    def prepare(
        self, particles: List[Particle], config: ParticleSystemConfig
    ) -> None: ...

    @abstractmethod
    def draw(
        self, screen: Surface, offset_x: float, offset_y: float, zoom: float
    ) -> None: ...

    @abstractmethod
    def on_config_change(self, config: ParticleSystemConfig) -> None: ...

    def clear(self) -> None: ...


class SpriteBatchRenderer(ParticleRenderer):
    def __init__(self) -> None:
        self._shape: str = ""
        self._tint_surf: Optional[Surface] = None
        self._tint_size: int = 0
        self._particles: List[Particle] = []

    def on_config_change(self, config: ParticleSystemConfig) -> None:
        self._shape = config.particle_shape
        self._tint_surf = None

    def clear(self) -> None:
        self._tint_surf = None

    def prepare(self, particles: List[Particle], config: ParticleSystemConfig) -> None:
        self._particles = particles
        shape = config.particle_shape
        if shape != self._shape:
            self._shape = shape
            self._tint_surf = None

    def draw(
        self,
        screen: Surface,
        offset_x: float,
        offset_y: float,
        zoom: float,
    ) -> None:
        shape = self._shape
        if not shape:
            return
        particles = self._particles
        if not particles:
            return

        screen_rect = screen.get_rect()

        for p in particles:

            sx = int((p.x - offset_x) * zoom)
            sy = int((p.y - offset_y) * zoom)
            size_px = max(1, int(p.current_size * zoom))
            half = size_px // 2 + 1
            if (
                sx + half < 0
                or sx - half > screen_rect.right
                or sy + half < 0
                or sy - half > screen_rect.bottom
            ):
                continue

            color = p.current_color
            if color[3] <= 0:
                continue

            tex = _get_scaled_texture(shape, size_px)
            tw = tex.get_width()

            draw_surf = tex.copy()
            tint = Surface((tw, tw), pygame.SRCALPHA)
            tint.fill(color)
            draw_surf.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            if p.rotation_speed != 0:
                draw_surf = pygame.transform.rotate(draw_surf, p.rotation)

            dr = draw_surf.get_rect(center=(sx, sy))
            screen.blit(draw_surf, dr)


class ParticleSystem:
    def __init__(
        self, config: ParticleSystemConfig, renderer: Optional[ParticleRenderer] = None
    ):
        self.config = config
        self.emitter = ParticleEmitter(config)
        self.renderer = renderer if renderer is not None else SpriteBatchRenderer()
        self.renderer.on_config_change(config)

    def set_config(self, config: ParticleSystemConfig) -> None:
        self.config = config
        self.emitter.set_config(config)
        self.renderer.on_config_change(config)

    def update(
        self, dt: float, area_x: float, area_y: float, area_w: float, area_h: float
    ) -> None:
        self.emitter.update(dt, area_x, area_y, area_w, area_h)

    def draw(
        self, screen: Surface, offset_x: float, offset_y: float, zoom: float
    ) -> None:
        self.renderer.prepare(self.emitter.particles, self.config)
        self.renderer.draw(screen, offset_x, offset_y, zoom)

    def emit_burst(self, count: int, x: float, y: float, w: float, h: float) -> None:
        self.emitter.emit_burst(count, x, y, w, h)

    def clear(self) -> None:
        self.emitter.clear()
        self.renderer.clear()

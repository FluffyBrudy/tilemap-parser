from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Dict, List, Literal, Optional, Tuple, Union

import pygame
from pygame import Rect, Surface

_COLOR_QUANT = 16
_MAX_TINTED_CACHE = 500
_MAX_SCALED_CACHE = 2000

from ..parser.node_parse import ParsedNode
from ..parser.particle import FieldQuality, ParticleShape, ParticleSystemConfig

PARTICLE_TEXTURE_SIZE = 24
MAX_DT = 0.05

_SYMMETRIC_SHAPES = frozenset({"circle", "square", "diamond", "star", "sparkle", "smoke", "fog"})

#: Field drift direction: compass degrees (0 = right, 90 = down, 180 = left,
#: 270 = up) or the string "random" for omnidirectional drift. The low-level
#: ``ParticleSystemConfig.direction < 0`` sentinel is hidden behind "random".
Direction = Union[float, Literal["random"]]

_ALPHA_FADE_MAP = {
    "none": 0,
    "fade_out": 1,
    "fade_in": 2,
    "fade_both": 3,
}


class ParticleEmitterNode:
    def __init__(self, parsed: ParsedNode) -> None:
        self.node_id = parsed.node_id
        self.name = parsed.name
        self.node_type = parsed.node_type
        self._rect = Rect(parsed.area.x, parsed.area.y, parsed.area.w, parsed.area.h)
        self.layer_name = parsed.layer_name
        self.group = parsed.group
        self.config = ParticleSystemConfig.from_dict(parsed.properties, name=parsed.name)

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


def _make_fog_texture() -> Surface:
    """Flat soft-edged square with a uniform core.

    Unlike the ``smoke`` disc (bright center, dark rim), this shape has
    roughly constant alpha across most of its canvas and only fades at the
    rim.  Densely overlapping fog particles therefore tile like stacked
    translucent sheets, producing one continuous haze instead of a field
    of individual circles.
    """
    s = Surface((PARTICLE_TEXTURE_SIZE, PARTICLE_TEXTURE_SIZE), pygame.SRCALPHA)
    half = PARTICLE_TEXTURE_SIZE / 2
    core = 0.55  # flat up to this normalized distance, then soft edge
    rim = 0.45  # edge width (normalized) over which alpha falls to 0
    for y in range(PARTICLE_TEXTURE_SIZE):
        dy = abs(y + 0.5 - half) / half
        for x in range(PARTICLE_TEXTURE_SIZE):
            dx = abs(x + 0.5 - half) / half
            d = max(dx, dy)
            if d <= core:
                a = 110
            else:
                t = min(1.0, (d - core) / rim)
                a = int(110 * (1.0 - t * t * (3.0 - 2.0 * t)))
            if a > 0:
                s.set_at((x, y), (255, 255, 255, a))
    return s


def _make_heart_texture() -> Surface:
    s = Surface((PARTICLE_TEXTURE_SIZE, PARTICLE_TEXTURE_SIZE), pygame.SRCALPHA)
    cx = PARTICLE_TEXTURE_SIZE // 2
    cy = PARTICLE_TEXTURE_SIZE // 2
    points: List[Tuple[float, float]] = []
    for i in range(60):
        t = math.pi * 2 * i / 60
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
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
            "fog": _make_fog_texture,
            "heart": _make_heart_texture,
        }
        maker = makers.get(shape, _make_circle_texture)
        _TEXTURE_CACHE[shape] = maker()
    return _TEXTURE_CACHE[shape]


_SCALED_CACHE: Dict[Tuple[str, int], Surface] = {}
_TINTED_CACHE: Dict[Tuple[str, int, Tuple[int, int, int, int], bool], Surface] = {}


def _interp_color(
    sc: Tuple[int, int, int, int],
    ec: Tuple[int, int, int, int],
    t: float,
    alpha_fade: int,
    peak_alpha: Optional[int] = None,
) -> Tuple[int, int, int, int]:
    r = int(sc[0] + (ec[0] - sc[0]) * t)
    g = int(sc[1] + (ec[1] - sc[1]) * t)
    b = int(sc[2] + (ec[2] - sc[2]) * t)
    a_start = sc[3]
    a_end = ec[3]
    if alpha_fade == 0:
        a = a_start
    elif alpha_fade == 1:
        a = int(a_start + (a_end - a_start) * t)
    elif alpha_fade == 2:
        a = int(a_end + (a_start - a_end) * t)
    else:
        mid = 0.5
        peak = peak_alpha if peak_alpha is not None else max(a_start, a_end)
        if t < mid:
            a = int(a_start + (peak - a_start) * (t / mid))
        else:
            a = int(peak + (a_end - peak) * ((t - mid) / mid))
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
    if len(_SCALED_CACHE) >= _MAX_SCALED_CACHE:
        _SCALED_CACHE.pop(next(iter(_SCALED_CACHE)))
    base = _get_base_texture(shape)
    w = max(1, size_px)
    scaled = pygame.transform.scale(base, (w, w))
    _SCALED_CACHE[key] = scaled
    return scaled


def _quantize_color(c: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
    q = _COLOR_QUANT
    half = q // 2
    return (
        (c[0] + half) // q * q,
        (c[1] + half) // q * q,
        (c[2] + half) // q * q,
        (c[3] + half) // q * q,
    )


def clear_texture_caches() -> None:
    _SCALED_CACHE.clear()
    _TINTED_CACHE.clear()
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
        "peak_alpha",
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
        alpha_fade: int,
        shape: str,
        peak_alpha: Optional[int] = None,
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
        self.peak_alpha = peak_alpha
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
        # Clamp to [0, 1]: in wrap mode life keeps ticking past zero (no
        # death), so without the clamp size/color would extrapolate forever.
        return min(1.0, max(0.0, 1.0 - self.life / self.max_life))

    @property
    def current_size(self) -> float:
        t = self.progress
        return self.start_size + (self.end_size - self.start_size) * t

    @property
    def current_color(self) -> Tuple[int, int, int, int]:
        return _interp_color(
            self.start_color,
            self.end_color,
            self.progress,
            self.alpha_fade,
            self.peak_alpha,
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

    def update(self, dt: float, area_x: float, area_y: float, area_w: float, area_h: float) -> None:
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

        if cfg.wrap:
            # Continuous media: particles never expire, they just move and
            # wrap around the emission area (toroidal, exact offset preserved).
            for p in self.particles:
                p.update(dt, grav_x, grav_y)
                self._wrap_particle(p, area_x, area_y, area_w, area_h)
            return

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
        if len(self._pool) > cfg.max_particles:
            del self._pool[: len(self._pool) - cfg.max_particles]

    @staticmethod
    def _wrap_particle(p: Particle, area_x: float, area_y: float, area_w: float, area_h: float) -> None:
        """Toroidally fold ``p`` back into the emission area.

        The particle disappears beyond the area edge by half its current
        size, then re-enters on the opposite side at the exact same offset
        (modulo), preserving velocity, alpha, and size.  Deterministic and
        stateless — the same in-range particle is left untouched.
        """
        half = p.current_size / 2
        span_x = area_w + 2 * half
        span_y = area_h + 2 * half
        if span_x <= 0 or span_y <= 0:
            return
        min_x = area_x - half
        max_x = area_x + area_w + half
        min_y = area_y - half
        max_y = area_y + area_h + half
        p.x = min_x + (p.x - min_x) % (max_x - min_x)
        p.y = min_y + (p.y - min_y) % (max_y - min_y)

    def _spawn(self, area_x: float, area_y: float, area_w: float, area_h: float) -> Optional[Particle]:
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
        alpha_int = _ALPHA_FADE_MAP.get(cfg.alpha_fade, 1)
        peak_alpha = cfg.fade_peak_alpha

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
            p.alpha_fade = alpha_int
            p.peak_alpha = peak_alpha
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
                alpha_fade=alpha_int,
                shape=cfg.particle_shape,
                peak_alpha=peak_alpha,
            )
        return p


class ParticleRenderer(ABC):
    @abstractmethod
    def prepare(self, particles: List[Particle], config: ParticleSystemConfig) -> None: ...

    @abstractmethod
    def draw(
        self,
        screen: Surface,
        offset_x: float,
        offset_y: float,
        zoom: float,
        blend: int = 0,
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
        self._batch: List[Tuple[Surface, Rect]] = []

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
        blend: int = 0,
    ) -> None:
        shape = self._shape
        if not shape:
            return
        particles = self._particles
        if not particles:
            return

        premul = blend == pygame.BLEND_PREMULTIPLIED
        screen_rect = screen.get_rect()
        batch = self._batch
        batch.clear()

        needs_rotation = shape not in _SYMMETRIC_SHAPES

        for p in particles:
            sx = int((p.x - offset_x) * zoom)
            sy = int((p.y - offset_y) * zoom)
            size_px = max(1, int(p.current_size * zoom))
            size_px = ((size_px + 4) // 8) * 8
            half = size_px // 2 + 1
            if sx + half < 0 or sx - half > screen_rect.right or sy + half < 0 or sy - half > screen_rect.bottom:
                continue

            color = p.current_color
            if color[3] <= 0:
                continue

            cache_key = (shape, size_px, _quantize_color(color), premul)
            draw_surf = _TINTED_CACHE.pop(cache_key, None)
            if draw_surf is None:
                if len(_TINTED_CACHE) >= _MAX_TINTED_CACHE:
                    _TINTED_CACHE.pop(next(iter(_TINTED_CACHE)))
                tex = _get_scaled_texture(shape, size_px)
                draw_surf = tex.copy()
                draw_surf.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
                if premul:
                    draw_surf = draw_surf.premul_alpha()
            _TINTED_CACHE[cache_key] = draw_surf  # move to MRU position

            if p.rotation_speed != 0 and needs_rotation:
                rotated = pygame.transform.rotate(draw_surf, p.rotation)
                dr = rotated.get_rect(center=(sx, sy))
                screen.blit(rotated, dr, special_flags=blend)
            else:
                dr = draw_surf.get_rect(center=(sx, sy))
                batch.append((draw_surf, dr))

        if batch:
            if blend:
                screen.fblits(batch, blend)
            else:
                screen.blits(batch)


class ParticleSystem:
    def __init__(self, config: ParticleSystemConfig, renderer: Optional[ParticleRenderer] = None):
        self.config = config
        self.emitter = ParticleEmitter(config)
        self.renderer = renderer if renderer is not None else SpriteBatchRenderer()
        self.renderer.on_config_change(config)

    def set_config(self, config: ParticleSystemConfig) -> None:
        self.config = config
        self.emitter.set_config(config)
        self.renderer.on_config_change(config)

    def update(self, dt: float, area_x: float, area_y: float, area_w: float, area_h: float) -> None:
        self.emitter.update(dt, area_x, area_y, area_w, area_h)

    def draw(
        self,
        screen: Surface,
        offset_x: float,
        offset_y: float,
        zoom: float,
        blend: int = 0,
    ) -> None:
        self.renderer.prepare(self.emitter.particles, self.config)
        self.renderer.draw(screen, offset_x, offset_y, zoom, blend)

    def emit_burst(self, count: int, x: float, y: float, w: float, h: float) -> None:
        self.emitter.emit_burst(count, x, y, w, h)

    def emit_field(self, coverage: float, x: float, y: float, w: float, h: float) -> None:
        """Fill the ``w x h`` area once with a persistent field.

        Sets the particle count from ``config.count_for_coverage``
        (capped at ``max_particles``), so density is expressed as a
        dimensionless coverage (0.5 = half the area) instead of a raw
        count.  Requires the field contract: ``wrap=True`` and
        ``spawn_rate=0`` — otherwise the field would die or spawn on top
        of itself, and the error names exactly which fields to change.
        """
        cfg = self.config
        if not cfg.wrap:
            raise ValueError(
                "emit_field() needs a persistent field: set config.wrap=True (particles wrap instead of dying)"
            )
        if cfg.spawn_rate != 0:
            raise ValueError(
                "emit_field() fills once: set config.spawn_rate=0 so update() " + "does not spawn on top of the field"
            )
        count = cfg.count_for_coverage(coverage, w, h)
        self.emitter.emit_burst(count, x, y, w, h)

    def clear(self) -> None:
        self.emitter.clear()
        self.renderer.clear()


@dataclass(frozen=True)
class FieldLayerSpec:
    """One layer's tuning inside a :class:`FieldProfile`.

    ``coverage`` is the fill density (see ``count_for_coverage``);
    ``ground_layer`` marks layers that sit in the lower band of the area
    when the field is built with ``ground_bias=True``.
    """

    name: str
    size_min: int
    size_max: int
    speed_min_mul: float
    speed_max_mul: float
    alpha: int
    coverage: float
    ground_layer: bool = False


@dataclass(frozen=True)
class FieldProfile:
    """Named, inspectable set of layer specs for :class:`ParticleField`.

    A profile is plain data: copy ``FOG_PROFILE`` and tweak the numbers to
    build your own mood (dust, sandstorm, underwater shimmer...).  The
    field machinery is generic; the tuning lives here.
    """

    name: str
    presets: Tuple[FieldLayerSpec, ...]

    def with_alpha(self, factor: float, name: Optional[str] = None) -> "FieldProfile":
        """Return a copy with every layer alpha scaled by ``factor``.

        Profiles are immutable data, so this never mutates the source profile.
        ``name`` overrides the profile name on the returned copy (handy for
        authoring named variants like ``fog.with_alpha(0.5, name="mist")``).
        Use ``ParticleField.global_alpha`` for live fading; use this when you
        want a named profile variant.
        """
        scale = max(0.0, float(factor))
        return FieldProfile(
            name if name is not None else self.name,
            tuple(
                FieldLayerSpec(
                    spec.name,
                    spec.size_min,
                    spec.size_max,
                    spec.speed_min_mul,
                    spec.speed_max_mul,
                    max(0, min(255, round(spec.alpha * scale))),
                    spec.coverage,
                    spec.ground_layer,
                )
                for spec in self.presets
            ),
        )


@dataclass
class ParticleFieldLayer:
    """One generated layer inside a :class:`ParticleField`.

    Most games should not need to build these manually.  The public shape is
    useful for inspection, testing, or drawing layers yourself.
    """

    name: str
    system: ParticleSystem
    area: Tuple[float, float, float, float]


class ParticleField:
    """High-level persistent particle field helper.

    ``ParticleField`` turns common continuous-effect dials (density,
    strength, motion, color) into wrapped particle fields.  It owns the
    field contract (``wrap=True`` and ``spawn_rate=0``), fills once, then
    only moves existing particles.  Layer tuning comes from a
    :class:`FieldProfile` (plain data) or from generic size/speed/alpha
    dials when no profile is given.
    """

    shape: ParticleShape
    quality: FieldQuality
    direction: Direction

    _QUALITY: ClassVar[Dict[str, Tuple[float, int]]] = {
        "low": (0.72, 260),
        "medium": (1.0, 500),
        "high": (1.25, 800),
    }

    def __init__(
        self,
        area: Tuple[float, float, float, float],
        *,
        shape: ParticleShape = "fog",
        color: Tuple[int, int, int] = (200, 205, 215),
        alpha: int = 14,
        global_alpha: float = 1.0,
        density: float = 1.0,
        direction: Direction = 0.0,
        speed: Tuple[float, float] = (6.0, 14.0),
        size: Tuple[int, int] = (70, 120),
        spread: float = 30.0,
        layers: int = 1,
        quality: FieldQuality = "medium",
        ground_bias: bool = True,
        render_scale: float = 1.0,
        profile: Optional[FieldProfile] = None,
        blend: int = 0,
    ) -> None:
        if quality not in self._QUALITY:
            raise ValueError("quality must be 'low', 'medium', or 'high'")
        self.area = area
        self.shape = shape
        self.color = color
        self.alpha = self._clamp_channel(alpha)
        self._global_alpha = self._clamp_alpha(global_alpha)
        self.density = max(0.01, float(density))
        self.direction = self._normalize_direction(direction)
        self.speed = (max(0.0, float(speed[0])), max(0.0, float(speed[1])))
        if self.speed[1] < self.speed[0]:
            self.speed = (self.speed[1], self.speed[0])
        self.size = (max(1, int(size[0])), max(1, int(size[1])))
        if self.size[1] < self.size[0]:
            self.size = (self.size[1], self.size[0])
        self.spread = max(0.0, min(360.0, float(spread)))
        self.layer_count = max(1, int(layers))
        self.quality = quality
        self.ground_bias = ground_bias
        self.render_scale = max(0.01, float(render_scale))
        self.profile = profile
        self.blend = int(blend)
        self.layers: List[ParticleFieldLayer] = []
        self._layer_base_alpha: List[int] = []
        self.refill()

    @staticmethod
    def _clamp_channel(value: float) -> int:
        return max(0, min(255, int(value)))

    @staticmethod
    def _clamp_alpha(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    @staticmethod
    def _normalize_direction(value: Direction) -> Direction:
        if value == "random":
            return "random"
        if isinstance(value, str):
            raise ValueError("direction must be degrees (float) or 'random'")
        return float(value)

    @property
    def global_alpha(self) -> float:
        """Master strength scale (0.0-1.0) applied to every layer's alpha."""
        return self._global_alpha

    @global_alpha.setter
    def global_alpha(self, value: float) -> None:
        """Live strength scale; restyles existing layer configs in place."""
        self._global_alpha = self._clamp_alpha(value)
        for layer, base in zip(self.layers, self._layer_base_alpha, strict=True):
            alpha = self._clamp_channel(base * self._global_alpha)
            cfg = layer.system.config
            cfg.start_color_a = alpha
            cfg.end_color_a = alpha

    @staticmethod
    def _ground_area(area: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        x, y, w, h = area
        top = y + h * 0.35
        return (x, top, w, h * 0.65)

    def _generic_presets(self) -> Tuple[FieldLayerSpec, ...]:
        size_min, size_max = self.size
        alpha = self.alpha
        if self.layer_count == 1:
            return (FieldLayerSpec("field", size_min, size_max, 1.0, 1.0, alpha, 1.0),)

        presets: List[FieldLayerSpec] = []
        for i in range(self.layer_count):
            t = i / max(1, self.layer_count - 1)
            speed_min_mul = 0.75 + t * 0.5
            speed_max_mul = 0.85 + t * 0.5
            size_mul = 1.2 - t * 0.35
            layer_alpha = max(1, round(alpha * (0.8 + t * 0.25)))
            presets.append(
                FieldLayerSpec(
                    f"layer-{i + 1}",
                    max(1, round(size_min * size_mul)),
                    max(1, round(size_max * size_mul)),
                    speed_min_mul,
                    speed_max_mul,
                    layer_alpha,
                    1.0 / self.layer_count,
                )
            )
        return tuple(presets)

    def _make_config(self, preset: FieldLayerSpec, max_particles: int) -> ParticleSystemConfig:
        r, g, b = (self._clamp_channel(c) for c in self.color)
        end_r = self._clamp_channel(r - 10)
        end_g = self._clamp_channel(g - 10)
        end_b = self._clamp_channel(b - 10)
        alpha = self._clamp_channel(preset.alpha * self.global_alpha)
        speed_min, speed_max = self.speed

        cfg = ParticleSystemConfig(
            name=preset.name,
            particle_shape=self.shape,
            emission_shape="rect",
            wrap=True,
            spawn_rate=0,
            particle_size_min=preset.size_min,
            particle_size_max=preset.size_max,
            speed_min=speed_min * preset.speed_min_mul,
            speed_max=speed_max * preset.speed_max_mul,
            direction=self.direction if self.direction != "random" else -1.0,
            spread=self.spread,
            gravity_x=0.0,
            gravity_y=0.0,
            lifetime_min=60.0,
            lifetime_max=120.0,
            start_color_r=r,
            start_color_g=g,
            start_color_b=b,
            start_color_a=alpha,
            end_color_r=end_r,
            end_color_g=end_g,
            end_color_b=end_b,
            end_color_a=alpha,
            alpha_fade="none",
            start_scale=0.9,
            end_scale=1.2,
            rotation_speed=0.0,
            max_particles=max_particles,
        )
        if self.render_scale != 1.0:
            cfg.apply_render_scale(self.render_scale)
        return cfg

    def refill(self) -> None:
        """Rebuild and fill layers after changing density, area, or quality."""
        quality_density, max_particles = self._QUALITY[self.quality]
        presets = self.profile.presets if self.profile is not None else self._generic_presets()
        self._layer_base_alpha = [preset.alpha for preset in presets]
        layers: List[ParticleFieldLayer] = []
        for preset in presets:
            area = self._ground_area(self.area) if preset.ground_layer and self.ground_bias else self.area
            cfg = self._make_config(preset, max_particles)
            system = ParticleSystem(cfg)
            coverage = preset.coverage * self.density * quality_density
            system.emit_field(coverage, *area)
            layers.append(ParticleFieldLayer(preset.name, system, area))
        self.layers = layers

    def set_area(self, area: Tuple[float, float, float, float]) -> None:
        self.area = area
        self.refill()

    def set_density(self, density: float) -> None:
        self.density = max(0.01, float(density))
        self.refill()

    def set_motion(
        self,
        *,
        direction: Optional[Direction] = None,
        speed: Optional[Tuple[float, float]] = None,
        spread: Optional[float] = None,
    ) -> None:
        if direction is not None:
            self.direction = self._normalize_direction(direction)
        if speed is not None:
            self.speed = (max(0.0, float(speed[0])), max(0.0, float(speed[1])))
            if self.speed[1] < self.speed[0]:
                self.speed = (self.speed[1], self.speed[0])
        if spread is not None:
            self.spread = max(0.0, min(360.0, float(spread)))
        self.refill()

    def set_color(self, color: Tuple[int, int, int]) -> None:
        """Recolor all layers in place; never rebuilds, never touches the
        profile or per-layer alphas, and preserves current positions."""
        self.color = color
        r, g, b = (self._clamp_channel(c) for c in color)
        end_r, end_g, end_b = (self._clamp_channel(c - 10) for c in (r, g, b))
        for layer in self.layers:
            cfg = layer.system.config
            cfg.start_color_r = r
            cfg.start_color_g = g
            cfg.start_color_b = b
            cfg.end_color_r = end_r
            cfg.end_color_g = end_g
            cfg.end_color_b = end_b

    def clear(self) -> None:
        for layer in self.layers:
            layer.system.clear()

    def update(self, dt: float) -> None:
        for layer in self.layers:
            layer.system.update(dt, *layer.area)

    def draw(
        self,
        screen: Surface,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        zoom: float = 1.0,
    ) -> None:
        for layer in self.layers:
            layer.system.draw(screen, offset_x, offset_y, zoom, self.blend)


# Known-good starting point: the validated layered fog look.  Copy it and
# tweak the numbers to build your own moods — the machinery is generic.
FOG_PROFILE = FieldProfile(
    "fog",
    (
        FieldLayerSpec("far", 90, 140, 0.38, 0.75, 10, 4.4),
        FieldLayerSpec("mid", 60, 95, 0.62, 1.12, 16, 2.67),
        FieldLayerSpec("near", 40, 65, 1.00, 1.75, 10, 1.85, True),
    ),
)

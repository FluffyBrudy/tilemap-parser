from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .map_parse import (
    JsonDict,
    MapParseError,
    _coerce_float,
    _coerce_int,
    _optional_dict,
    _require_dict,
    _require_list,
    _require_str,
    _ctx,
)


EMISSION_SHAPES = ["point", "rect", "circle", "line"]
PARTICLE_SHAPES = ["circle", "square", "diamond", "star", "sparkle", "smoke", "heart", "line"]
ALPHA_FADE_MODES = ["none", "fade_out", "fade_in", "fade_both"]


@dataclass
class ParticleSystemConfig:
    name: str
    emission_shape: str = "point"
    particle_shape: str = "circle"
    particle_size_min: int = 2
    particle_size_max: int = 6
    spawn_rate: int = 20
    max_particles: int = 100
    lifetime_min: float = 0.5
    lifetime_max: float = 2.0
    speed_min: float = 20.0
    speed_max: float = 60.0
    direction: float = -1.0
    spread: float = 45.0
    gravity_x: float = 0.0
    gravity_y: float = 30.0
    start_color_r: int = 255
    start_color_g: int = 200
    start_color_b: int = 100
    start_color_a: int = 255
    end_color_r: int = 255
    end_color_g: int = 100
    end_color_b: int = 50
    end_color_a: int = 0
    start_scale: float = 1.0
    end_scale: float = 0.3
    rotation_speed: float = 0.0
    alpha_fade: str = "fade_out"

    def to_dict(self) -> JsonDict:
        return {
            "emission_shape": self.emission_shape,
            "particle_shape": self.particle_shape,
            "particle_size_min": self.particle_size_min,
            "particle_size_max": self.particle_size_max,
            "spawn_rate": self.spawn_rate,
            "max_particles": self.max_particles,
            "lifetime_min": self.lifetime_min,
            "lifetime_max": self.lifetime_max,
            "speed_min": self.speed_min,
            "speed_max": self.speed_max,
            "direction": self.direction,
            "spread": self.spread,
            "gravity_x": self.gravity_x,
            "gravity_y": self.gravity_y,
            "start_color_r": self.start_color_r,
            "start_color_g": self.start_color_g,
            "start_color_b": self.start_color_b,
            "start_color_a": self.start_color_a,
            "end_color_r": self.end_color_r,
            "end_color_g": self.end_color_g,
            "end_color_b": self.end_color_b,
            "end_color_a": self.end_color_a,
            "start_scale": self.start_scale,
            "end_scale": self.end_scale,
            "rotation_speed": self.rotation_speed,
            "alpha_fade": self.alpha_fade,
        }

    @classmethod
    def from_dict(cls, d: JsonDict, name: str = "") -> "ParticleSystemConfig":
        def g(key: str, default: Any = 0) -> Any:
            return d.get(key, default)

        cfg = cls(name=name)
        cfg.emission_shape = str(g("emission_shape", "point"))
        if cfg.emission_shape not in EMISSION_SHAPES:
            cfg.emission_shape = "point"
        cfg.particle_shape = str(g("particle_shape", "circle"))
        if cfg.particle_shape not in PARTICLE_SHAPES:
            cfg.particle_shape = "circle"
        cfg.alpha_fade = str(g("alpha_fade", "fade_out"))
        if cfg.alpha_fade not in ALPHA_FADE_MODES:
            cfg.alpha_fade = "fade_out"
        cfg.particle_size_min = max(1, int(g("particle_size_min", 2)))
        cfg.particle_size_max = max(cfg.particle_size_min, int(g("particle_size_max", 6)))
        cfg.spawn_rate = max(1, int(g("spawn_rate", 20)))
        cfg.max_particles = max(1, int(g("max_particles", 100)))
        cfg.lifetime_min = max(0.1, float(g("lifetime_min", 0.5)))
        cfg.lifetime_max = max(cfg.lifetime_min, float(g("lifetime_max", 2.0)))
        cfg.speed_min = max(0.0, float(g("speed_min", 20)))
        cfg.speed_max = max(cfg.speed_min, float(g("speed_max", 60)))
        cfg.direction = float(g("direction", -1))
        cfg.spread = max(0.0, min(360.0, float(g("spread", 45))))
        cfg.gravity_x = float(g("gravity_x", 0))
        cfg.gravity_y = float(g("gravity_y", 30))
        cfg.start_color_r = max(0, min(255, int(g("start_color_r", 255))))
        cfg.start_color_g = max(0, min(255, int(g("start_color_g", 200))))
        cfg.start_color_b = max(0, min(255, int(g("start_color_b", 100))))
        cfg.start_color_a = max(0, min(255, int(g("start_color_a", 255))))
        cfg.end_color_r = max(0, min(255, int(g("end_color_r", 255))))
        cfg.end_color_g = max(0, min(255, int(g("end_color_g", 100))))
        cfg.end_color_b = max(0, min(255, int(g("end_color_b", 50))))
        cfg.end_color_a = max(0, min(255, int(g("end_color_a", 0))))
        cfg.start_scale = max(0.1, float(g("start_scale", 1.0)))
        cfg.end_scale = max(0.1, float(g("end_scale", 0.3)))
        cfg.rotation_speed = float(g("rotation_speed", 0))
        return cfg


def _parse_system(raw: Any, ctx: str) -> ParticleSystemConfig:
    d = _require_dict(raw, ctx)
    name = str(d.get("name", ""))
    cfg_raw = _optional_dict(d.get("config"), f"{ctx}.config")
    if cfg_raw is None:
        cfg_raw = {}
    return ParticleSystemConfig.from_dict(cfg_raw, name=name)


def parse_particle_dict(root: JsonDict) -> List[ParticleSystemConfig]:
    root = _require_dict(root, "root")
    raw_systems = _require_list(root.get("particle_systems", []), "root.particle_systems")
    return [_parse_system(item, f"root.particle_systems[{i}]") for i, item in enumerate(raw_systems)]


def parse_particle_file(path: Union[str, Path]) -> List[ParticleSystemConfig]:
    p = Path(path)
    if not p.is_file():
        raise MapParseError(f"Not a file: {p}")
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        raise MapParseError(f"Cannot read {p}: {e}") from e
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        raise MapParseError(f"Invalid JSON in {p}: {e}") from e
    return parse_particle_dict(payload)

"""
Full preset browser — cycle through all 55+ editor presets with keyboard.

Controls:
  ← / →  or  ↑ / ↓   — previous / next preset
  Space               — burst emission at cursor
  Esc / Q             — quit

Configs sourced from tilemap-editor's particle_presets.py (55 presets,
11 categories) and rendered using tilemap-parser's runtime.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

import pygame

from tilemap_parser.runtime.particles import ParticleSystem

# ── 55 presets copied from tilemap-editor ──────────────────────────────────
PresetEntry = Dict[str, Any]

PRESETS: List[PresetEntry] = []


def _p(name: str, category: str, desc: str, config: dict) -> PresetEntry:
    return {"name": name, "category": category, "description": desc, "config": config}


# Fire & Heat (6)
PRESETS.append(
    _p(
        "Campfire",
        "Fire & Heat",
        "Classic warm fire, orange→red, upward",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 3,
            "particle_size_max": 7,
            "spawn_rate": 30,
            "max_particles": 70,
            "lifetime_min": 0.4,
            "lifetime_max": 1.2,
            "speed_min": 25,
            "speed_max": 65,
            "direction": 270,
            "spread": 28,
            "gravity_x": 0,
            "gravity_y": -12,
            "start_color_r": 255,
            "start_color_g": 200,
            "start_color_b": 50,
            "start_color_a": 255,
            "end_color_r": 180,
            "end_color_g": 40,
            "end_color_b": 10,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.2,
            "rotation_speed": 0,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Bonfire",
        "Fire & Heat",
        "Large roaring fire with more particles and wider spread",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 4,
            "particle_size_max": 10,
            "spawn_rate": 50,
            "max_particles": 120,
            "lifetime_min": 0.5,
            "lifetime_max": 1.8,
            "speed_min": 30,
            "speed_max": 80,
            "direction": 270,
            "spread": 40,
            "gravity_x": 2,
            "gravity_y": -15,
            "start_color_r": 255,
            "start_color_g": 180,
            "start_color_b": 30,
            "start_color_a": 255,
            "end_color_r": 200,
            "end_color_g": 60,
            "end_color_b": 10,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.3,
            "rotation_speed": 5,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Embers",
        "Fire & Heat",
        "Glowing red/orange embers floating upward",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 1,
            "particle_size_max": 3,
            "spawn_rate": 15,
            "max_particles": 40,
            "lifetime_min": 1.0,
            "lifetime_max": 3.0,
            "speed_min": 10,
            "speed_max": 30,
            "direction": 270,
            "spread": 15,
            "gravity_x": -2,
            "gravity_y": -8,
            "start_color_r": 255,
            "start_color_g": 120,
            "start_color_b": 20,
            "start_color_a": 255,
            "end_color_r": 200,
            "end_color_g": 50,
            "end_color_b": 10,
            "end_color_a": 80,
            "start_scale": 1.0,
            "end_scale": 0.5,
            "rotation_speed": 15,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Blue Flame",
        "Fire & Heat",
        "Intense hot blue-white flame",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 2,
            "particle_size_max": 5,
            "spawn_rate": 25,
            "max_particles": 60,
            "lifetime_min": 0.3,
            "lifetime_max": 0.9,
            "speed_min": 35,
            "speed_max": 75,
            "direction": 270,
            "spread": 20,
            "gravity_x": 0,
            "gravity_y": -18,
            "start_color_r": 100,
            "start_color_g": 180,
            "start_color_b": 255,
            "start_color_a": 255,
            "end_color_r": 30,
            "end_color_g": 60,
            "end_color_b": 200,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.15,
            "rotation_speed": 0,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Lava",
        "Fire & Heat",
        "Slow heavy lava globules, bright orange",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 5,
            "particle_size_max": 12,
            "spawn_rate": 8,
            "max_particles": 30,
            "lifetime_min": 1.5,
            "lifetime_max": 3.0,
            "speed_min": 8,
            "speed_max": 20,
            "direction": 270,
            "spread": 10,
            "gravity_x": 0,
            "gravity_y": -3,
            "start_color_r": 255,
            "start_color_g": 80,
            "start_color_b": 10,
            "start_color_a": 255,
            "end_color_r": 180,
            "end_color_g": 30,
            "end_color_b": 5,
            "end_color_a": 150,
            "start_scale": 1.0,
            "end_scale": 0.6,
            "rotation_speed": -10,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Wildfire",
        "Fire & Heat",
        "Fast chaotic fire spreading sideways",
        {
            "emission_shape": "rect",
            "particle_shape": "circle",
            "particle_size_min": 3,
            "particle_size_max": 6,
            "spawn_rate": 40,
            "max_particles": 100,
            "lifetime_min": 0.3,
            "lifetime_max": 1.0,
            "speed_min": 50,
            "speed_max": 120,
            "direction": -1,
            "spread": 360,
            "gravity_x": 15,
            "gravity_y": -10,
            "start_color_r": 255,
            "start_color_g": 160,
            "start_color_b": 20,
            "start_color_a": 255,
            "end_color_r": 150,
            "end_color_g": 30,
            "end_color_b": 5,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.2,
            "rotation_speed": 20,
            "alpha_fade": "fade_out",
        },
    )
)

# Water & Liquid (6)
PRESETS.append(
    _p(
        "Rain",
        "Water & Liquid",
        "Fast falling rain streaks",
        {
            "emission_shape": "rect",
            "particle_shape": "line",
            "particle_size_min": 1,
            "particle_size_max": 2,
            "spawn_rate": 80,
            "max_particles": 250,
            "lifetime_min": 0.3,
            "lifetime_max": 0.8,
            "speed_min": 250,
            "speed_max": 400,
            "direction": 90,
            "spread": 6,
            "gravity_x": 0,
            "gravity_y": 0,
            "start_color_r": 180,
            "start_color_g": 210,
            "start_color_b": 255,
            "start_color_a": 200,
            "end_color_r": 140,
            "end_color_g": 180,
            "end_color_b": 255,
            "end_color_a": 30,
            "start_scale": 1.0,
            "end_scale": 1.0,
            "rotation_speed": 0,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Fountain",
        "Water & Liquid",
        "Water fountain arc with gravity pull",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 2,
            "particle_size_max": 5,
            "spawn_rate": 40,
            "max_particles": 90,
            "lifetime_min": 1.0,
            "lifetime_max": 2.5,
            "speed_min": 80,
            "speed_max": 150,
            "direction": 270,
            "spread": 30,
            "gravity_x": 0,
            "gravity_y": 90,
            "start_color_r": 140,
            "start_color_g": 200,
            "start_color_b": 255,
            "start_color_a": 255,
            "end_color_r": 80,
            "end_color_g": 160,
            "end_color_b": 255,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.4,
            "rotation_speed": 0,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Water Drip",
        "Water & Liquid",
        "Slow drips from a ceiling edge",
        {
            "emission_shape": "line",
            "particle_shape": "circle",
            "particle_size_min": 2,
            "particle_size_max": 4,
            "spawn_rate": 6,
            "max_particles": 15,
            "lifetime_min": 0.5,
            "lifetime_max": 1.5,
            "speed_min": 30,
            "speed_max": 80,
            "direction": 90,
            "spread": 5,
            "gravity_x": 0,
            "gravity_y": 50,
            "start_color_r": 160,
            "start_color_g": 200,
            "start_color_b": 255,
            "start_color_a": 220,
            "end_color_r": 120,
            "end_color_g": 180,
            "end_color_b": 255,
            "end_color_a": 100,
            "start_scale": 1.0,
            "end_scale": 0.8,
            "rotation_speed": 0,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Splash",
        "Water & Liquid",
        "Burst of water droplets outward",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 1,
            "particle_size_max": 4,
            "spawn_rate": 60,
            "max_particles": 40,
            "lifetime_min": 0.2,
            "lifetime_max": 0.8,
            "speed_min": 60,
            "speed_max": 180,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": 60,
            "start_color_r": 180,
            "start_color_g": 220,
            "start_color_b": 255,
            "start_color_a": 255,
            "end_color_r": 100,
            "end_color_g": 180,
            "end_color_b": 255,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.2,
            "rotation_speed": 30,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Bubbles",
        "Water & Liquid",
        "Rising translucent bubbles",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 3,
            "particle_size_max": 8,
            "spawn_rate": 10,
            "max_particles": 30,
            "lifetime_min": 2.0,
            "lifetime_max": 4.0,
            "speed_min": 10,
            "speed_max": 30,
            "direction": 270,
            "spread": 20,
            "gravity_x": 3,
            "gravity_y": -12,
            "start_color_r": 200,
            "start_color_g": 230,
            "start_color_b": 255,
            "start_color_a": 120,
            "end_color_r": 180,
            "end_color_g": 220,
            "end_color_b": 255,
            "end_color_a": 30,
            "start_scale": 1.0,
            "end_scale": 1.2,
            "rotation_speed": 5,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Stream",
        "Water & Liquid",
        "Flowing water current particles",
        {
            "emission_shape": "rect",
            "particle_shape": "circle",
            "particle_size_min": 2,
            "particle_size_max": 4,
            "spawn_rate": 25,
            "max_particles": 60,
            "lifetime_min": 1.0,
            "lifetime_max": 3.0,
            "speed_min": 20,
            "speed_max": 50,
            "direction": 90,
            "spread": 10,
            "gravity_x": 0,
            "gravity_y": 20,
            "start_color_r": 160,
            "start_color_g": 200,
            "start_color_b": 240,
            "start_color_a": 150,
            "end_color_r": 120,
            "end_color_g": 180,
            "end_color_b": 220,
            "end_color_a": 30,
            "start_scale": 1.0,
            "end_scale": 0.6,
            "rotation_speed": 5,
            "alpha_fade": "fade_out",
        },
    )
)

# Ice & Cold (5)
PRESETS.append(
    _p(
        "Snow",
        "Ice & Cold",
        "Gentle falling snowflakes",
        {
            "emission_shape": "rect",
            "particle_shape": "circle",
            "particle_size_min": 2,
            "particle_size_max": 5,
            "spawn_rate": 20,
            "max_particles": 120,
            "lifetime_min": 3.0,
            "lifetime_max": 6.0,
            "speed_min": 10,
            "speed_max": 30,
            "direction": 90,
            "spread": 35,
            "gravity_x": 3,
            "gravity_y": 12,
            "start_color_r": 255,
            "start_color_g": 255,
            "start_color_b": 255,
            "start_color_a": 230,
            "end_color_r": 200,
            "end_color_g": 220,
            "end_color_b": 255,
            "end_color_a": 80,
            "start_scale": 1.0,
            "end_scale": 0.9,
            "rotation_speed": 20,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Blizzard",
        "Ice & Cold",
        "Heavy snow with strong wind",
        {
            "emission_shape": "rect",
            "particle_shape": "circle",
            "particle_size_min": 1,
            "particle_size_max": 4,
            "spawn_rate": 60,
            "max_particles": 200,
            "lifetime_min": 2.0,
            "lifetime_max": 5.0,
            "speed_min": 40,
            "speed_max": 100,
            "direction": 80,
            "spread": 25,
            "gravity_x": 40,
            "gravity_y": 20,
            "start_color_r": 240,
            "start_color_g": 245,
            "start_color_b": 255,
            "start_color_a": 200,
            "end_color_r": 180,
            "end_color_g": 200,
            "end_color_b": 240,
            "end_color_a": 40,
            "start_scale": 0.8,
            "end_scale": 0.4,
            "rotation_speed": 30,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Ice Shards",
        "Ice & Cold",
        "Sharp ice crystals shooting outward",
        {
            "emission_shape": "point",
            "particle_shape": "diamond",
            "particle_size_min": 3,
            "particle_size_max": 7,
            "spawn_rate": 15,
            "max_particles": 40,
            "lifetime_min": 0.5,
            "lifetime_max": 1.5,
            "speed_min": 60,
            "speed_max": 140,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": 15,
            "start_color_r": 200,
            "start_color_g": 230,
            "start_color_b": 255,
            "start_color_a": 255,
            "end_color_r": 140,
            "end_color_g": 200,
            "end_color_b": 255,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.3,
            "rotation_speed": 100,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Frost Breath",
        "Ice & Cold",
        "Cold mist breath, white icy vapor",
        {
            "emission_shape": "point",
            "particle_shape": "smoke",
            "particle_size_min": 5,
            "particle_size_max": 10,
            "spawn_rate": 15,
            "max_particles": 40,
            "lifetime_min": 1.0,
            "lifetime_max": 2.5,
            "speed_min": 15,
            "speed_max": 40,
            "direction": 0,
            "spread": 20,
            "gravity_x": 0,
            "gravity_y": -5,
            "start_color_r": 220,
            "start_color_g": 235,
            "start_color_b": 255,
            "start_color_a": 120,
            "end_color_r": 180,
            "end_color_g": 210,
            "end_color_b": 255,
            "end_color_a": 0,
            "start_scale": 0.5,
            "end_scale": 1.5,
            "rotation_speed": 3,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Hail",
        "Ice & Cold",
        "Hard falling ice pellets",
        {
            "emission_shape": "rect",
            "particle_shape": "square",
            "particle_size_min": 3,
            "particle_size_max": 6,
            "spawn_rate": 25,
            "max_particles": 80,
            "lifetime_min": 0.5,
            "lifetime_max": 1.2,
            "speed_min": 100,
            "speed_max": 200,
            "direction": 90,
            "spread": 10,
            "gravity_x": 0,
            "gravity_y": 60,
            "start_color_r": 230,
            "start_color_g": 240,
            "start_color_b": 255,
            "start_color_a": 255,
            "end_color_r": 200,
            "end_color_g": 220,
            "end_color_b": 250,
            "end_color_a": 120,
            "start_scale": 1.0,
            "end_scale": 0.8,
            "rotation_speed": 50,
            "alpha_fade": "fade_out",
        },
    )
)

# Smoke & Gas (5)
PRESETS.append(
    _p(
        "Smoke",
        "Smoke & Gas",
        "Thick gray smoke billowing upward",
        {
            "emission_shape": "point",
            "particle_shape": "smoke",
            "particle_size_min": 8,
            "particle_size_max": 14,
            "spawn_rate": 8,
            "max_particles": 40,
            "lifetime_min": 2.0,
            "lifetime_max": 4.0,
            "speed_min": 10,
            "speed_max": 30,
            "direction": 270,
            "spread": 20,
            "gravity_x": -3,
            "gravity_y": -10,
            "start_color_r": 180,
            "start_color_g": 180,
            "start_color_b": 180,
            "start_color_a": 130,
            "end_color_r": 100,
            "end_color_g": 100,
            "end_color_b": 100,
            "end_color_a": 0,
            "start_scale": 0.5,
            "end_scale": 1.8,
            "rotation_speed": 4,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Steam",
        "Smoke & Gas",
        "Hot white vapor, faint and rising",
        {
            "emission_shape": "point",
            "particle_shape": "smoke",
            "particle_size_min": 6,
            "particle_size_max": 12,
            "spawn_rate": 6,
            "max_particles": 30,
            "lifetime_min": 3.0,
            "lifetime_max": 5.0,
            "speed_min": 5,
            "speed_max": 15,
            "direction": 270,
            "spread": 15,
            "gravity_x": -2,
            "gravity_y": -6,
            "start_color_r": 220,
            "start_color_g": 220,
            "start_color_b": 220,
            "start_color_a": 100,
            "end_color_r": 200,
            "end_color_g": 200,
            "end_color_b": 200,
            "end_color_a": 0,
            "start_scale": 0.3,
            "end_scale": 2.2,
            "rotation_speed": 2,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Mist",
        "Smoke & Gas",
        "Ground-level hazy mist",
        {
            "emission_shape": "rect",
            "particle_shape": "smoke",
            "particle_size_min": 10,
            "particle_size_max": 18,
            "spawn_rate": 4,
            "max_particles": 20,
            "lifetime_min": 4.0,
            "lifetime_max": 8.0,
            "speed_min": 3,
            "speed_max": 10,
            "direction": -1,
            "spread": 360,
            "gravity_x": 2,
            "gravity_y": -2,
            "start_color_r": 200,
            "start_color_g": 200,
            "start_color_b": 210,
            "start_color_a": 80,
            "end_color_r": 180,
            "end_color_g": 180,
            "end_color_b": 190,
            "end_color_a": 0,
            "start_scale": 0.3,
            "end_scale": 2.5,
            "rotation_speed": 1,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Poison Gas",
        "Smoke & Gas",
        "Toxic green cloud",
        {
            "emission_shape": "point",
            "particle_shape": "smoke",
            "particle_size_min": 7,
            "particle_size_max": 13,
            "spawn_rate": 10,
            "max_particles": 45,
            "lifetime_min": 2.0,
            "lifetime_max": 4.5,
            "speed_min": 8,
            "speed_max": 25,
            "direction": -1,
            "spread": 360,
            "gravity_x": -3,
            "gravity_y": -8,
            "start_color_r": 50,
            "start_color_g": 200,
            "start_color_b": 80,
            "start_color_a": 100,
            "end_color_r": 20,
            "end_color_g": 120,
            "end_color_b": 50,
            "end_color_a": 0,
            "start_scale": 0.6,
            "end_scale": 2.0,
            "rotation_speed": 3,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Dust Cloud",
        "Smoke & Gas",
        "Brown dust kicked up",
        {
            "emission_shape": "rect",
            "particle_shape": "circle",
            "particle_size_min": 3,
            "particle_size_max": 8,
            "spawn_rate": 20,
            "max_particles": 60,
            "lifetime_min": 1.0,
            "lifetime_max": 3.0,
            "speed_min": 15,
            "speed_max": 45,
            "direction": -1,
            "spread": 360,
            "gravity_x": 5,
            "gravity_y": 5,
            "start_color_r": 180,
            "start_color_g": 160,
            "start_color_b": 130,
            "start_color_a": 100,
            "end_color_r": 140,
            "end_color_g": 120,
            "end_color_b": 100,
            "end_color_a": 0,
            "start_scale": 0.5,
            "end_scale": 1.5,
            "rotation_speed": 10,
            "alpha_fade": "fade_out",
        },
    )
)

# Nature (6)
PRESETS.append(
    _p(
        "Falling Leaves",
        "Nature",
        "Autumn leaves drifting down",
        {
            "emission_shape": "rect",
            "particle_shape": "square",
            "particle_size_min": 3,
            "particle_size_max": 6,
            "spawn_rate": 6,
            "max_particles": 30,
            "lifetime_min": 3.0,
            "lifetime_max": 6.0,
            "speed_min": 8,
            "speed_max": 25,
            "direction": 90,
            "spread": 40,
            "gravity_x": 10,
            "gravity_y": 10,
            "start_color_r": 220,
            "start_color_g": 180,
            "start_color_b": 60,
            "start_color_a": 255,
            "end_color_r": 160,
            "end_color_g": 100,
            "end_color_b": 30,
            "end_color_a": 100,
            "start_scale": 1.0,
            "end_scale": 0.7,
            "rotation_speed": 40,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Pollen",
        "Nature",
        "Tiny yellow pollen floating in air",
        {
            "emission_shape": "rect",
            "particle_shape": "circle",
            "particle_size_min": 1,
            "particle_size_max": 3,
            "spawn_rate": 10,
            "max_particles": 50,
            "lifetime_min": 4.0,
            "lifetime_max": 8.0,
            "speed_min": 3,
            "speed_max": 12,
            "direction": -1,
            "spread": 360,
            "gravity_x": 2,
            "gravity_y": -2,
            "start_color_r": 255,
            "start_color_g": 240,
            "start_color_b": 120,
            "start_color_a": 180,
            "end_color_r": 240,
            "end_color_g": 220,
            "end_color_b": 80,
            "end_color_a": 40,
            "start_scale": 1.0,
            "end_scale": 0.5,
            "rotation_speed": 5,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Fireflies",
        "Nature",
        "Glowing yellow-green dots at night",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 2,
            "particle_size_max": 4,
            "spawn_rate": 8,
            "max_particles": 25,
            "lifetime_min": 3.0,
            "lifetime_max": 6.0,
            "speed_min": 5,
            "speed_max": 20,
            "direction": -1,
            "spread": 360,
            "gravity_x": -5,
            "gravity_y": -5,
            "start_color_r": 200,
            "start_color_g": 255,
            "start_color_b": 80,
            "start_color_a": 255,
            "end_color_r": 150,
            "end_color_g": 220,
            "end_color_b": 40,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.3,
            "rotation_speed": 10,
            "alpha_fade": "fade_both",
        },
    )
)

PRESETS.append(
    _p(
        "Petals",
        "Nature",
        "Falling flower petals, pink and spinning",
        {
            "emission_shape": "rect",
            "particle_shape": "heart",
            "particle_size_min": 3,
            "particle_size_max": 6,
            "spawn_rate": 8,
            "max_particles": 35,
            "lifetime_min": 2.0,
            "lifetime_max": 5.0,
            "speed_min": 10,
            "speed_max": 30,
            "direction": 90,
            "spread": 45,
            "gravity_x": 8,
            "gravity_y": 15,
            "start_color_r": 255,
            "start_color_g": 140,
            "start_color_b": 180,
            "start_color_a": 255,
            "end_color_r": 255,
            "end_color_g": 100,
            "end_color_b": 150,
            "end_color_a": 60,
            "start_scale": 0.8,
            "end_scale": 0.4,
            "rotation_speed": 60,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Sand Storm",
        "Nature",
        "Horizontal blowing sand",
        {
            "emission_shape": "rect",
            "particle_shape": "circle",
            "particle_size_min": 1,
            "particle_size_max": 3,
            "spawn_rate": 60,
            "max_particles": 180,
            "lifetime_min": 1.0,
            "lifetime_max": 3.0,
            "speed_min": 50,
            "speed_max": 120,
            "direction": 0,
            "spread": 15,
            "gravity_x": 80,
            "gravity_y": 5,
            "start_color_r": 200,
            "start_color_g": 180,
            "start_color_b": 140,
            "start_color_a": 180,
            "end_color_r": 160,
            "end_color_g": 140,
            "end_color_b": 100,
            "end_color_a": 20,
            "start_scale": 1.0,
            "end_scale": 0.5,
            "rotation_speed": 5,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Morning Dew",
        "Nature",
        "Sparkly dew drops, catching light",
        {
            "emission_shape": "point",
            "particle_shape": "diamond",
            "particle_size_min": 1,
            "particle_size_max": 3,
            "spawn_rate": 5,
            "max_particles": 20,
            "lifetime_min": 2.0,
            "lifetime_max": 4.0,
            "speed_min": 2,
            "speed_max": 8,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": 5,
            "start_color_r": 255,
            "start_color_g": 255,
            "start_color_b": 255,
            "start_color_a": 200,
            "end_color_r": 200,
            "end_color_g": 240,
            "end_color_b": 255,
            "end_color_a": 40,
            "start_scale": 1.0,
            "end_scale": 0.3,
            "rotation_speed": 20,
            "alpha_fade": "fade_both",
        },
    )
)

# Magic (8)
PRESETS.append(
    _p(
        "Magic Sparkles",
        "Magic",
        "Purple→cyan sparkling burst",
        {
            "emission_shape": "point",
            "particle_shape": "sparkle",
            "particle_size_min": 2,
            "particle_size_max": 5,
            "spawn_rate": 30,
            "max_particles": 70,
            "lifetime_min": 0.5,
            "lifetime_max": 1.5,
            "speed_min": 40,
            "speed_max": 110,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": -18,
            "start_color_r": 200,
            "start_color_g": 100,
            "start_color_b": 255,
            "start_color_a": 255,
            "end_color_r": 80,
            "end_color_g": 200,
            "end_color_b": 255,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.2,
            "rotation_speed": 200,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Nebula",
        "Magic",
        "Cosmic purple/blue ambient cloud",
        {
            "emission_shape": "point",
            "particle_shape": "diamond",
            "particle_size_min": 5,
            "particle_size_max": 10,
            "spawn_rate": 15,
            "max_particles": 55,
            "lifetime_min": 2.0,
            "lifetime_max": 4.0,
            "speed_min": 15,
            "speed_max": 40,
            "direction": -1,
            "spread": 360,
            "gravity_x": -5,
            "gravity_y": -5,
            "start_color_r": 80,
            "start_color_g": 50,
            "start_color_b": 180,
            "start_color_a": 220,
            "end_color_r": 200,
            "end_color_g": 100,
            "end_color_b": 255,
            "end_color_a": 0,
            "start_scale": 0.5,
            "end_scale": 1.8,
            "rotation_speed": 50,
            "alpha_fade": "fade_both",
        },
    )
)

PRESETS.append(
    _p(
        "Holy Light",
        "Magic",
        "Golden/white rays descending",
        {
            "emission_shape": "point",
            "particle_shape": "star",
            "particle_size_min": 3,
            "particle_size_max": 7,
            "spawn_rate": 20,
            "max_particles": 50,
            "lifetime_min": 1.0,
            "lifetime_max": 2.5,
            "speed_min": 15,
            "speed_max": 40,
            "direction": 90,
            "spread": 25,
            "gravity_x": 0,
            "gravity_y": 5,
            "start_color_r": 255,
            "start_color_g": 240,
            "start_color_b": 180,
            "start_color_a": 220,
            "end_color_r": 255,
            "end_color_g": 220,
            "end_color_b": 100,
            "end_color_a": 0,
            "start_scale": 0.5,
            "end_scale": 1.2,
            "rotation_speed": -30,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Dark Magic",
        "Magic",
        "Purple/black shadowy wisps",
        {
            "emission_shape": "point",
            "particle_shape": "smoke",
            "particle_size_min": 4,
            "particle_size_max": 10,
            "spawn_rate": 18,
            "max_particles": 50,
            "lifetime_min": 1.5,
            "lifetime_max": 3.5,
            "speed_min": 20,
            "speed_max": 60,
            "direction": -1,
            "spread": 360,
            "gravity_x": -5,
            "gravity_y": -15,
            "start_color_r": 120,
            "start_color_g": 30,
            "start_color_b": 150,
            "start_color_a": 200,
            "end_color_r": 40,
            "end_color_g": 0,
            "end_color_b": 60,
            "end_color_a": 0,
            "start_scale": 0.4,
            "end_scale": 1.5,
            "rotation_speed": 15,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Fairy Dust",
        "Magic",
        "Sparkling trail of golden dust",
        {
            "emission_shape": "point",
            "particle_shape": "sparkle",
            "particle_size_min": 1,
            "particle_size_max": 3,
            "spawn_rate": 25,
            "max_particles": 60,
            "lifetime_min": 0.8,
            "lifetime_max": 2.0,
            "speed_min": 20,
            "speed_max": 60,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": -10,
            "start_color_r": 255,
            "start_color_g": 240,
            "start_color_b": 150,
            "start_color_a": 255,
            "end_color_r": 255,
            "end_color_g": 200,
            "end_color_b": 50,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.15,
            "rotation_speed": 150,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Arcane Portal",
        "Magic",
        "Swirling blue energy",
        {
            "emission_shape": "circle",
            "particle_shape": "circle",
            "particle_size_min": 3,
            "particle_size_max": 8,
            "spawn_rate": 30,
            "max_particles": 80,
            "lifetime_min": 0.5,
            "lifetime_max": 1.5,
            "speed_min": 20,
            "speed_max": 60,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": 0,
            "start_color_r": 60,
            "start_color_g": 120,
            "start_color_b": 255,
            "start_color_a": 200,
            "end_color_r": 20,
            "end_color_g": 60,
            "end_color_b": 200,
            "end_color_a": 0,
            "start_scale": 0.5,
            "end_scale": 0.1,
            "rotation_speed": 80,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Healing Aura",
        "Magic",
        "Gentle green sparkles rising",
        {
            "emission_shape": "circle",
            "particle_shape": "sparkle",
            "particle_size_min": 2,
            "particle_size_max": 4,
            "spawn_rate": 20,
            "max_particles": 50,
            "lifetime_min": 1.0,
            "lifetime_max": 2.5,
            "speed_min": 15,
            "speed_max": 45,
            "direction": 270,
            "spread": 45,
            "gravity_x": 0,
            "gravity_y": -12,
            "start_color_r": 100,
            "start_color_g": 255,
            "start_color_b": 120,
            "start_color_a": 220,
            "end_color_r": 50,
            "end_color_g": 200,
            "end_color_b": 80,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.2,
            "rotation_speed": 60,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Energy Orbs",
        "Magic",
        "Floating glowing balls of energy",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 5,
            "particle_size_max": 9,
            "spawn_rate": 8,
            "max_particles": 25,
            "lifetime_min": 2.0,
            "lifetime_max": 5.0,
            "speed_min": 5,
            "speed_max": 15,
            "direction": -1,
            "spread": 360,
            "gravity_x": -3,
            "gravity_y": -8,
            "start_color_r": 100,
            "start_color_g": 200,
            "start_color_b": 255,
            "start_color_a": 200,
            "end_color_r": 60,
            "end_color_g": 150,
            "end_color_b": 255,
            "end_color_a": 30,
            "start_scale": 1.0,
            "end_scale": 0.6,
            "rotation_speed": 5,
            "alpha_fade": "fade_both",
        },
    )
)

# Combat (7)
PRESETS.append(
    _p(
        "Explosion",
        "Combat",
        "Burst of fire and debris, short-lived",
        {
            "emission_shape": "point",
            "particle_shape": "star",
            "particle_size_min": 3,
            "particle_size_max": 7,
            "spawn_rate": 200,
            "max_particles": 80,
            "lifetime_min": 0.2,
            "lifetime_max": 0.7,
            "speed_min": 80,
            "speed_max": 220,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": 0,
            "start_color_r": 255,
            "start_color_g": 220,
            "start_color_b": 80,
            "start_color_a": 255,
            "end_color_r": 120,
            "end_color_g": 50,
            "end_color_b": 20,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.1,
            "rotation_speed": 150,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Muzzle Flash",
        "Combat",
        "Quick bright flash from gunfire",
        {
            "emission_shape": "point",
            "particle_shape": "star",
            "particle_size_min": 2,
            "particle_size_max": 5,
            "spawn_rate": 300,
            "max_particles": 30,
            "lifetime_min": 0.05,
            "lifetime_max": 0.2,
            "speed_min": 50,
            "speed_max": 150,
            "direction": 0,
            "spread": 30,
            "gravity_x": 0,
            "gravity_y": 0,
            "start_color_r": 255,
            "start_color_g": 240,
            "start_color_b": 180,
            "start_color_a": 255,
            "end_color_r": 255,
            "end_color_g": 200,
            "end_color_b": 80,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.05,
            "rotation_speed": 200,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Blood Spatter",
        "Combat",
        "Red droplets splattering outward",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 2,
            "particle_size_max": 5,
            "spawn_rate": 80,
            "max_particles": 40,
            "lifetime_min": 0.5,
            "lifetime_max": 2.0,
            "speed_min": 60,
            "speed_max": 180,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": 60,
            "start_color_r": 180,
            "start_color_g": 10,
            "start_color_b": 10,
            "start_color_a": 255,
            "end_color_r": 120,
            "end_color_g": 5,
            "end_color_b": 5,
            "end_color_a": 50,
            "start_scale": 1.0,
            "end_scale": 0.5,
            "rotation_speed": 20,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Slash Trail",
        "Combat",
        "Sword slash arc trail",
        {
            "emission_shape": "line",
            "particle_shape": "sparkle",
            "particle_size_min": 1,
            "particle_size_max": 3,
            "spawn_rate": 60,
            "max_particles": 30,
            "lifetime_min": 0.1,
            "lifetime_max": 0.4,
            "speed_min": 5,
            "speed_max": 15,
            "direction": -1,
            "spread": 180,
            "gravity_x": 0,
            "gravity_y": 0,
            "start_color_r": 200,
            "start_color_g": 200,
            "start_color_b": 255,
            "start_color_a": 255,
            "end_color_r": 100,
            "end_color_g": 100,
            "end_color_b": 255,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.1,
            "rotation_speed": 50,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Fireball Trail",
        "Combat",
        "Fire trailing behind a projectile",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 2,
            "particle_size_max": 5,
            "spawn_rate": 40,
            "max_particles": 60,
            "lifetime_min": 0.2,
            "lifetime_max": 0.6,
            "speed_min": 5,
            "speed_max": 15,
            "direction": 180,
            "spread": 15,
            "gravity_x": 0,
            "gravity_y": 0,
            "start_color_r": 255,
            "start_color_g": 180,
            "start_color_b": 30,
            "start_color_a": 200,
            "end_color_r": 200,
            "end_color_g": 60,
            "end_color_b": 10,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.2,
            "rotation_speed": 10,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Shield Spark",
        "Combat",
        "Sparks from a blocked hit",
        {
            "emission_shape": "point",
            "particle_shape": "star",
            "particle_size_min": 1,
            "particle_size_max": 3,
            "spawn_rate": 100,
            "max_particles": 30,
            "lifetime_min": 0.1,
            "lifetime_max": 0.5,
            "speed_min": 80,
            "speed_max": 180,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": 0,
            "start_color_r": 255,
            "start_color_g": 255,
            "start_color_b": 200,
            "start_color_a": 255,
            "end_color_r": 255,
            "end_color_g": 200,
            "end_color_b": 80,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.1,
            "rotation_speed": 300,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Smoke Screen",
        "Combat",
        "Thick concealing smoke burst",
        {
            "emission_shape": "point",
            "particle_shape": "smoke",
            "particle_size_min": 10,
            "particle_size_max": 18,
            "spawn_rate": 30,
            "max_particles": 40,
            "lifetime_min": 1.5,
            "lifetime_max": 3.5,
            "speed_min": 20,
            "speed_max": 60,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": -5,
            "start_color_r": 140,
            "start_color_g": 140,
            "start_color_b": 140,
            "start_color_a": 150,
            "end_color_r": 80,
            "end_color_g": 80,
            "end_color_b": 80,
            "end_color_a": 0,
            "start_scale": 0.3,
            "end_scale": 2.5,
            "rotation_speed": 10,
            "alpha_fade": "fade_out",
        },
    )
)

# Celebration (6)
PRESETS.append(
    _p(
        "Confetti",
        "Celebration",
        "Colorful falling squares",
        {
            "emission_shape": "rect",
            "particle_shape": "square",
            "particle_size_min": 3,
            "particle_size_max": 6,
            "spawn_rate": 35,
            "max_particles": 120,
            "lifetime_min": 2.0,
            "lifetime_max": 4.5,
            "speed_min": 20,
            "speed_max": 60,
            "direction": 270,
            "spread": 50,
            "gravity_x": 5,
            "gravity_y": 35,
            "start_color_r": 255,
            "start_color_g": 180,
            "start_color_b": 80,
            "start_color_a": 255,
            "end_color_r": 100,
            "end_color_g": 220,
            "end_color_b": 255,
            "end_color_a": 80,
            "start_scale": 1.0,
            "end_scale": 0.8,
            "rotation_speed": 120,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Hearts",
        "Celebration",
        "Floating pink hearts",
        {
            "emission_shape": "point",
            "particle_shape": "heart",
            "particle_size_min": 4,
            "particle_size_max": 8,
            "spawn_rate": 12,
            "max_particles": 40,
            "lifetime_min": 2.0,
            "lifetime_max": 4.0,
            "speed_min": 20,
            "speed_max": 50,
            "direction": 270,
            "spread": 15,
            "gravity_x": 2,
            "gravity_y": -12,
            "start_color_r": 255,
            "start_color_g": 60,
            "start_color_b": 120,
            "start_color_a": 255,
            "end_color_r": 255,
            "end_color_g": 120,
            "end_color_b": 160,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.5,
            "rotation_speed": 25,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Bubbles (Celebration)",
        "Celebration",
        "Playful rising bubbles, translucent",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 3,
            "particle_size_max": 8,
            "spawn_rate": 10,
            "max_particles": 30,
            "lifetime_min": 2.0,
            "lifetime_max": 4.0,
            "speed_min": 10,
            "speed_max": 30,
            "direction": 270,
            "spread": 20,
            "gravity_x": 3,
            "gravity_y": -12,
            "start_color_r": 200,
            "start_color_g": 230,
            "start_color_b": 255,
            "start_color_a": 120,
            "end_color_r": 180,
            "end_color_g": 220,
            "end_color_b": 255,
            "end_color_a": 30,
            "start_scale": 1.0,
            "end_scale": 1.2,
            "rotation_speed": 5,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Fireworks",
        "Celebration",
        "Brilliant multicolor burst",
        {
            "emission_shape": "point",
            "particle_shape": "star",
            "particle_size_min": 2,
            "particle_size_max": 5,
            "spawn_rate": 150,
            "max_particles": 100,
            "lifetime_min": 0.5,
            "lifetime_max": 1.5,
            "speed_min": 50,
            "speed_max": 150,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": 10,
            "start_color_r": 255,
            "start_color_g": 100,
            "start_color_b": 200,
            "start_color_a": 255,
            "end_color_r": 100,
            "end_color_g": 200,
            "end_color_b": 255,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.15,
            "rotation_speed": 100,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Glitter",
        "Celebration",
        "Shimmering gold/silver sparkle rain",
        {
            "emission_shape": "rect",
            "particle_shape": "sparkle",
            "particle_size_min": 1,
            "particle_size_max": 3,
            "spawn_rate": 20,
            "max_particles": 60,
            "lifetime_min": 1.0,
            "lifetime_max": 3.0,
            "speed_min": 5,
            "speed_max": 20,
            "direction": 90,
            "spread": 60,
            "gravity_x": 3,
            "gravity_y": 10,
            "start_color_r": 255,
            "start_color_g": 255,
            "start_color_b": 200,
            "start_color_a": 200,
            "end_color_r": 255,
            "end_color_g": 200,
            "end_color_b": 100,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.2,
            "rotation_speed": 150,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Party Streamers",
        "Celebration",
        "Long colorful ribbons falling",
        {
            "emission_shape": "rect",
            "particle_shape": "line",
            "particle_size_min": 2,
            "particle_size_max": 4,
            "spawn_rate": 15,
            "max_particles": 40,
            "lifetime_min": 2.0,
            "lifetime_max": 4.0,
            "speed_min": 15,
            "speed_max": 40,
            "direction": 90,
            "spread": 60,
            "gravity_x": 10,
            "gravity_y": 25,
            "start_color_r": 255,
            "start_color_g": 100,
            "start_color_b": 100,
            "start_color_a": 255,
            "end_color_r": 100,
            "end_color_g": 100,
            "end_color_b": 255,
            "end_color_a": 60,
            "start_scale": 1.5,
            "end_scale": 0.8,
            "rotation_speed": 80,
            "alpha_fade": "fade_out",
        },
    )
)

# Atmospheric (6)
PRESETS.append(
    _p(
        "Starry Sky",
        "Atmospheric",
        "Twinkling stars in space",
        {
            "emission_shape": "rect",
            "particle_shape": "star",
            "particle_size_min": 1,
            "particle_size_max": 3,
            "spawn_rate": 3,
            "max_particles": 40,
            "lifetime_min": 3.0,
            "lifetime_max": 6.0,
            "speed_min": 2,
            "speed_max": 8,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": 0,
            "start_color_r": 255,
            "start_color_g": 255,
            "start_color_b": 255,
            "start_color_a": 200,
            "end_color_r": 200,
            "end_color_g": 200,
            "end_color_b": 255,
            "end_color_a": 30,
            "start_scale": 1.0,
            "end_scale": 0.3,
            "rotation_speed": 20,
            "alpha_fade": "fade_both",
        },
    )
)

PRESETS.append(
    _p(
        "Aurora",
        "Atmospheric",
        "Wavy green/blue aurora-like glow",
        {
            "emission_shape": "rect",
            "particle_shape": "smoke",
            "particle_size_min": 8,
            "particle_size_max": 16,
            "spawn_rate": 5,
            "max_particles": 25,
            "lifetime_min": 4.0,
            "lifetime_max": 8.0,
            "speed_min": 10,
            "speed_max": 30,
            "direction": 0,
            "spread": 30,
            "gravity_x": 10,
            "gravity_y": -3,
            "start_color_r": 50,
            "start_color_g": 200,
            "start_color_b": 180,
            "start_color_a": 150,
            "end_color_r": 100,
            "end_color_g": 255,
            "end_color_b": 200,
            "end_color_a": 0,
            "start_scale": 0.5,
            "end_scale": 2.0,
            "rotation_speed": 2,
            "alpha_fade": "fade_both",
        },
    )
)

PRESETS.append(
    _p(
        "Heat Haze",
        "Atmospheric",
        "Shimmering heat distortion effect",
        {
            "emission_shape": "rect",
            "particle_shape": "smoke",
            "particle_size_min": 5,
            "particle_size_max": 10,
            "spawn_rate": 8,
            "max_particles": 20,
            "lifetime_min": 0.5,
            "lifetime_max": 1.5,
            "speed_min": 5,
            "speed_max": 15,
            "direction": 270,
            "spread": 5,
            "gravity_x": 0,
            "gravity_y": -10,
            "start_color_r": 255,
            "start_color_g": 255,
            "start_color_b": 200,
            "start_color_a": 80,
            "end_color_r": 255,
            "end_color_g": 240,
            "end_color_b": 180,
            "end_color_a": 0,
            "start_scale": 0.5,
            "end_scale": 1.0,
            "rotation_speed": 0,
            "alpha_fade": "fade_both",
        },
    )
)

PRESETS.append(
    _p(
        "Fog Bank",
        "Atmospheric",
        "Thick rolling fog",
        {
            "emission_shape": "rect",
            "particle_shape": "smoke",
            "particle_size_min": 12,
            "particle_size_max": 20,
            "spawn_rate": 3,
            "max_particles": 15,
            "lifetime_min": 6.0,
            "lifetime_max": 10.0,
            "speed_min": 3,
            "speed_max": 10,
            "direction": 0,
            "spread": 10,
            "gravity_x": 5,
            "gravity_y": 0,
            "start_color_r": 180,
            "start_color_g": 180,
            "start_color_b": 190,
            "start_color_a": 100,
            "end_color_r": 160,
            "end_color_g": 160,
            "end_color_b": 170,
            "end_color_a": 0,
            "start_scale": 0.2,
            "end_scale": 3.0,
            "rotation_speed": 0,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Lightning Flash",
        "Atmospheric",
        "Brief bright bolt flash",
        {
            "emission_shape": "point",
            "particle_shape": "star",
            "particle_size_min": 5,
            "particle_size_max": 12,
            "spawn_rate": 300,
            "max_particles": 15,
            "lifetime_min": 0.03,
            "lifetime_max": 0.15,
            "speed_min": 100,
            "speed_max": 300,
            "direction": 90,
            "spread": 15,
            "gravity_x": 0,
            "gravity_y": 0,
            "start_color_r": 255,
            "start_color_g": 255,
            "start_color_b": 255,
            "start_color_a": 255,
            "end_color_r": 150,
            "end_color_g": 200,
            "end_color_b": 255,
            "end_color_a": 0,
            "start_scale": 2.0,
            "end_scale": 0.0,
            "rotation_speed": 0,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Aurora Borealis",
        "Atmospheric",
        "Northern lights, green/purple waves",
        {
            "emission_shape": "rect",
            "particle_shape": "smoke",
            "particle_size_min": 6,
            "particle_size_max": 14,
            "spawn_rate": 6,
            "max_particles": 30,
            "lifetime_min": 3.0,
            "lifetime_max": 6.0,
            "speed_min": 15,
            "speed_max": 40,
            "direction": 0,
            "spread": 25,
            "gravity_x": 12,
            "gravity_y": -5,
            "start_color_r": 60,
            "start_color_g": 220,
            "start_color_b": 150,
            "start_color_a": 130,
            "end_color_r": 180,
            "end_color_g": 80,
            "end_color_b": 200,
            "end_color_a": 0,
            "start_scale": 0.4,
            "end_scale": 1.8,
            "rotation_speed": 3,
            "alpha_fade": "fade_both",
        },
    )
)

# Sci-Fi / Tech (6)
PRESETS.append(
    _p(
        "Laser Sparks",
        "Sci-Fi",
        "Bright neon sparks from cutting/impact",
        {
            "emission_shape": "point",
            "particle_shape": "sparkle",
            "particle_size_min": 2,
            "particle_size_max": 5,
            "spawn_rate": 60,
            "max_particles": 40,
            "lifetime_min": 0.15,
            "lifetime_max": 0.6,
            "speed_min": 40,
            "speed_max": 120,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": -5,
            "start_color_r": 255,
            "start_color_g": 50,
            "start_color_b": 50,
            "start_color_a": 255,
            "end_color_r": 255,
            "end_color_g": 150,
            "end_color_b": 50,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.1,
            "rotation_speed": 250,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Plasma",
        "Sci-Fi",
        "Glowing purple/blue plasma energy",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 4,
            "particle_size_max": 10,
            "spawn_rate": 20,
            "max_particles": 50,
            "lifetime_min": 0.5,
            "lifetime_max": 1.5,
            "speed_min": 10,
            "speed_max": 40,
            "direction": -1,
            "spread": 360,
            "gravity_x": -5,
            "gravity_y": -10,
            "start_color_r": 150,
            "start_color_g": 50,
            "start_color_b": 255,
            "start_color_a": 200,
            "end_color_r": 50,
            "end_color_g": 0,
            "end_color_b": 200,
            "end_color_a": 0,
            "start_scale": 0.8,
            "end_scale": 0.1,
            "rotation_speed": 40,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Data Stream",
        "Sci-Fi",
        "Green matrix-style falling code",
        {
            "emission_shape": "rect",
            "particle_shape": "line",
            "particle_size_min": 1,
            "particle_size_max": 2,
            "spawn_rate": 40,
            "max_particles": 100,
            "lifetime_min": 0.5,
            "lifetime_max": 2.0,
            "speed_min": 80,
            "speed_max": 200,
            "direction": 90,
            "spread": 5,
            "gravity_x": 0,
            "gravity_y": 0,
            "start_color_r": 0,
            "start_color_g": 255,
            "start_color_b": 50,
            "start_color_a": 220,
            "end_color_r": 0,
            "end_color_g": 180,
            "end_color_b": 30,
            "end_color_a": 30,
            "start_scale": 1.0,
            "end_scale": 1.0,
            "rotation_speed": 0,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Warp Field",
        "Sci-Fi",
        "Distorted space-time particles",
        {
            "emission_shape": "circle",
            "particle_shape": "diamond",
            "particle_size_min": 2,
            "particle_size_max": 6,
            "spawn_rate": 25,
            "max_particles": 60,
            "lifetime_min": 0.3,
            "lifetime_max": 1.0,
            "speed_min": 30,
            "speed_max": 80,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": 0,
            "start_color_r": 100,
            "start_color_g": 100,
            "start_color_b": 255,
            "start_color_a": 200,
            "end_color_r": 50,
            "end_color_g": 50,
            "end_color_b": 200,
            "end_color_a": 0,
            "start_scale": 0.3,
            "end_scale": 1.5,
            "rotation_speed": 150,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Engine Exhaust",
        "Sci-Fi",
        "Rocket thruster flame",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 3,
            "particle_size_max": 8,
            "spawn_rate": 50,
            "max_particles": 100,
            "lifetime_min": 0.2,
            "lifetime_max": 0.8,
            "speed_min": 60,
            "speed_max": 120,
            "direction": 90,
            "spread": 15,
            "gravity_x": 0,
            "gravity_y": 50,
            "start_color_r": 255,
            "start_color_g": 200,
            "start_color_b": 80,
            "start_color_a": 255,
            "end_color_r": 100,
            "end_color_g": 50,
            "end_color_b": 200,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.3,
            "rotation_speed": 10,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Hologram",
        "Sci-Fi",
        "Glitchy holographic particles",
        {
            "emission_shape": "rect",
            "particle_shape": "square",
            "particle_size_min": 2,
            "particle_size_max": 5,
            "spawn_rate": 20,
            "max_particles": 50,
            "lifetime_min": 0.5,
            "lifetime_max": 2.0,
            "speed_min": 10,
            "speed_max": 30,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": -5,
            "start_color_r": 80,
            "start_color_g": 200,
            "start_color_b": 255,
            "start_color_a": 180,
            "end_color_r": 200,
            "end_color_g": 100,
            "end_color_b": 255,
            "end_color_a": 20,
            "start_scale": 0.6,
            "end_scale": 0.2,
            "rotation_speed": 30,
            "alpha_fade": "fade_both",
        },
    )
)

# Feedback (5)
PRESETS.append(
    _p(
        "Alert Ping",
        "Feedback",
        "Quick expanding ring pulse",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 4,
            "particle_size_max": 6,
            "spawn_rate": 100,
            "max_particles": 20,
            "lifetime_min": 0.15,
            "lifetime_max": 0.4,
            "speed_min": 20,
            "speed_max": 50,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": 0,
            "start_color_r": 255,
            "start_color_g": 200,
            "start_color_b": 50,
            "start_color_a": 255,
            "end_color_r": 255,
            "end_color_g": 100,
            "end_color_b": 20,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 2.0,
            "rotation_speed": 0,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Loading",
        "Feedback",
        "Spinning circle of dots",
        {
            "emission_shape": "circle",
            "particle_shape": "circle",
            "particle_size_min": 3,
            "particle_size_max": 4,
            "spawn_rate": 15,
            "max_particles": 12,
            "lifetime_min": 0.8,
            "lifetime_max": 1.2,
            "speed_min": 30,
            "speed_max": 50,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": 0,
            "start_color_r": 100,
            "start_color_g": 200,
            "start_color_b": 255,
            "start_color_a": 255,
            "end_color_r": 50,
            "end_color_g": 150,
            "end_color_b": 255,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.2,
            "rotation_speed": 200,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Click Pop",
        "Feedback",
        "Tiny burst on button click",
        {
            "emission_shape": "point",
            "particle_shape": "circle",
            "particle_size_min": 1,
            "particle_size_max": 3,
            "spawn_rate": 60,
            "max_particles": 10,
            "lifetime_min": 0.1,
            "lifetime_max": 0.3,
            "speed_min": 10,
            "speed_max": 30,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": 0,
            "start_color_r": 200,
            "start_color_g": 200,
            "start_color_b": 255,
            "start_color_a": 200,
            "end_color_r": 100,
            "end_color_g": 100,
            "end_color_b": 255,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.3,
            "rotation_speed": 30,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Level Up",
        "Feedback",
        "Rising golden stars",
        {
            "emission_shape": "point",
            "particle_shape": "star",
            "particle_size_min": 3,
            "particle_size_max": 6,
            "spawn_rate": 40,
            "max_particles": 50,
            "lifetime_min": 0.8,
            "lifetime_max": 2.0,
            "speed_min": 20,
            "speed_max": 60,
            "direction": 270,
            "spread": 60,
            "gravity_x": 0,
            "gravity_y": -20,
            "start_color_r": 255,
            "start_color_g": 215,
            "start_color_b": 0,
            "start_color_a": 255,
            "end_color_r": 255,
            "end_color_g": 180,
            "end_color_b": 0,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.3,
            "rotation_speed": 100,
            "alpha_fade": "fade_out",
        },
    )
)

PRESETS.append(
    _p(
        "Achievement",
        "Feedback",
        "Celebration unlock burst",
        {
            "emission_shape": "point",
            "particle_shape": "sparkle",
            "particle_size_min": 2,
            "particle_size_max": 6,
            "spawn_rate": 120,
            "max_particles": 80,
            "lifetime_min": 0.3,
            "lifetime_max": 1.5,
            "speed_min": 30,
            "speed_max": 100,
            "direction": -1,
            "spread": 360,
            "gravity_x": 0,
            "gravity_y": -15,
            "start_color_r": 255,
            "start_color_g": 255,
            "start_color_b": 100,
            "start_color_a": 255,
            "end_color_r": 255,
            "end_color_g": 150,
            "end_color_b": 50,
            "end_color_a": 0,
            "start_scale": 1.0,
            "end_scale": 0.1,
            "rotation_speed": 180,
            "alpha_fade": "fade_out",
        },
    )
)


SCREEN_W, SCREEN_H = 1200, 800
FPS = 60
AREA_X, AREA_Y, AREA_W, AREA_H = 300, 150, 600, 500
SIZE_SCALE = 12.0


def build_particle_system(config: dict) -> ParticleSystem:
    from tilemap_parser.parser.particle import ParticleSystemConfig

    scaled = dict(config)
    scaled["particle_size_min"] = int(config.get("particle_size_min", 2) * SIZE_SCALE)
    scaled["particle_size_max"] = int(config.get("particle_size_max", 6) * SIZE_SCALE)
    scaled["speed_min"] = config.get("speed_min", 20) * SIZE_SCALE * 0.6
    scaled["speed_max"] = config.get("speed_max", 60) * SIZE_SCALE * 0.6

    cfg = ParticleSystemConfig.from_dict(scaled, name=config.get("name", ""))
    return ParticleSystem(cfg)


# ── Profiler (sliding-window) ────────────────────────────────────────────────
import collections
import time as _time
from tilemap_parser.runtime import particles as _particles_mod

_WINDOW = 120  # 2-second rolling window at 60fps


class Profiler:
    def __init__(self) -> None:
        self.clear()

    def clear(self) -> None:
        self._updates = collections.deque(maxlen=_WINDOW)
        self._draws = collections.deque(maxlen=_WINDOW)
        self._totals = collections.deque(maxlen=_WINDOW)
        self._counts = collections.deque(maxlen=_WINDOW)
        self._snapshot: dict = {
            "texture_cache": 0,
            "scaled_cache": 0,
            "tinted_cache": 0,
            "frames": 0,
        }

    def begin_frame(self) -> None:
        self._frame_start = _time.perf_counter()

    def end_update(self) -> None:
        self._update_end = _time.perf_counter()

    def end_draw(self, emitter) -> None:
        now = _time.perf_counter()
        self._updates.append((self._update_end - self._frame_start) * 1000)
        self._draws.append((now - self._update_end) * 1000)
        self._totals.append((now - self._frame_start) * 1000)
        self._counts.append(len(emitter.particles))
        s = self._snapshot
        s["texture_cache"] = len(_particles_mod._TEXTURE_CACHE)
        s["scaled_cache"] = len(_particles_mod._SCALED_CACHE)
        s["tinted_cache"] = len(_particles_mod._TINTED_CACHE)
        s["frames"] = len(self._totals)

    def snapshot(self) -> dict:
        s = self._snapshot
        w = max(len(self._totals), 1)
        return {
            "avg_update_ms": sum(self._updates) / w,
            "avg_draw_ms": sum(self._draws) / w,
            "avg_total_ms": sum(self._totals) / w,
            "avg_particles": sum(self._counts) / w,
            "texture_cache": s["texture_cache"],
            "scaled_cache": s["scaled_cache"],
            "tinted_cache": s["tinted_cache"],
            "frames": s["frames"],
        }


def _render_profiler(screen, snap: dict, font):
    lines = [
        f"Avg update: {snap['avg_update_ms']:.3f}ms",
        f"Avg draw:   {snap['avg_draw_ms']:.3f}ms",
        f"Avg total:  {snap['avg_total_ms']:.3f}ms",
        f"Avg particles: {snap['avg_particles']:.0f}",
        f"Texture cache: {snap['texture_cache']}",
        f"Scaled cache:  {snap['scaled_cache']}",
        f"Tinted cache:  {snap['tinted_cache']}",
        f"Frames sampled: {snap['frames']}",
    ]
    bg = pygame.Surface((240, len(lines) * 22 + 12))
    bg.fill((10, 10, 15))
    bg.set_alpha(200)
    screen.blit(bg, (SCREEN_W - 260, SCREEN_H - len(lines) * 22 - 32))
    for i, line in enumerate(lines):
        surf = font.render(line, True, (120, 220, 120))
        screen.blit(surf, (SCREEN_W - 252, SCREEN_H - len(lines) * 22 - 24 + i * 22))


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(
        "Particle Preset Browser — ← → to navigate, Space to burst  |  Tab = profiler"
    )
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)
    font_small = pygame.font.SysFont(None, 22)
    font_prof = pygame.font.SysFont(None, 19)

    idx = 0
    presets = PRESETS
    ps = build_particle_system(presets[idx]["config"])
    ps.emit_burst(60, AREA_X, AREA_Y, AREA_W, AREA_H)

    profiler = Profiler()
    show_profiler = False

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        profiler.begin_frame()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                    idx = (idx + 1) % len(presets)
                    ps = build_particle_system(presets[idx]["config"])
                    ps.emit_burst(60, AREA_X, AREA_Y, AREA_W, AREA_H)
                    profiler.clear()
                    from tilemap_parser.runtime.particles import clear_texture_caches as _clr
                    _clr()
                elif event.key in (pygame.K_LEFT, pygame.K_UP):
                    idx = (idx - 1) % len(presets)
                    ps = build_particle_system(presets[idx]["config"])
                    ps.emit_burst(60, AREA_X, AREA_Y, AREA_W, AREA_H)
                    profiler.clear()
                    from tilemap_parser.runtime.particles import clear_texture_caches as _clr
                    _clr()
                elif event.key == pygame.K_SPACE:
                    mx, my = pygame.mouse.get_pos()
                    ps.emit_burst(40, mx - 48, my - 48, 96, 96)
                elif event.key == pygame.K_TAB:
                    show_profiler = not show_profiler

        screen.fill((20, 20, 30))

        pygame.draw.rect(
            screen, (40, 40, 50), (AREA_X, AREA_Y, AREA_W, AREA_H), 1
        )

        ps.update(dt, AREA_X, AREA_Y, AREA_W, AREA_H)
        profiler.end_update()

        ps.draw(screen, 0, 0, 1)
        profiler.end_draw(ps.emitter)

        entry = presets[idx]
        name_surf = font.render(
            f"{entry['name']}  ({idx+1}/{len(presets)})", True, (255, 255, 200)
        )
        cat_surf = font_small.render(entry["category"], True, (180, 180, 200))
        desc_surf = font_small.render(entry["description"], True, (150, 150, 170))
        controls = font_small.render(
            "\u2190 \u2192 prev/next    Space burst    Tab profile    Esc quit",
            True,
            (100, 100, 120),
        )

        bar_y = 20
        screen.blit(name_surf, (20, bar_y))
        screen.blit(cat_surf, (20, bar_y + 32))
        screen.blit(desc_surf, (20, bar_y + 56))
        screen.blit(controls, (20, SCREEN_H - 32))

        if show_profiler:
            _render_profiler(screen, profiler.snapshot(), font_prof)

        pygame.display.flip()

    if show_profiler:
        print("\n=== Profiler Summary ===")
        for k, v in profiler.snapshot().items():
            print(f"  {k}: {v}")

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

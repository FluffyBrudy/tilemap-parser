"""
Tests for ParticleEmitter behavior — spawn_rate and manual emission.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

import pygame

from tilemap_parser.parser.particle import ParticleSystemConfig
from tilemap_parser.runtime.particles import (
    FOG_PROFILE,
    FieldLayerSpec,
    FieldProfile,
    ParticleEmitter,
    ParticleField,
    ParticleRenderer,
    ParticleSystem,
    _interp_color,
)


class TestInterpColorFadeModes:
    def test_fade_out_goes_start_to_end(self):
        c = _interp_color((10, 10, 10, 200), (10, 10, 10, 0), 0.0, 1)
        assert c[3] == 200
        c = _interp_color((10, 10, 10, 200), (10, 10, 10, 0), 1.0, 1)
        assert c[3] == 0

    def test_fade_in_goes_end_to_start(self):
        c = _interp_color((10, 10, 10, 80), (10, 10, 10, 0), 0.0, 2)
        assert c[3] == 0
        c = _interp_color((10, 10, 10, 80), (10, 10, 10, 0), 1.0, 2)
        assert c[3] == 80

    def test_fade_both_peaks_at_max_start_end(self):
        """fade_both must never exceed the configured peak alpha."""
        c = _interp_color((10, 10, 10, 26), (10, 10, 10, 0), 0.5, 3)
        assert c[3] == 26

    def test_fade_both_midpoints(self):
        c = _interp_color((10, 10, 10, 30), (10, 10, 10, 0), 0.25, 3)
        assert c[3] == 30
        c = _interp_color((10, 10, 10, 30), (10, 10, 10, 0), 0.75, 3)
        assert c[3] == 15

    def test_fade_both_opaque_still_peaks_255(self):
        """Existing fire/spark style (255 -> 0) keeps peaking at 255."""
        c = _interp_color((255, 200, 100, 255), (255, 100, 50, 0), 0.5, 3)
        assert c[3] == 255

    def test_fade_both_explicit_peak_bell_curve(self):
        """A configured peak allows a smooth 0 -> peak -> 0 bell, ideal for fog."""
        c = _interp_color((10, 10, 10, 0), (10, 10, 10, 0), 0.0, 3, peak_alpha=44)
        assert c[3] == 0
        c = _interp_color((10, 10, 10, 0), (10, 10, 10, 0), 0.25, 3, peak_alpha=44)
        assert c[3] == 22
        c = _interp_color((10, 10, 10, 0), (10, 10, 10, 0), 0.5, 3, peak_alpha=44)
        assert c[3] == 44
        c = _interp_color((10, 10, 10, 0), (10, 10, 10, 0), 0.75, 3, peak_alpha=44)
        assert c[3] == 22
        c = _interp_color((10, 10, 10, 0), (10, 10, 10, 0), 1.0, 3, peak_alpha=44)
        assert c[3] == 0

    def test_fade_peak_alpha_roundtrip(self):
        cfg = ParticleSystemConfig(name="fog", fade_peak_alpha=44)
        d = cfg.to_dict()
        assert d["fade_peak_alpha"] == 44
        again = ParticleSystemConfig.from_dict(d, name="fog")
        assert again.fade_peak_alpha == 44

    def test_fade_peak_alpha_omitted_when_unset(self):
        cfg = ParticleSystemConfig(name="fog")
        assert "fade_peak_alpha" not in cfg.to_dict()


class TestWrapMode:
    def _emitter(self, wrap=True, lifetime=5.0, count=50):
        cfg = ParticleSystemConfig(
            name="test",
            wrap=wrap,
            spawn_rate=0,
            max_particles=1000,
            particle_size_min=10,
            particle_size_max=10,
            speed_min=20,
            speed_max=20,
            direction=0,
            spread=0,
            lifetime_min=lifetime,
            lifetime_max=lifetime,
        )
        emitter = ParticleEmitter(cfg)
        emitter.emit_burst(count, 0, 0, 100, 100)
        return emitter

    def test_wrap_particles_never_die(self):
        """With wrap=True, tiny lifetimes do not kill particles."""
        emitter = self._emitter(lifetime=0.001)
        for _ in range(200):
            emitter.update(0.016, 0, 0, 100, 100)
        assert len(emitter.particles) == 50

    def test_wrap_count_stable_over_many_updates(self):
        emitter = self._emitter()
        for _ in range(2000):
            emitter.update(0.016, 0, 0, 100, 100)
        assert len(emitter.particles) == 50

    def test_wrap_progress_clamped_so_size_plateaus(self):
        """Life keeps ticking past zero in wrap mode; progress must clamp so
        current_size stops at end_size instead of extrapolating forever."""
        emitter = self._emitter(lifetime=0.5)
        for _ in range(300):
            emitter.update(0.016, 0, 0, 100, 100)
        for p in emitter.particles:
            assert p.life < 0
            assert 0.0 <= p.progress <= 1.0
            assert p.current_size <= p.end_size + 1e-6

    def test_wrap_keeps_particles_inside_bounds(self):
        emitter = self._emitter()
        for _ in range(1000):
            emitter.update(0.016, 0, 0, 100, 100)
        for p in emitter.particles:
            assert -p.current_size / 2 - 1 <= p.x <= 100 + p.current_size / 2 + 1
            assert -p.current_size / 2 - 1 <= p.y <= 100 + p.current_size / 2 + 1

    def test_wrap_reentry_preserves_velocity_and_offset(self):
        """A right-drifting particle exits right and re-enters left at the
        same y offset, keeping its velocity untouched."""
        cfg = ParticleSystemConfig(
            name="test",
            wrap=True,
            spawn_rate=0,
            max_particles=100,
            particle_size_min=10,
            particle_size_max=10,
            speed_min=30,
            speed_max=30,
            direction=0,
            spread=0,
            gravity_x=0,
            gravity_y=0,
            lifetime_min=5,
            lifetime_max=5,
        )
        emitter = ParticleEmitter(cfg)
        emitter.emit_burst(1, 0, 0, 100, 100)
        p = emitter.particles[0]
        p.x = 95.0
        p.y = 40.0
        p.vx = 30.0
        p.vy = 0.0
        for _ in range(100):
            emitter.update(0.1, 0, 0, 100, 100)
        assert abs(p.vx - 30.0) < 1e-9
        assert abs(p.vy) < 1e-9
        assert p.x <= 50  # wrapped back to the left half
        assert abs(p.y - 40.0) < 1.0  # exact offset preserved

    def test_wrap_preserves_color_and_size(self):
        emitter = self._emitter()
        for _ in range(500):
            emitter.update(0.016, 0, 0, 100, 100)
        for p in emitter.particles:
            assert p.alpha_fade == 1
            assert p.start_size == p.size * 1.0

    def test_wrap_config_roundtrip(self):
        cfg = ParticleSystemConfig(name="w", wrap=True)
        d = cfg.to_dict()
        assert d["wrap"] is True
        assert ParticleSystemConfig.from_dict(d, name="w").wrap is True
        assert ParticleSystemConfig(name="w").to_dict()["wrap"] is False

    def test_spawn_rate_zero_survives_roundtrip(self):
        """from_dict must not clamp spawn_rate to >= 1: 0 is the field mode."""
        cfg = ParticleSystemConfig(name="f", spawn_rate=0)
        assert cfg.to_dict()["spawn_rate"] == 0
        assert ParticleSystemConfig.from_dict(cfg.to_dict(), name="f").spawn_rate == 0


class TestFieldDensity:
    def _cfg(self, **over):
        base = dict(
            name="f",
            emission_shape="rect",
            particle_shape="fog",
            particle_size_min=100,
            particle_size_max=100,
        )
        base.update(over)
        return ParticleSystemConfig(**base)

    def test_count_for_coverage_rect(self):
        cfg = self._cfg()
        assert cfg.count_for_coverage(1.0, 1000, 1000) == 100
        assert cfg.count_for_coverage(0.5, 1000, 1000) == 50
        assert cfg.count_for_coverage(0.1, 1000, 1000) == 10

    def test_count_for_coverage_circle_emission_uses_disc_area(self):
        cfg = self._cfg(emission_shape="circle")
        # fill area is pi * 500^2, not 1000^2 -> ~78.5 sheets
        assert cfg.count_for_coverage(1.0, 1000, 1000) == 79

    def test_count_for_coverage_circle_particle_uses_disc_fill(self):
        cfg = self._cfg(particle_shape="circle")
        # sheet area pi/4 of the square -> needs ~127 to cover fully
        assert cfg.count_for_coverage(1.0, 1000, 1000) == 127

    def test_count_for_coverage_via_mean_size(self):
        cfg = self._cfg(particle_size_min=40, particle_size_max=60)
        assert cfg.count_for_coverage(1.0, 1000, 1000) == 400

    def test_count_for_coverage_rejects_point_and_bad_coverage(self):
        cfg = self._cfg(emission_shape="point")
        with pytest.raises(ValueError):
            cfg.count_for_coverage(0.5, 100, 100)
        with pytest.raises(ValueError):
            self._cfg().count_for_coverage(0, 100, 100)
        with pytest.raises(ValueError):
            self._cfg().count_for_coverage(-1, 100, 100)


class TestEmitField:
    def _field_system(self, **cfg_over):
        base = dict(
            name="field",
            wrap=True,
            spawn_rate=0,
            emission_shape="rect",
            particle_shape="fog",
            particle_size_min=100,
            particle_size_max=100,
            speed_min=5,
            speed_max=10,
            max_particles=1000,
        )
        base.update(cfg_over)
        return ParticleSystem(ParticleSystemConfig(**base))

    def test_emit_field_fills_coverage_count(self):
        ps = self._field_system()
        ps.emit_field(1.0, 0, 0, 1000, 1000)
        assert len(ps.emitter.particles) == 100
        ps.emit_field(0.5, 0, 0, 1000, 1000)
        assert len(ps.emitter.particles) == 150

    def test_emit_field_caps_at_max_particles(self):
        ps = self._field_system(max_particles=50)
        ps.emit_field(1.0, 0, 0, 1000, 1000)
        assert len(ps.emitter.particles) == 50

    def test_emit_field_requires_wrap(self):
        ps = ParticleSystem(ParticleSystemConfig(
            name="field", spawn_rate=0, particle_size_min=10,
            particle_size_max=10, max_particles=10))
        with pytest.raises(ValueError, match="wrap"):
            ps.emit_field(0.5, 0, 0, 100, 100)

    def test_emit_field_requires_spawn_rate_zero(self):
        ps = ParticleSystem(ParticleSystemConfig(
            name="field", wrap=True, spawn_rate=10, particle_size_min=10,
            particle_size_max=10, max_particles=10))
        with pytest.raises(ValueError, match="spawn_rate"):
            ps.emit_field(0.5, 0, 0, 100, 100)



class TestParticleEmitterSpawnRate:
    def test_spawn_rate_zero_prevents_auto_spawn(self):
        """With spawn_rate=0, update() never auto-spawns particles."""
        config = ParticleSystemConfig(
            name="test",
            spawn_rate=0,
            max_particles=100,
            speed_min=10,
            speed_max=100,
            lifetime_min=0.5,
            lifetime_max=2.0,
        )
        emitter = ParticleEmitter(config)

        for _ in range(100):
            emitter.update(0.016, 0, 0, 100, 100)

        assert len(emitter.particles) == 0

    def test_emit_burst_still_works_with_spawn_rate_zero(self):
        """emit_burst() creates particles regardless of spawn_rate=0."""
        config = ParticleSystemConfig(
            name="test",
            spawn_rate=0,
            max_particles=100,
            speed_min=10,
            speed_max=100,
            lifetime_min=0.5,
            lifetime_max=2.0,
        )
        emitter = ParticleEmitter(config)

        emitter.emit_burst(5, 0, 0, 100, 100)

        assert len(emitter.particles) == 5

    def test_spawn_rate_zero_particles_die_naturally(self):
        """Particles created via emit_burst with spawn_rate=0 live and die.

        After burst, particles exist. After their max lifetime passes,
        all are gone and the emitter returns to zero.
        """
        config = ParticleSystemConfig(
            name="test",
            spawn_rate=0,
            max_particles=100,
            speed_min=0,
            speed_max=0,
            lifetime_min=0.5,
            lifetime_max=0.5,
        )
        emitter = ParticleEmitter(config)

        emitter.emit_burst(3, 0, 0, 100, 100)
        assert len(emitter.particles) == 3

        for _ in range(30):
            emitter.update(0.05, 0, 0, 100, 100)
        assert len(emitter.particles) == 0


class _SpyRenderer(ParticleRenderer):
    def __init__(self) -> None:
        self.calls: list[int] = []

    def prepare(self, particles, config) -> None:  # type: ignore[no-untyped-def]
        pass

    def draw(self, screen, offset_x, offset_y, zoom, blend=0) -> None:  # type: ignore[no-untyped-def]
        self.calls.append(blend)

    def on_config_change(self, config) -> None:  # type: ignore[no-untyped-def]
        pass


class TestParticleField:
    def _counts(self, field):
        return [len(layer.system.emitter.particles) for layer in field.layers]

    def test_particle_field_uses_persistent_field_contract(self):
        field = ParticleField(area=(0, 0, 1000, 600))
        assert len(field.layers) == 1
        for layer in field.layers:
            cfg = layer.system.config
            assert cfg.wrap is True
            assert cfg.spawn_rate == 0
            assert cfg.particle_shape == "fog"
            assert cfg.emission_shape == "rect"
            assert cfg.alpha_fade == "none"
            assert cfg.gravity_x == 0
            assert cfg.gravity_y == 0

    def test_particle_field_counts_stay_stable(self):
        field = ParticleField(area=(0, 0, 1000, 600))
        before = self._counts(field)
        for _ in range(300):
            field.update(0.016)
        assert self._counts(field) == before

    def test_density_controls_particle_count(self):
        sparse = ParticleField(area=(0, 0, 1000, 600), density=0.5)
        dense = ParticleField(area=(0, 0, 1000, 600), density=1.5)
        assert sum(self._counts(dense)) > sum(self._counts(sparse))

    def test_alpha_and_color_clamp_safely(self):
        field = ParticleField(area=(0, 0, 1000, 600), color=(999, -5, 30), alpha=999)
        cfg = field.layers[0].system.config
        assert cfg.start_color_r == 255
        assert cfg.start_color_g == 0
        assert cfg.start_color_b == 30
        assert cfg.start_color_a == 255
        assert cfg.end_color_a == 255

    def test_set_density_refills_count(self):
        field = ParticleField(area=(0, 0, 1000, 600), density=0.5)
        before = sum(self._counts(field))
        field.set_density(1.5)
        assert sum(self._counts(field)) > before

    def test_set_area_updates_layer_areas(self):
        field = ParticleField(area=(0, 0, 1000, 600))
        field.set_area((10, 20, 300, 200))
        assert field.layers[0].area == (10, 20, 300, 200)

    def test_set_motion_updates_config(self):
        field = ParticleField(area=(0, 0, 1000, 600))
        field.set_motion(direction=180, speed=(3, 8), spread=45)
        cfg = field.layers[0].system.config
        assert cfg.direction == 180
        assert cfg.speed_min == 3
        assert cfg.speed_max == 8
        assert cfg.spread == 45

    def test_set_color_updates_config(self):
        field = ParticleField(area=(0, 0, 1000, 600))
        field.set_color((180, 150, 100))
        cfg = field.layers[0].system.config
        assert (cfg.start_color_r, cfg.start_color_g, cfg.start_color_b) == (180, 150, 100)
        assert cfg.start_color_a == 14  # color only: alpha untouched

    def test_set_color_keeps_profile_layers(self):
        field = ParticleField(area=(0, 0, 1000, 600), profile=FOG_PROFILE)
        field.set_color((180, 150, 100))
        assert [layer.name for layer in field.layers] == ["far", "mid", "near"]
        assert field.layers[1].system.config.start_color_a == 16

    def test_quality_is_a_budget_dial_not_a_layer_trimmer(self):
        low = ParticleField(area=(0, 0, 1000, 600), profile=FOG_PROFILE, quality="low")
        high = ParticleField(area=(0, 0, 1000, 600), profile=FOG_PROFILE, quality="high")
        assert len(low.layers) == 3  # layer structure belongs to the profile
        assert len(high.layers) == 3
        assert sum(self._counts(high)) > sum(self._counts(low))
        assert high.layers[0].system.config.max_particles > low.layers[0].system.config.max_particles

    def test_global_alpha_scales_preset_alphas_and_clamps(self):
        low = ParticleField(area=(0, 0, 1000, 600), profile=FOG_PROFILE, global_alpha=0.5)
        high = ParticleField(area=(0, 0, 1000, 600), profile=FOG_PROFILE, global_alpha=99)
        assert low.layers[1].system.config.start_color_a == 8  # 16 * 0.5
        assert high.layers[1].system.config.start_color_a == 16  # clamped to 1.0

    def test_global_alpha_property_refills(self):
        field = ParticleField(area=(0, 0, 1000, 600), profile=FOG_PROFILE)
        field.global_alpha = 0.5
        assert field.global_alpha == 0.5
        assert field.layers[1].system.config.start_color_a == 8
        assert field.layers[2].system.config.start_color_a == 5  # 10 * 0.5

    def test_fog_profile_preserves_layer_names_and_defaults(self):
        field = ParticleField(
            area=(0, 0, 1000, 600), profile=FOG_PROFILE, direction=0, speed=(8, 8)
        )
        assert [layer.name for layer in field.layers] == ["far", "mid", "near"]
        assert field.layers[0].system.config.particle_size_min == 90
        assert field.layers[1].system.config.particle_size_min == 60
        assert field.layers[2].system.config.particle_size_min == 40
        assert field.layers[0].system.config.speed_min == pytest.approx(8 * 0.38)

    def test_field_emits_hand_verified_count(self):
        field = ParticleField(area=(0, 0, 100, 100), size=(10, 10), speed=(2, 2))
        assert self._counts(field) == [100]

    def test_quality_orders_counts_high_medium_low(self):
        def total(q):
            field = ParticleField(area=(0, 0, 1000, 600), profile=FOG_PROFILE, quality=q)
            return sum(self._counts(field))

        assert total("high") > total("medium") > total("low")

    def test_custom_profile_drives_layers(self):
        profile = FieldProfile(
            "dust",
            (
                FieldLayerSpec("blown", 50, 80, 1.0, 1.0, 12, 2.0),
                FieldLayerSpec("settled", 20, 30, 0.5, 0.7, 8, 3.0, True),
            ),
        )
        field = ParticleField(area=(10, 20, 1000, 600), profile=profile, ground_bias=True)
        assert [layer.name for layer in field.layers] == ["blown", "settled"]
        assert field.layers[0].system.config.particle_size_min == 50
        assert field.layers[1].area == (10, 230.0, 1000, 390.0)

    def test_ground_bias_moves_near_layer_to_lower_band(self):
        field = ParticleField(area=(10, 20, 1000, 600), profile=FOG_PROFILE, ground_bias=True)
        near = field.layers[-1]
        assert near.name == "near"
        assert near.area == (10, 230.0, 1000, 390.0)

        full = ParticleField(area=(10, 20, 1000, 600), profile=FOG_PROFILE, ground_bias=False)
        assert full.layers[-1].area == (10, 20, 1000, 600)

    def test_invalid_quality_errors(self):
        with pytest.raises(ValueError, match="quality"):
            ParticleField(area=(0, 0, 100, 100), quality="ultra")

    def test_with_alpha_returns_new_profile_with_scaled_alpha(self):
        light = FOG_PROFILE.with_alpha(0.5)
        assert light.name == FOG_PROFILE.name
        assert [p.alpha for p in light.presets] == [5, 8, 5]
        for scaled, source in zip(light.presets, FOG_PROFILE.presets, strict=True):
            assert (
                source.name,
                source.size_min,
                source.size_max,
                source.speed_min_mul,
                source.speed_max_mul,
                source.coverage,
                source.ground_layer,
            ) == (
                scaled.name,
                scaled.size_min,
                scaled.size_max,
                scaled.speed_min_mul,
                scaled.speed_max_mul,
                scaled.coverage,
                scaled.ground_layer,
            )

    def test_with_alpha_does_not_mutate_original(self):
        original = FOG_PROFILE.presets
        FOG_PROFILE.with_alpha(2.0)
        assert FOG_PROFILE.presets == original

    def test_with_alpha_clamps_and_sets_name(self):
        assert FOG_PROFILE.with_alpha(20.0).presets[1].alpha == 255
        assert FOG_PROFILE.with_alpha(0.0).presets[1].alpha == 0
        assert FOG_PROFILE.with_alpha(0.5, name="mist").name == "mist"
        assert FOG_PROFILE.with_alpha(0.5).name == "fog"

    def test_global_alpha_never_mutates_profile_data(self):
        before = tuple(p.alpha for p in FOG_PROFILE.presets)
        field = ParticleField(area=(0, 0, 1000, 600), profile=FOG_PROFILE)
        field.global_alpha = 0.5
        field.refill()
        assert tuple(p.alpha for p in FOG_PROFILE.presets) == before
        assert field.layers[1].system.config.start_color_a == 8

    def test_blend_flags_reach_renderer(self):
        spy = _SpyRenderer()
        field = ParticleField(area=(0, 0, 200, 150), profile=FOG_PROFILE, blend=pygame.BLEND_RGB_ADD)
        for layer in field.layers:
            layer.system.renderer = spy
        field.draw(pygame.Surface((200, 150), pygame.SRCALPHA), 0, 0, 1.0)
        assert len(spy.calls) == len(field.layers)
        assert all(blend == pygame.BLEND_RGB_ADD for blend in spy.calls)

    def test_default_blend_zero_reaches_renderer(self):
        spy = _SpyRenderer()
        field = ParticleField(area=(0, 0, 200, 150), profile=FOG_PROFILE)
        for layer in field.layers:
            layer.system.renderer = spy
        field.draw(pygame.Surface((200, 150), pygame.SRCALPHA), 0, 0, 1.0)
        assert len(spy.calls) == len(field.layers)
        assert all(blend == 0 for blend in spy.calls)

    def test_blend_kwarg_accepted_and_stored(self):
        for flag in (0, pygame.BLEND_RGB_ADD, pygame.BLEND_RGBA_ADD, pygame.BLEND_PREMULTIPLIED):
            field = ParticleField(area=(0, 0, 200, 150), blend=flag)
            assert field.blend == flag

    def test_draw_with_blend_flags_produces_pixels(self):
        field = ParticleField(area=(0, 0, 200, 150), profile=FOG_PROFILE, direction=0, speed=(4, 4))
        flags = (0, pygame.BLEND_RGB_ADD, pygame.BLEND_RGBA_ADD, pygame.BLEND_PREMULTIPLIED)
        for flag in flags:
            field.blend = flag
            surf = pygame.Surface((200, 150), pygame.SRCALPHA)
            field.draw(surf, 0, 0, 1.0)
            raw = pygame.image.tobytes(surf, "RGBA")
            covered = sum(1 for i in range(0, len(raw), 4) if raw[i] or raw[i + 1] or raw[i + 2])
            assert covered > 200, f"blend {flag}: nothing drawn"

    def test_additive_composite_trick_brightens_scene(self):
        field = ParticleField(area=(0, 0, 200, 150), profile=FOG_PROFILE, direction=0, speed=(4, 4))
        rgb = pygame.Surface((200, 150))
        field.draw(rgb, 0, 0, 1.0)
        scene = pygame.Surface((200, 150))
        scene.fill((10, 10, 10))
        scene.blit(rgb, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        raw = pygame.image.tobytes(scene, "RGB")
        total = sum(raw[i] for i in range(0, len(raw), 3))
        assert total > 200 * 150 * 10

    def test_direction_random_maps_to_omnidirectional_sentinel(self):
        field = ParticleField(area=(0, 0, 200, 150), direction="random")
        assert field.direction == "random"
        assert all(layer.system.config.direction == -1.0 for layer in field.layers)

    def test_direction_random_via_set_motion(self):
        field = ParticleField(area=(0, 0, 200, 150), direction=90)
        field.set_motion(direction="random")
        assert field.direction == "random"
        assert field.layers[0].system.config.direction == -1.0

    def test_direction_random_particles_move_every_way(self):
        import random

        random.seed(1234)
        field = ParticleField(area=(0, 0, 1000, 600), direction="random", size=(10, 12), speed=(2, 2))
        system = field.layers[0].system
        assert len(system.emitter.particles) >= 500, "guard needs a large sample"
        vx_signs = {1 if p.vx >= 0 else -1 for p in system.emitter.particles}
        vy_signs = {1 if p.vy >= 0 else -1 for p in system.emitter.particles}
        assert vx_signs == {-1, 1}, "random drift must cover both horizontal directions"
        assert vy_signs == {-1, 1}, "random drift must cover both vertical directions"

    def test_invalid_direction_string_errors(self):
        with pytest.raises(ValueError, match="direction"):
            ParticleField(area=(0, 0, 200, 150), direction="up")

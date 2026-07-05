from typing import Optional, cast

from pygame import Rect
from tilemap_parser import (
    Camera,
    CollisionRunner,
    ParticleSystem,
    TileLayerRenderer,
    TilesetCollision,
    check_collision,
    get_shape_aabb,
    load_map,
)
from tilemap_parser.runtime.collision_cache import _global_cache

from src.effects import CircleTransition, TransitionState
from src.entities import Bullet, Player
from src.entities.collision.resolver import resolve_player_enemy_hit
from src.entities.enemies.arial import EyeFire, MutatedBat
from src.entities.enemies.base import EnemyManager
from src.entities.enemies.devilkin2 import Devilkin2
from src.entities.tilemap import Tilemap
from src.settings import *
from src.utils.pgdebug import Debug, pgdebug
from src.utils.shape import get_sprite_center
from src.utils.soundmanager import SoundManager
from src.world_context import world_context


class LevelScene:
    __slots__ = (
        "collision_runner",
        "collision_tileset",
        "tile_renderer",
        "player",
        "tilemap",
        "enemy_manager",
        "bullet_effect",
        "blood_effect",
        "snow",
        "star",
        "camera",
        "soundmanager",
        "level_name",
        "exit_rect",
        "transition",
        "on_transition_complete",
        "exit_reached",
    )

    def __init__(self, level_name: str = "level1", on_transition_complete=None):
        self.level_name = level_name
        self.on_transition_complete = on_transition_complete
        self.exit_reached = False

        mapdata = load_map(
            DATA_PATH / "maps" / f"{level_name}.json",
            nodes_dir=NODES_PATH,
        )

        self.collision_tileset = cast(
            TilesetCollision,
            _global_cache.get_tileset_collision(COLLISION_TILESET_PATH / "tileset-collision.collision.json"),
        )
        self.tile_renderer = TileLayerRenderer(data=mapdata)
        self.tile_renderer.warm_cache()

        self.collision_runner = CollisionRunner.from_game_type(
            "platformer",
            mapdata.tile_size,
            strict=True,
            render_scale=mapdata.render_scale,
        )

        node = mapdata.area_nodes[0]
        rs = mapdata.render_scale

        bullet_cfg = next(pn for pn in mapdata.particle_emitters if pn.name == "bulletEffect").config
        bullet_cfg.apply_render_scale(rs)
        self.bullet_effect = ParticleSystem(bullet_cfg)
        self.bullet_effect.config.spawn_rate = 0
        self.bullet_effect.config.direction = -1
        self.bullet_effect.emitter.clear()

        blood_cfg = next(pn for pn in mapdata.particle_emitters if pn.name == "blood").config
        blood_cfg.apply_render_scale(rs)
        self.blood_effect = ParticleSystem(blood_cfg)
        self.blood_effect.config.spawn_rate = 0
        self.blood_effect.config.direction = -1
        self.blood_effect.emitter.clear()

        self.snow = ParticleSystem(
            next(pn for pn in mapdata.particle_emitters if pn.name == "snow").config,
        )
        self.star = ParticleSystem(
            next(pn for pn in mapdata.particle_emitters if pn.name == "starysky").config,
        )
        self.player = Player(node.rect.centerx * rs, node.rect.top * rs)
        self.tilemap = Tilemap(mapdata, self.collision_tileset)

        self.snow.config.apply_render_scale(self.tilemap.render_scale)
        self.star.config.apply_render_scale(self.tilemap.render_scale)

        self.soundmanager = SoundManager()
        self.soundmanager.add_sound(ASSETS_PATH / "sounds" / "Shoot.wav", "player_shoot", "sfx")
        self.soundmanager.add_sound(ASSETS_PATH / "sounds" / "Hit.wav", "player_hit", "sfx")
        self.soundmanager.add_sound(ASSETS_PATH / "sounds" / "enemy_death.wav", "enemy_death", "sfx")
        self.soundmanager.add_sound(ASSETS_PATH / "sounds" / "Jump.wav", "player_jump", "sfx")
        self.soundmanager.add_sound(ASSETS_PATH / "sounds" / "Nextlevel.wav", "next_level", "main")
        self.soundmanager.add_sound(ASSETS_PATH / "sounds" / "Powerup.wav", "powerup", "sfx")

        world_context.player = self.player

        self.enemy_manager = EnemyManager()
        self._spawn_enemies()

        self.camera = Camera(WIDTH, HEIGHT, mode="deadzone")
        self.camera.lerp_speed = 1

        self.transition = CircleTransition(WIDTH, HEIGHT)
        self.transition.start_open()

        self.exit_rect = self._find_exit_rect(mapdata, rs)

    def _spawn_enemies(self):
        s = EnemyManager.spawn
        t = self.player
        s(EyeFire, 400, 400, t)
        s(MutatedBat, 800, 1000, t)
        s(MutatedBat, 600, 600, t)
        s(MutatedBat, 1400, 500, t)
        s(Devilkin2, 1100, 0, t)
        s(Devilkin2, 100, 300, t)
        s(Devilkin2, 1500, 0, t)
        s(Devilkin2, 100, 800, t)
        s(EyeFire, 1000, 300, t)

    def _find_exit_rect(self, mapdata, rs: float) -> Optional[Rect]:
        for an in mapdata.area_nodes:
            if an.name == "exit":
                return Rect(
                    an.rect.x * rs,
                    an.rect.y * rs,
                    an.rect.w * rs,
                    an.rect.h * rs,
                )
        return None

    def _on_bullet_wall(self, left: float, top: float, right: float, bottom: float) -> bool:
        if self.tilemap.rect_collides(left, top, right, bottom):
            self.bullet_effect.emit_burst(15, (left + right) * 0.5, (top + bottom) * 0.5, 1, 1)
            return True
        return False

    def handle_enemy_player_collision(self):
        if self.player.is_hitted:
            return
        hit = self.enemy_manager.manager.check_object_first(self.player)
        if hit is not None:
            resolve_player_enemy_hit(self.player, hit)
            if self.player.is_hitted:
                self.soundmanager.play("player_hit", "sfx")
                self.camera.shake(0.3, 6.0)
            enemy = hit.other(self.player)
            if isinstance(enemy, MutatedBat) and enemy.current_state.name == "explode":
                self.camera.shake(0.5, 8.0)
                l, t, r, b = get_shape_aabb(enemy.x, enemy.y, enemy.collision_shape)
                self.blood_effect.emit_burst(60, (l + r) * 0.5, (t + b) * 0.5, 1, 1)
            if isinstance(enemy, Devilkin2) and enemy.current_state.name == "attack":
                self.camera.shake(0.5, 8)

    def _handle_bullet_enemy_collision(self):
        for enemy in self.enemy_manager.get_enemies():
            bullets_to_remove = set()
            for bullet in Bullet.bullet_group:
                if not check_collision(bullet, enemy):
                    continue
                if isinstance(enemy, Devilkin2) and not enemy.take_damage(1):
                    continue
                bullets_to_remove.add(bullet)
                cx, cy = get_sprite_center(enemy)
                if isinstance(enemy, Devilkin2):
                    self.blood_effect.emit_burst(6, cx, cy, 1, 1)
                    if enemy.hp <= 0:
                        self.blood_effect.emit_burst(100, cx, cy, 1, 1)
                        self.soundmanager.play("enemy_death", "sfx")
                elif isinstance(enemy, MutatedBat):
                    enemy.take_damage(1)
                    self.blood_effect.emit_burst(6, cx, cy, 1, 1)
                    if enemy.hp <= 0:
                        self.blood_effect.emit_burst(80, cx, cy, 1, 1)
                        self.soundmanager.play("enemy_death", "sfx")
                elif isinstance(enemy, EyeFire):
                    enemy.take_damage(1)
                    self.blood_effect.emit_burst(4, cx, cy, 1, 1)
                    if enemy.hp <= 0:
                        self.blood_effect.emit_burst(60, cx, cy, 1, 1)
                        self.soundmanager.play("enemy_death", "sfx")

            Bullet.bullet_group -= bullets_to_remove

    def _update_ground_enemy_physics(self, dt: float) -> None:
        for enemy in self.enemy_manager.get_enemies():
            if not isinstance(enemy, Devilkin2):
                continue
            if not enemy.on_ground:
                enemy.vy += self.collision_runner.gravity * dt
                if enemy.vy > self.collision_runner.max_fall_speed:
                    enemy.vy = self.collision_runner.max_fall_speed
            self.collision_runner.move_platformer(
                enemy,
                self.collision_tileset,
                self.tilemap.tilemap,
                dt,
                velocity=(enemy.vx, enemy.vy),
            )

    def update(self, dt):
        self.transition.update(dt)

        if self.transition.state is TransitionState.OPENING:
            return

        if not self.exit_reached and self.transition.state is TransitionState.NONE:
            self.collision_runner.move_platformer(
                self.player,
                self.collision_tileset,
                self.tilemap.tilemap,
                dt,
                self.player.input_x,
                self.player.jump_pressed,
                self.player.velocity_override,
            )
            self.player.update(dt)
            self.handle_enemy_player_collision()
            self._handle_bullet_enemy_collision()
            Bullet.update(dt, self._on_bullet_wall)
            self.enemy_manager.update(dt)
            self._update_ground_enemy_physics(dt)
            self.bullet_effect.update(dt, 0, 0, 0, 0)
            self.blood_effect.update(dt, 0, 0, 0, 0)

            self.camera.follow(self.player)
            self.camera.update(dt)
            self.snow.update(dt, self.camera.x, self.camera.y + HEIGHT // 4, WIDTH, HEIGHT // 2)
            self.star.update(dt, self.camera.x, self.camera.y + HEIGHT // 6, WIDTH, HEIGHT // 2)

            if self.exit_rect is not None:
                pcx, pcy = get_sprite_center(self.player)
                if self.exit_rect.collidepoint(pcx, pcy):
                    self.exit_reached = True
                    self.soundmanager.play("next_level", "main")
                    cx = int(pcx - self.camera.x)
                    cy = int(pcy - self.camera.y)
                    self.transition.start_close(
                        center_x=cx,
                        center_y=cy,
                        on_complete=self._on_close_complete,
                    )

        pgdebug(f"{1 / dt}")

    def _on_close_complete(self):
        if self.on_transition_complete:
            self.on_transition_complete(self)

    def draw(self, screen):
        screen.fill(BLACK)
        camera_offset = self.camera.offset
        self.tile_renderer.render(screen, camera_offset)
        self.snow.draw(screen, self.camera.x, self.camera.y, 1.0)
        self.star.draw(screen, self.camera.x, self.camera.y, 1.0)
        self.bullet_effect.draw(screen, self.camera.x, self.camera.y, 1.0)
        self.blood_effect.draw(screen, self.camera.x, self.camera.y, 1.0)
        Bullet.render(screen, camera_offset)
        self.player.render(screen, camera_offset)
        EnemyManager.render(screen, camera_offset, (self.player.x, self.player.y))
        self.transition.draw(screen)
        Debug.draw_all(screen)

    def emit_bullet_burst(self):
        l, t, r, b = get_shape_aabb(self.player.x, self.player.y, self.player.collision_shape)
        self.bullet_effect.emit_burst(30, (l + r) * 0.5, (t + b) * 0.5, 1, 1)

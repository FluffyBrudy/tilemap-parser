from typing import Optional

from tilemap_parser import check_collision
from tilemap_parser.runtime.collision_cache import _global_cache

from src.entities.entity import Entity
from src.entities.fsm import BaseFsm, StateManager
from src.entities.projectiles.bullet import Bullet
from src.settings import ANIMATION_PATH, CHARACTER_COLLISION_PATH, DEFAULT_CHANGE_RANGE, SPEED_NORMAL
from src.utils.shape import get_sprite_center
from src.utils.target_movement import EnemyTargetMoverConfig, velocity_toward_target

CHASE_RANGE = DEFAULT_CHANGE_RANGE


class Devilkin2(Entity):
    collision_name = "devilkin2.collision.json"
    anim_name = "devilkin2.anim.json"
    move_speed = SPEED_NORMAL

    def __init__(self, x: float, y: float) -> None:
        collision = _global_cache.get_character_collision(
            CHARACTER_COLLISION_PATH / self.collision_name,
        )
        if collision is None:
            raise ValueError(f"Unable to load {self.collision_name}")

        mover_cfg = EnemyTargetMoverConfig(speed=self.move_speed, stop_dist=30)
        super().__init__(
            x,
            y,
            collision,
            ANIMATION_PATH / self.anim_name,
            self.make_states(mover_cfg),
            apply_shape_bound=True,
        )
        self.current_state = self.states["idle"]
        self.target: Optional[Entity] = None
        self.hp = 3
        self.spawn_x = x
        self.attack_range = 45
        self.hit_flag = False
        self.invulnerable_timer = 0.0
        self.on_ground = False
        self.detection_range = CHASE_RANGE

    def set_target(self, entity: Entity) -> None:
        self.target = entity

    def take_damage(self, amount: int = 1) -> bool:
        if self.invulnerable_timer > 0:
            return False
        self.hp -= amount
        self.hit_flag = True
        return True

    def can_kill(self) -> bool:
        if self.hp <= 0:
            return True
        return self.current_state.name == "death" and self.animation_states["death"].finished

    def make_states(self, mover_cfg: EnemyTargetMoverConfig) -> dict[str, BaseFsm]:
        return {
            "idle": DevilkinIdleFsm("idle"),
            "run": DevilkinRunFsm("run", mover_cfg),
            "attack": DevilkinAttackFsm("attack"),
            "hurt": DevilkinHurtFsm("hurt"),
            "death": DevilkinDeathFsm("death"),
        }

    def update(self, dt: float) -> None:
        if self.hit_flag:
            self.hit_flag = False
            self.current_state.exit(self)
            if self.hp <= 0:
                self.current_state = self.states["death"]
                self.animation_states["death"].reset()
            else:
                self.current_state = self.states["hurt"]
                self.animation_states["hurt"].reset()
                self.invulnerable_timer = 0.3
            self.current_state.enter(self)

        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= dt

        # FSM sets vx/vy for physics to use — position is handled by move_platformer in scene
        StateManager.update(self)
        self.animation_states[self.current_state.name].update(dt * 1000)


class DevilkinIdleFsm(BaseFsm):
    def enter(self, entity: Devilkin2, /) -> None:
        entity.vx = 0

    def get_next_state(self, entity: Devilkin2, /) -> str | None:
        target = entity.target
        if target is None:
            return None

        ecx, ecy = get_sprite_center(entity)
        tcx, tcy = get_sprite_center(target)
        dx = tcx - ecx
        dy = tcy - ecy
        length = (dx * dx + dy * dy) ** 0.5

        if length <= entity.detection_range:
            return "run"
        return None


class DevilkinRunFsm(BaseFsm):
    def __init__(self, name: str, mover_cfg: EnemyTargetMoverConfig) -> None:
        super().__init__(name)
        self.mover_cfg = mover_cfg

    def enter(self, entity: Devilkin2, /) -> None:
        entity.vx = 0

    def update(self, entity: Devilkin2, /) -> None:
        target = entity.target
        if target is None or getattr(target, "is_hitted", False):
            entity.vx = 0
            return
        vx, _vy, _length = velocity_toward_target(entity, target, config=self.mover_cfg)
        entity.vx = vx
        entity.flipped = entity.vx < 0

    def get_next_state(self, entity: Devilkin2, /) -> str | None:
        target = entity.target
        if target is None:
            return "idle"

        if getattr(target, "is_hitted", False):
            return None

        ecx, ecy = get_sprite_center(entity)
        tcx, tcy = get_sprite_center(target)
        dx = tcx - ecx
        dy = tcy - ecy
        length = (dx * dx + dy * dy) ** 0.5

        if length <= entity.attack_range:
            return "attack"
        if length > CHASE_RANGE * 1.5:
            return "idle"
        return None


class DevilkinAttackFsm(BaseFsm):
    def enter(self, entity: Devilkin2, /) -> None:
        entity.vx = 0

    def get_next_state(self, entity: Devilkin2, /) -> str | None:
        if entity.animation_states["attack"].finished:
            target = entity.target
            if target is not None:
                ecx, ecy = get_sprite_center(entity)
                tcx, tcy = get_sprite_center(target)
                dx = tcx - ecx
                dy = tcy - ecy
                length = (dx * dx + dy * dy) ** 0.5
                if length <= CHASE_RANGE:
                    return "run"
            return "idle"
        return None


class DevilkinHurtFsm(BaseFsm):
    def enter(self, entity: Devilkin2, /) -> None:
        entity.vx = 0

    def get_next_state(self, entity: Devilkin2, /) -> str | None:
        if entity.animation_states["hurt"].finished:
            return "idle"
        return None


class DevilkinDeathFsm(BaseFsm):
    def enter(self, entity: Devilkin2, /) -> None:
        entity.vx = 0

    def get_next_state(self, entity: Devilkin2, /) -> str | None:
        return None

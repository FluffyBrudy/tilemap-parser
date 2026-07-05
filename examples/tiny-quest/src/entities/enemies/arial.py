from typing import Optional

from tilemap_parser.runtime.collision_cache import _global_cache

from src.entities.entity import Entity
from src.entities.fsm import BaseFsm
from src.settings import ANIMATION_PATH, CHARACTER_COLLISION_PATH, DEFAULT_CHANGE_RANGE, SPEED_LOW
from src.utils.pgdebug import pgdebug
from src.utils.shape import get_sprite_center, is_close_to
from src.utils.target_movement import EnemyTargetMoverConfig, velocity_toward_target

CHASE_RANGE = DEFAULT_CHANGE_RANGE


class ArialEnemyBase(Entity):
    collision_name: str
    anim_name: str
    move_speed: float
    stop_dist: float = 5
    initial_state: str = "idle"

    def __init__(self, x: float, y: float) -> None:
        collision = _global_cache.get_character_collision(
            CHARACTER_COLLISION_PATH / self.collision_name,
        )
        if collision is None:
            raise ValueError(f"Unable to load {self.collision_name}")

        mover_cfg = EnemyTargetMoverConfig(speed=self.move_speed, stop_dist=self.stop_dist)

        super().__init__(
            x,
            y,
            collision,
            ANIMATION_PATH / self.anim_name,
            self.make_states(mover_cfg),
        )
        self.current_state = self.states[self.initial_state]
        self.spawn_coor = get_sprite_center(self)[:2]
        self.target: Optional[Entity] = None
        self.hp = 2
        self.hit_flag = False
        self.detection_range = CHASE_RANGE

    def can_kill(self) -> bool:
        return self.hp <= 0

    def take_damage(self, amount: int = 1) -> None:
        self.hp -= amount
        self.hit_flag = True

    def make_states(self, mover_cfg: EnemyTargetMoverConfig) -> dict[str, BaseFsm]:
        raise NotImplementedError

    def set_target(self, entity: Entity) -> None:
        self.target = entity

    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.hit_flag = False
        return super().update(dt)


class EyeFire(ArialEnemyBase):
    collision_name = "eye_fire_red.collision.json"
    anim_name = "eye_fire_red.anim.json"
    move_speed = SPEED_LOW
    stop_dist = 5
    initial_state = "chase"

    def make_states(self, mover_cfg: EnemyTargetMoverConfig) -> dict[str, BaseFsm]:
        return {
            "idle": EyeFireIdleFsm("idle"),
            "chase": EyeFireChaseFsm("chase", mover_cfg),
        }

    def can_kill(self) -> bool:
        return self.hp <= 0 or super().can_kill()


class MutatedBat(ArialEnemyBase):
    collision_name = "mutated-bat.collision.json"
    anim_name = "mutated-bat.anim.json"
    move_speed = SPEED_LOW
    stop_dist = 8
    initial_state = "flyidle"

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y)
        self.apply_shape_bound = False

        self.explode_radius = getattr(_global_cache.get_character_collision(self.collision_name), "radius", 5)

    def make_states(self, mover_cfg: EnemyTargetMoverConfig) -> dict[str, BaseFsm]:
        return {
            "flyidle": MutatedBatIdleFsm("flyidle"),
            "chase": MutatedBatChaseFsm("chase", mover_cfg),
            "explode": MutatedExplodeFsm("explode"),
        }

    def can_kill(self) -> bool:
        if self.hp <= 0:
            return True
        current_name = self.current_state.name
        return current_name == "explode" and self.animation_states[current_name].finished


class ArialNoActionFsm(BaseFsm):
    def enter(self, entity: "ArialEnemyBase", /) -> None:
        entity.vx = 0
        entity.vy = 0

    def update(self, entity: "ArialEnemyBase", /) -> None:
        is_close, dirs = is_close_to(entity, entity.spawn_coor, 5)
        if not is_close:
            entity.vx = dirs[0] * SPEED_LOW
            entity.vy = dirs[1] * SPEED_LOW
            entity.flipped = entity.vx > 0
        elif (entity.vx != 0) or (entity.vy != 0):
            entity.vx = 0
            entity.vy = 0


class ArialFollowTargetFsm(BaseFsm):
    def __init__(self, name: str, mover_cfg: EnemyTargetMoverConfig) -> None:
        super().__init__(name)
        self.mover_cfg = mover_cfg

    def enter(self, entity: "EyeFire", /) -> None:
        entity.vx = 0
        entity.vy = 0

    def update(self, entity: "EyeFire", /) -> None:
        target = entity.target
        if target is None or getattr(target, "is_hitted", False):
            entity.vx = 0
            entity.vy = 0
            return

        vx, vy, _length = velocity_toward_target(entity, target, config=self.mover_cfg)
        entity.vx = vx
        entity.vy = vy
        entity.flipped = entity.vx > 0


class EyeFireIdleFsm(ArialNoActionFsm):
    def get_next_state(self, entity: "EyeFire", /) -> str | None:
        target = entity.target
        if target is None or getattr(target, "is_hitted", False):
            return None

        ecx, ecy = get_sprite_center(entity)
        tcx, tcy = get_sprite_center(target)
        dx = tcx - ecx
        dy = tcy - ecy
        length = (dx * dx + dy * dy) ** 0.5

        if length <= entity.detection_range:
            return "chase"
        return None


class EyeFireChaseFsm(ArialFollowTargetFsm):
    def get_next_state(self, entity: "EyeFire", /) -> str | None:
        target = entity.target
        if target is None:
            return "idle"

        ecx, ecy = get_sprite_center(entity)
        tcx, tcy = get_sprite_center(target)
        dx = tcx - ecx
        dy = tcy - ecy
        length = (dx * dx + dy * dy) ** 0.5

        if length > CHASE_RANGE:
            return "idle"
        return None


class MutatedBatIdleFsm(ArialNoActionFsm):
    def get_next_state(self, entity: "EyeFire", /) -> str | None:
        target = entity.target
        if target is None or getattr(target, "is_hitted", False):
            return None

        ecx, ecy = get_sprite_center(entity)
        tcx, tcy = get_sprite_center(target)
        dx = tcx - ecx
        dy = tcy - ecy
        length = (dx * dx + dy * dy) ** 0.5

        if length <= entity.detection_range:
            return "chase"
        return None


class MutatedBatChaseFsm(ArialFollowTargetFsm):
    def get_next_state(self, entity: "MutatedBat", /) -> str | None:
        target = entity.target
        if target is None:
            return "flyidle"

        ecx, ecy = get_sprite_center(entity)
        tcx, tcy = get_sprite_center(target)
        dx = tcx - ecx
        dy = tcy - ecy
        length = (dx * dx + dy * dy) ** 0.5

        pgdebug(f"{entity.current_state.name}")
        if length > CHASE_RANGE:
            return "flyidle"
        if getattr(target, "is_hitted", False):
            return None
        if length <= 2 * entity.explode_radius:
            return "explode"

        return None


class MutatedExplodeFsm(BaseFsm):
    def enter(self, entity: "MutatedBat", /) -> None:
        entity.vx = 0
        entity.vy = 0

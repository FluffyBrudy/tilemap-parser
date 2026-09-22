from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

PathLike = Union[str, Path]

TANIM_VERSION = 1
TANIM_SUFFIX = ".tanim.json"
ANIM_CLIP_KEY = "anim_clip"
MODE_DEFAULT = "default"
MODE_RANDOM_START = "random_start_times"


@dataclass(frozen=True)
class TileClipFrame:
    sheet: str = ""
    variant: int = 0
    duration_ms: float = 100.0


@dataclass(frozen=True)
class TileAnimClip:
    name: str = ""
    frames: Tuple[TileClipFrame, ...] = ()
    loop: bool = True
    mode: str = MODE_DEFAULT

    def total_duration_ms(self) -> float:
        return sum(f.duration_ms for f in self.frames)


def _is_frame(frame: Any) -> bool:
    return (
        isinstance(frame, dict)
        and isinstance(frame.get("sheet"), str)
        and bool(frame.get("sheet"))
        and isinstance(frame.get("variant"), int)
        and not isinstance(frame.get("variant"), bool)
        and frame.get("variant") >= 0
        and isinstance(frame.get("duration_ms", 100.0), (int, float))
        and not isinstance(frame.get("duration_ms", 100.0), bool)
        and frame.get("duration_ms", 100.0) > 0
        and frame.get("duration_ms", 100.0) != float("inf")
    )


def _parse_clip(name: Any, data: Any) -> Optional[TileAnimClip]:
    if not isinstance(name, str) or not name or not isinstance(data, dict):
        return None
    raw_frames = data.get("frames")
    if not isinstance(raw_frames, list) or not raw_frames:
        return None
    frames = [
        TileClipFrame(
            sheet=f["sheet"],
            variant=f["variant"],
            duration_ms=float(f.get("duration_ms", 100.0)),
        )
        for f in raw_frames
        if _is_frame(f)
    ]
    if not frames:
        return None
    mode = data.get("mode", MODE_DEFAULT)
    if mode not in (MODE_DEFAULT, MODE_RANDOM_START):
        mode = MODE_DEFAULT
    return TileAnimClip(
        name=name,
        frames=tuple(frames),
        loop=data.get("loop", True) is True,
        mode=mode,
    )


@dataclass
class TileAnimFile:
    tileset: str = ""
    clips: List[TileAnimClip] = field(default_factory=list)

    def by_name(self, name: str) -> Optional[TileAnimClip]:
        for clip in self.clips:
            if clip.name == name:
                return clip
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": TANIM_VERSION,
            "tileset": self.tileset,
            "clips": {
                c.name: {
                    "loop": c.loop,
                    "mode": c.mode,
                    "frames": [f.__dict__ for f in c.frames],
                }
                for c in self.clips
            },
        }

    @staticmethod
    def from_dict(data: Any) -> "TileAnimFile":
        if not isinstance(data, dict):
            return TileAnimFile()
        tileset = data.get("tileset", "")
        raw = data.get("clips", {})
        clips: List[TileAnimClip] = []
        if isinstance(raw, dict):
            for name, entry in raw.items():
                clip = _parse_clip(name, entry)
                if clip is None:
                    continue
                clips.append(clip)
        return TileAnimFile(
            tileset=tileset if isinstance(tileset, str) else "",
            clips=clips,
        )

    @staticmethod
    def load(path: PathLike) -> "TileAnimFile":
        try:
            with open(path) as f:
                return TileAnimFile.from_dict(json.load(f))
        except (OSError, ValueError):
            return TileAnimFile()


def load_tile_anim_file(path: PathLike) -> Dict[str, TileAnimClip]:
    return {c.name: c for c in TileAnimFile.load(path).clips}


def find_tileanims(directory: PathLike) -> List[Path]:
    try:
        return sorted(Path(directory).glob(f"*{TANIM_SUFFIX}"))
    except OSError:
        return []


def _frame_index_at(clip: TileAnimClip, time_ms: float, phase: int = 0) -> int:
    n = len(clip.frames)
    total = clip.total_duration_ms()
    if n == 0:
        return 0
    if total <= 0:
        return 0
    phase = phase % n
    if not clip.loop and time_ms >= total:
        return (phase + n - 1) % n
    t = time_ms % total if clip.loop else time_ms
    acc = 0.0
    for i in range(n):
        idx = (phase + i) % n
        acc += clip.frames[idx].duration_ms
        if t < acc:
            return idx
    return (phase + n - 1) % n


def clip_frame_at(
    clip: TileAnimClip, time_ms: float, phase: int = 0
) -> Optional[TileClipFrame]:
    if not clip.frames:
        return None
    return clip.frames[_frame_index_at(clip, time_ms, phase)]


def resolve_clip_sheet(paths: Sequence[str], sheet_ref: str) -> Optional[int]:
    def norm(p: str) -> str:
        return str(PurePosixPath(p.replace("\\", "/")))

    ref = norm(sheet_ref or "")
    if not ref:
        return None
    for i, p in enumerate(paths):
        if norm(p or "") == ref:
            return i
    ref_name = PurePosixPath(ref).name
    hits = [
        i for i, p in enumerate(paths) if PurePosixPath(norm(p or "")).name == ref_name
    ]
    if len(hits) == 1:
        return hits[0]
    ref_stem = PurePosixPath(ref).stem
    hits = [
        i
        for i, p in enumerate(paths)
        if PurePosixPath(norm(p or "")).stem == ref_stem
    ]
    if len(hits) == 1:
        return hits[0]
    return None

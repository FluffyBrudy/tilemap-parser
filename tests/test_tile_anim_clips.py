import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pygame
from pygame import Surface

from tilemap_parser.parser.map_parse import (
    ParsedLayer,
    ParsedMap,
    ParsedMeta,
    ParsedTile,
    ParsedTileset,
    TilesetAnimation,
)
from tilemap_parser.parser.tileanim import (
    TileAnimClip,
    TileAnimFile,
    TileClipFrame,
    clip_frame_at,
    find_tileanims,
    load_tile_anim_file,
    resolve_clip_sheet,
)
from tilemap_parser.runtime.map_loader import TilemapData
from tilemap_parser.runtime.renderer import TileLayerRenderer

CELL = 16


def _strip(colors):
    surf = Surface((CELL * len(colors), CELL))
    for i, c in enumerate(colors):
        surf.fill(c, pygame.Rect(i * CELL, 0, CELL, CELL))
    return surf


def _tile(pos, ttype=0, variant=0, properties=None):
    return ParsedTile(
        pos=pos, ttype=ttype, variant=variant, gid=None, properties=properties
    )


def _layer(tiles, lid=0):
    layer = ParsedLayer(
        id=lid,
        name=f"L{lid}",
        layer_type="tile",
        visible=True,
        locked=False,
        opacity=1.0,
        z_index=0,
    )
    for pos, tile in tiles.items():
        layer.tiles[pos] = tile
    return layer


def _make_data(layers, tilesets, surfaces):
    meta = ParsedMeta(
        tile_size=(CELL, CELL),
        map_size=(10, 10),
        initial_map_size=(10, 10),
        zoom_level=1.0,
        scroll=(0, 0),
        version="1.1",
        render_scale=1.0,
    )
    mock_map = object.__new__(ParsedMap)
    mock_map.meta = meta
    mock_map.layers = layers
    mock_map.tilesets = tilesets
    return TilemapData(
        mock_map, surfaces, [Path(f"t{i}.png") for i in range(len(surfaces))], []
    )


def _sheet_ts(path, tile_properties=None, animation=None):
    return ParsedTileset(
        path=path,
        type="tile",
        tile_properties=tile_properties or {},
        animation=animation,
    )


def _pixel(target, x=0, y=0):
    return target.get_at((x * CELL + CELL // 2, y * CELL + CELL // 2))[:3]


def _waves(sheet="a.png"):
    return TileAnimClip(
        name="waves",
        frames=(
            TileClipFrame(sheet=sheet, variant=1, duration_ms=100.0),
            TileClipFrame(sheet=sheet, variant=2, duration_ms=200.0),
            TileClipFrame(sheet=sheet, variant=3, duration_ms=50.0),
        ),
        loop=True,
        mode="default",
    )


RED, GREEN, BLUE, YELLOW = (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)


class TestSidecarSchema:
    def test_valid_file(self, tmp_path):
        p = tmp_path / "water.tanim.json"
        p.write_text(
            '{"version": 1, "tileset": "tiles/water.png", "clips": '
            '{"waves": {"loop": true, "mode": "default", "frames": '
            '[{"sheet": "tiles/water.png", "variant": 5, "duration_ms": 120}]}}}'
        )
        clips = load_tile_anim_file(p)
        assert set(clips) == {"waves"}
        assert clips["waves"].frames[0].duration_ms == 120.0

    def test_malformed_leaves_skipped(self, tmp_path):
        p = tmp_path / "x.tanim.json"
        p.write_text(
            '{"clips": {"ok": {"frames": ['
            '{"sheet": "a.png", "variant": 1},'
            '{"sheet": "", "variant": 1},'
            '{"sheet": "a.png", "variant": -1},'
            '{"sheet": "a.png", "variant": true},'
            '{"sheet": "a.png", "variant": 2, "duration_ms": 0},'
            '{"sheet": "a.png", "variant": 3, "duration_ms": -5},'
            '"nope",'
            '{"sheet": "a.png", "variant": 4, "duration_ms": 50}]}},'
            '"empty": {"frames": []},'
            '"nodict": [1, 2]}'
        )
        clips = load_tile_anim_file(p)
        assert set(clips) == {"ok"}
        assert [f.variant for f in clips["ok"].frames] == [1, 4]

    def test_unknown_mode_defaults_loop_stays_strict(self):
        clip = TileAnimFile.from_dict(
            {"clips": {"c": {"mode": "weird", "frames": [{"sheet": "a", "variant": 0}]}}}
        ).by_name("c")
        assert clip.mode == "default"
        assert clip.loop is True
        clip2 = TileAnimFile.from_dict(
            {"clips": {"c": {"loop": 1, "frames": [{"sheet": "a", "variant": 0}]}}}
        ).by_name("c")
        assert clip2.loop is False

    def test_duplicate_names_first_wins(self, tmp_path):
        first = tmp_path / "one.tanim.json"
        first.write_text(
            '{"clips": {"c": {"frames": [{"sheet": "a", "variant": 1}]}}}'
        )
        second = tmp_path / "two.tanim.json"
        second.write_text(
            '{"clips": {"c": {"frames": [{"sheet": "a", "variant": 9}]}}}'
        )
        clips = {}
        for p in (first, second):
            for name, clip in load_tile_anim_file(p).items():
                clips.setdefault(name, clip)
        assert clips["c"].frames[0].variant == 1

    def test_missing_file_and_bad_json_yield_empty(self, tmp_path):
        assert load_tile_anim_file(tmp_path / "nope.tanim.json") == {}
        bad = tmp_path / "bad.tanim.json"
        bad.write_text("{not json")
        assert load_tile_anim_file(bad) == {}
        assert TileAnimFile.from_dict(None).clips == []

    def test_round_trip(self):
        clip = _waves()
        back = TileAnimFile.from_dict(
            TileAnimFile(tileset="a.png", clips=[clip]).to_dict()
        ).by_name("waves")
        assert back == clip

    def test_find_tileanims(self, tmp_path):
        (tmp_path / "b.tanim.json").write_text("{}")
        (tmp_path / "a.tanim.json").write_text("{}")
        (tmp_path / "note.txt").write_text("x")
        found = find_tileanims(tmp_path)
        assert [p.name for p in found] == ["a.tanim.json", "b.tanim.json"]
        assert find_tileanims(tmp_path / "missing") == []


class TestClipFrameAt:
    def test_uneven_durations(self):
        clip = _waves()
        assert clip_frame_at(clip, 0).variant == 1
        assert clip_frame_at(clip, 99.9).variant == 1
        assert clip_frame_at(clip, 100).variant == 2
        assert clip_frame_at(clip, 299.9).variant == 2
        assert clip_frame_at(clip, 300).variant == 3
        assert clip_frame_at(clip, 349.9).variant == 3
        assert clip_frame_at(clip, 350).variant == 1
        assert clip_frame_at(clip, -1).variant == 3

    def test_phase_rotates_order(self):
        clip = _waves()
        assert clip_frame_at(clip, 0, phase=1).variant == 2
        assert clip_frame_at(clip, 199.9, phase=1).variant == 2
        assert clip_frame_at(clip, 200, phase=1).variant == 3
        assert clip_frame_at(clip, 250, phase=1).variant == 1
        assert clip_frame_at(clip, 0, phase=7).variant == 2

    def test_non_loop_holds_last(self):
        clip = TileAnimClip(
            name="x",
            frames=(
                TileClipFrame(sheet="a", variant=1, duration_ms=100.0),
                TileClipFrame(sheet="a", variant=2, duration_ms=100.0),
            ),
            loop=False,
        )
        assert clip_frame_at(clip, 0).variant == 1
        assert clip_frame_at(clip, 199.9).variant == 2
        assert clip_frame_at(clip, 200).variant == 2
        assert clip_frame_at(clip, 9999).variant == 2

    def test_non_loop_holds_phase_rotated_last(self):
        clip = TileAnimClip(
            name="x",
            frames=(
                TileClipFrame(sheet="a", variant=1, duration_ms=100.0),
                TileClipFrame(sheet="a", variant=2, duration_ms=100.0),
                TileClipFrame(sheet="a", variant=3, duration_ms=100.0),
            ),
            loop=False,
        )
        assert clip_frame_at(clip, 0, phase=1).variant == 2
        assert clip_frame_at(clip, 300, phase=1).variant == 1
        assert clip_frame_at(clip, 9999, phase=1).variant == 1

    def test_empty_and_zero_total(self):
        assert clip_frame_at(TileAnimClip(name="e", frames=()), 0) is None
        zero = TileAnimClip(
            name="z",
            frames=(TileClipFrame(sheet="a", variant=4, duration_ms=0.0),),
        )
        assert clip_frame_at(zero, 500).variant == 4


class TestResolveSheet:
    PATHS = ["assets/tiles/water.png", "assets/tiles/grass.png"]

    def test_exact_and_slashes(self):
        assert resolve_clip_sheet(self.PATHS, "assets/tiles/water.png") == 0
        assert resolve_clip_sheet(self.PATHS, "assets\\tiles\\grass.png") == 1

    def test_basename_and_stem_fallback(self):
        assert resolve_clip_sheet(self.PATHS, "other/water.png") == 0
        assert resolve_clip_sheet(self.PATHS, "water") == 0

    def test_ambiguous_and_missing_yield_none(self):
        dup = ["x/water.png", "y/water.png"]
        assert resolve_clip_sheet(dup, "water.png") is None
        assert resolve_clip_sheet(self.PATHS, "lava.png") is None
        assert resolve_clip_sheet(self.PATHS, "") is None


class TestRendererClips:
    def _clip_data(self, props=None, tilesets=None, surfaces=None):
        layer = _layer({(0, 0): _tile((0, 0), properties=props)})
        ts = tilesets or [_sheet_ts("a.png")]
        surfs = surfaces or [_strip([RED, GREEN, BLUE, YELLOW])]
        return _make_data([layer], ts, surfs)

    def test_clip_plays_uneven_frames(self):
        data = self._clip_data(props={"anim_clip": "waves"})
        r = TileLayerRenderer(data, tile_clips={"waves": _waves()})
        target = Surface((32, 32))
        r.render(target, (0, 0), current_time_ms=50)
        assert _pixel(target) == GREEN
        r.render(target, (0, 0), current_time_ms=150)
        assert _pixel(target) == BLUE
        r.render(target, (0, 0), current_time_ms=320)
        assert _pixel(target) == YELLOW

    def test_unflagged_tile_static(self):
        data = self._clip_data()
        r = TileLayerRenderer(data, tile_clips={"waves": _waves()})
        target = Surface((32, 32))
        r.render(target, (0, 0), current_time_ms=150)
        assert _pixel(target) == RED

    def test_unknown_clip_static_with_warning(self):
        data = self._clip_data(props={"anim_clip": "nope"})
        r = TileLayerRenderer(data, tile_clips={"waves": _waves()})
        assert any("nope" in w for w in r.warnings)
        target = Surface((32, 32))
        r.render(target, (0, 0), current_time_ms=150)
        assert _pixel(target) == RED

    def test_unresolvable_sheet_degrades_to_base(self):
        clip = TileAnimClip(
            name="w",
            frames=(TileClipFrame(sheet="void.png", variant=2, duration_ms=100.0),),
        )
        data = self._clip_data(props={"anim_clip": "w"})
        r = TileLayerRenderer(data, tile_clips={"w": clip})
        assert r.warnings
        target = Surface((32, 32))
        r.render(target, (0, 0), current_time_ms=50)
        assert _pixel(target) == RED

    def test_out_of_range_frame_degrades_to_base(self):
        clip = TileAnimClip(
            name="w",
            frames=(
                TileClipFrame(sheet="a.png", variant=1, duration_ms=100.0),
                TileClipFrame(sheet="a.png", variant=99, duration_ms=100.0),
            ),
        )
        data = self._clip_data(props={"anim_clip": "w"})
        r = TileLayerRenderer(data, tile_clips={"w": clip})
        target = Surface((32, 32))
        r.render(target, (0, 0), current_time_ms=50)
        assert _pixel(target) == GREEN
        r.render(target, (0, 0), current_time_ms=150)
        assert _pixel(target) == RED

    def test_sidecar_path_form(self, tmp_path):
        p = tmp_path / "w.tanim.json"
        p.write_text(
            '{"clips": {"waves": {"frames": ['
            '{"sheet": "a.png", "variant": 1, "duration_ms": 100},'
            '{"sheet": "a.png", "variant": 2, "duration_ms": 100}]}}}'
        )
        data = self._clip_data(props={"anim_clip": "waves"})
        r = TileLayerRenderer(data, tile_clips=p)
        target = Surface((32, 32))
        r.render(target, (0, 0), current_time_ms=150)
        assert _pixel(target) == BLUE

    def test_missing_sidecar_renders_legacy_with_warning(self, tmp_path):
        data = self._clip_data(props={"anim_clip": "waves"})
        r = TileLayerRenderer(data, tile_clips=tmp_path / "gone.tanim.json")
        assert r.warnings
        target = Surface((32, 32))
        r.render(target, (0, 0), current_time_ms=150)
        assert _pixel(target) == RED

    def test_duplicate_names_first_wins(self, tmp_path):
        p1 = tmp_path / "one.tanim.json"
        p1.write_text(
            '{"clips": {"w": {"frames": [{"sheet": "a.png", "variant": 1}]}}}'
        )
        p2 = tmp_path / "two.tanim.json"
        p2.write_text(
            '{"clips": {"w": {"frames": [{"sheet": "a.png", "variant": 2}]}}}'
        )
        data = self._clip_data(props={"anim_clip": "w"})
        r = TileLayerRenderer(data, tile_clips=[p1, p2])
        assert any("duplicate" in w for w in r.warnings)
        target = Surface((32, 32))
        r.render(target, (0, 0), current_time_ms=10)
        assert _pixel(target) == GREEN

    def test_multi_sheet_clip(self):
        layer = _layer({(0, 0): _tile((0, 0), properties={"anim_clip": "w"})})
        data = _make_data(
            [layer],
            [_sheet_ts("a.png"), _sheet_ts("b.png")],
            [_strip([RED, GREEN]), _strip([BLUE, YELLOW])],
        )
        clip = TileAnimClip(
            name="w",
            frames=(
                TileClipFrame(sheet="a.png", variant=1, duration_ms=100.0),
                TileClipFrame(sheet="b.png", variant=0, duration_ms=100.0),
            ),
        )
        r = TileLayerRenderer(data, tile_clips={"w": clip})
        target = Surface((32, 32))
        r.render(target, (0, 0), current_time_ms=50)
        assert _pixel(target) == GREEN
        r.render(target, (0, 0), current_time_ms=150)
        assert _pixel(target) == BLUE

    def test_clip_beats_stride(self):
        anim = TilesetAnimation(
            frame_count=2, frame_duration_ms=100.0, frame_stride=1
        )
        data = self._clip_data(
            props={"anim_clip": "waves"},
            tilesets=[_sheet_ts("a.png", animation=anim)],
        )
        r = TileLayerRenderer(data, tile_clips={"waves": _waves()})
        target = Surface((32, 32))
        r.render(target, (0, 0), current_time_ms=150)
        assert _pixel(target) == BLUE

    def test_stride_untouched_without_clips(self):
        anim = TilesetAnimation(
            frame_count=2, frame_duration_ms=100.0, frame_stride=1
        )
        data = self._clip_data(tilesets=[_sheet_ts("a.png", animation=anim)])
        r = TileLayerRenderer(data)
        target = Surface((32, 32))
        r.render(target, (0, 0), current_time_ms=50)
        assert _pixel(target) == RED
        r.render(target, (0, 0), current_time_ms=150)
        assert _pixel(target) == GREEN

    def test_load_optional_anim_flag(self):
        anim = TilesetAnimation(
            frame_count=2, frame_duration_ms=100.0, frame_stride=1
        )
        layer = _layer(
            {
                (0, 0): _tile((0, 0), properties={"anim": True}),
                (1, 0): _tile((1, 0)),
            }
        )
        data = _make_data([layer], [_sheet_ts("a.png", animation=anim)],
                          [_strip([RED, GREEN])])
        r = TileLayerRenderer(data, load_optional_anim="anim")
        target = Surface((64, 32))
        r.render(target, (0, 0), current_time_ms=150)
        assert _pixel(target, 0, 0) == GREEN
        assert _pixel(target, 1, 0) == RED

    def test_warm_cache_freezes_clip_frames(self):
        data = self._clip_data(props={"anim_clip": "waves"})
        r = TileLayerRenderer(data, tile_clips={"waves": _waves()})
        r.warm_cache()
        target = Surface((32, 32))
        r.render(target, (0, 0), current_time_ms=320)
        assert _pixel(target) == YELLOW

    def test_random_start_desyncs_cells(self):
        clip = TileAnimClip(
            name="w",
            frames=(
                TileClipFrame(sheet="a.png", variant=0, duration_ms=100.0),
                TileClipFrame(sheet="a.png", variant=1, duration_ms=100.0),
            ),
            mode="random_start_times",
        )
        layer = _layer(
            {
                (0, 0): _tile((0, 0), properties={"anim_clip": "w"}),
                (5, 0): _tile((5, 0), properties={"anim_clip": "w"}),
            }
        )
        data = _make_data([layer], [_sheet_ts("a.png")],
                          [_strip([RED, GREEN])])
        r = TileLayerRenderer(data, tile_clips={"w": clip})
        target = Surface((128, 32))
        r.render(target, (0, 0), current_time_ms=50)
        assert _pixel(target, 0, 0) != _pixel(target, 5, 0)

    def test_non_loop_holds_last_frame(self):
        clip = TileAnimClip(
            name="w",
            frames=(
                TileClipFrame(sheet="a.png", variant=1, duration_ms=100.0),
                TileClipFrame(sheet="a.png", variant=2, duration_ms=100.0),
            ),
            loop=False,
        )
        data = self._clip_data(props={"anim_clip": "w"})
        r = TileLayerRenderer(data, tile_clips={"w": clip})
        target = Surface((32, 32))
        r.render(target, (0, 0), current_time_ms=99999)
        assert _pixel(target) == BLUE

    def test_tileset_and_placement_props_merge(self):
        layer = _layer({(0, 0): _tile((0, 0), properties={"anim_clip": "w2"})})
        data = _make_data(
            [layer],
            [_sheet_ts("a.png", tile_properties={"0": {"anim_clip": "w1"}})],
            [_strip([RED, GREEN, BLUE])],
        )
        w1 = TileAnimClip(
            name="w1",
            frames=(TileClipFrame(sheet="a.png", variant=1, duration_ms=100.0),),
        )
        w2 = TileAnimClip(
            name="w2",
            frames=(TileClipFrame(sheet="a.png", variant=2, duration_ms=100.0),),
        )
        assert data.get_tile_properties(0, 0, {"anim_clip": "w2"})["anim_clip"] == "w2"
        assert data.get_tile_properties(0, 0, None)["anim_clip"] == "w1"
        r = TileLayerRenderer(data, tile_clips={"w1": w1, "w2": w2})
        target = Surface((32, 32))
        r.render(target, (0, 0), current_time_ms=10)
        assert _pixel(target) == BLUE


class TestRendererClipFlips:
    def _quadrants(self):
        surf = Surface((CELL, CELL))
        surf.fill(RED, pygame.Rect(0, 0, CELL // 2, CELL // 2))
        surf.fill(GREEN, pygame.Rect(CELL // 2, 0, CELL // 2, CELL // 2))
        surf.fill(BLUE, pygame.Rect(0, CELL // 2, CELL // 2, CELL // 2))
        surf.fill(YELLOW, pygame.Rect(CELL // 2, CELL // 2, CELL // 2, CELL // 2))
        return surf

    def _clip_data(self, **flips):
        tile = ParsedTile(pos=(0, 0), ttype=0, variant=0, gid=None,
                          properties={"anim_clip": "w"}, **flips)
        return _make_data([_layer({(0, 0): tile})], [_sheet_ts("a.png")], [self._quadrants()])

    def _clip(self):
        return TileAnimClip(
            name="w",
            frames=(TileClipFrame(sheet="a.png", variant=0, duration_ms=100.0),),
        )

    def _quads(self, target):
        return (
            target.get_at((4, 4))[:3],
            target.get_at((12, 4))[:3],
            target.get_at((4, 12))[:3],
            target.get_at((12, 12))[:3],
        )

    def _render(self, r, **kw):
        target = Surface((32, 32))
        r.render(target, (0, 0), current_time_ms=10, **kw)
        return self._quads(target)

    def test_unflipped_clip(self):
        r = TileLayerRenderer(self._clip_data(), tile_clips={"w": self._clip()})
        assert self._render(r) == (RED, GREEN, BLUE, YELLOW)

    def test_flipped_h_clip(self):
        r = TileLayerRenderer(self._clip_data(flip_h=True), tile_clips={"w": self._clip()})
        assert self._render(r) == (GREEN, RED, YELLOW, BLUE)

    def test_flipped_v_clip(self):
        r = TileLayerRenderer(self._clip_data(flip_v=True), tile_clips={"w": self._clip()})
        assert self._render(r) == (BLUE, YELLOW, RED, GREEN)

    def test_flipped_d_clip(self):
        r = TileLayerRenderer(self._clip_data(flip_d=True), tile_clips={"w": self._clip()})
        assert self._render(r) == (RED, BLUE, GREEN, YELLOW)

    def test_warmed_flipped_clip_needs_no_data(self):
        r = TileLayerRenderer(self._clip_data(flip_h=True), tile_clips={"w": self._clip()})
        r.warm_cache()
        assert r.data is None
        assert self._render(r) == (GREEN, RED, YELLOW, BLUE)

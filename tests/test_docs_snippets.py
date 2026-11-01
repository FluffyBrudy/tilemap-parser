"""Executable documentation: cookbook snippets.

Every snippet in webdocs/src/snippets/cookbook.json runs against a
generated fixture map in a temporary working directory, so the documented
access patterns fail CI as soon as the API they show changes.

Fixture layout, shared by all snippets (cwd is the tmp dir):
    data/map.json                          tile layer + object layer
    data/collision/ground.collision.json   polygons + custom tile properties
    assets/tileset.png                     32x16 sheet, two 16x16 cells
"""

import json
import sys
from pathlib import Path

import pygame
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser import load_map  # noqa: E402

ROOT = Path(__file__).parent.parent
SNIPPETS = json.loads(
    (ROOT / "webdocs" / "src" / "snippets" / "cookbook.json").read_text()
)

MAP_PAYLOAD = {
    "meta": {
        "tile_size": "16;16",
        "map_size": "4;4",
        "initial_map_size": "4;4",
        "render_scale": 1,
        "scroll": "0;0",
        "version": "1.1",
    },
    "resources": {"tilesets": [{"path": "../assets/tileset.png", "type": "object"}]},
    "project_state": {"rules": [], "groups": []},
    "data": {
        "layers": [
            {
                "name": "Terrain",
                "type": "tile",
                "visible": True,
                "locked": False,
                "opacity": 1.0,
                "z_index": 0,
                "tiles": {
                    "0;0": {
                        "pos": "0;0",
                        "ttype": 0,
                        "variant": 1,
                        "properties": {"surface": "stone"},
                    },
                    "1;0": {
                        "pos": "1;0",
                        "ttype": 0,
                        "variant": 0,
                        "properties": {"surface": "ice"},
                    },
                },
            },
            {
                "name": "Objects",
                "type": "object",
                "visible": True,
                "locked": False,
                "opacity": 1.0,
                "z_index": 1,
                "tiles": {},
                "objects": {
                    "5": {
                        "area": {"x": 64, "y": 96, "w": 16, "h": 16},
                        "ttype": 0,
                        "tileset_type": "object",
                        "variant": 1,
                        "properties": {},
                    },
                    "7": {
                        "area": {"x": 8, "y": 24, "w": 16, "h": 16},
                        "ttype": 0,
                        "tileset_type": "object",
                        "variant": 0,
                        "properties": {"pickup": "coin"},
                    },
                },
            },
        ]
    },
}

COLLISION_PAYLOAD = {
    "tileset_name": "ground",
    "tile_size": [16, 16],
    "tiles": {
        "0": {
            "shapes": [
                {
                    "vertices": [[0, 0], [16, 0], [16, 16], [0, 16]],
                    "one_way": False,
                }
            ],
            "properties": {"surface": "gear"},
        }
    },
}


def _write_fixture(tmp_path: Path) -> None:
    data = tmp_path / "data"
    (data / "collision").mkdir(parents=True)
    (tmp_path / "assets").mkdir()

    sheet = pygame.Surface((32, 16), pygame.SRCALPHA)
    pygame.draw.rect(sheet, (255, 64, 64), (0, 0, 16, 16))
    pygame.draw.rect(sheet, (64, 160, 255), (16, 0, 16, 16))
    pygame.image.save(sheet, str(tmp_path / "assets" / "tileset.png"))

    with open(data / "map.json", "w") as f:
        json.dump(MAP_PAYLOAD, f, indent=2)
    with open(data / "collision" / "ground.collision.json", "w") as f:
        json.dump(COLLISION_PAYLOAD, f, indent=2)


def test_fixture_loads_map_with_expected_ids(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_fixture(tmp_path)
    data = load_map("data/map.json")
    layer = data.get_layer("Objects")
    assert layer is not None
    assert set(layer.objects) == {5, 7}
    assert layer.objects[7].properties == {"pickup": "coin"}
    assert data.get_tile_at("Terrain", 1, 0).properties == {"surface": "ice"}


@pytest.mark.parametrize(
    "snippet", SNIPPETS, ids=[s["id"] for s in SNIPPETS]
)
def test_cookbook_snippet_runs(snippet, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_fixture(tmp_path)
    namespace: dict = {"__name__": f"cookbook.{snippet['id']}"}
    exec(compile(snippet["code"], f"<cookbook:{snippet['id']}>", "exec"), namespace)


def test_snippets_reference_stable_fixture_positions():
    # Keeps the snippet asserts and the fixture payload from drifting apart.
    for snippet in SNIPPETS:
        if "layer.objects[7]" in snippet["code"]:
            obj_area = MAP_PAYLOAD["data"]["layers"][1]["objects"]["7"]["area"]
            assert "(8, 24, 16, 16)" in snippet["code"]
            assert obj_area == {"x": 8, "y": 24, "w": 16, "h": 16}

"""Build the static site (public/index.html) and print-ready STLs (public/downloads/) from the Yosh Studios STLs.

    pip install -r requirements.txt
    python tools/build.py

Modifications applied to the Yosh model:
  * gold frame  -> ONE solid part: closed floor + wall layer with holes for the gems (2 x 1/4 of the original 4.25 mm)
  * gems + disc -> thinned to 1.0 mm and re-seated on the floor
  * ring        -> unchanged, recentered so its top plate sits at z = 0 under the frame
"""
import base64, json
from pathlib import Path
import numpy as np, trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
SRC, PUB, DL = ROOT / "models" / "source", ROOT / "public", ROOT / "public" / "downloads"
DL.mkdir(parents=True, exist_ok=True)
CLEAR, GEM_T = 0.15, 1.0            # hole clearance around gems, gem thickness (mm)
load = lambda n: trimesh.load(SRC / n, force="mesh")
frame_src, gems, ring = load("ring_frame.stl"), load("gems.stl"), load("ring.stl")
for m in (frame_src, gems, ring): m.apply_translation([-128.0, -128.0, 0])   # Yosh plate offset -> centre on origin
LAYER = float(frame_src.bounds[1][2]) / 4


def polys_at(m, z):
    p2, T = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1]).to_2D()
    out = []
    for pg in p2.polygons_full:
        def tr(c):
            a = np.array(c); h = np.column_stack([a, np.zeros(len(a)), np.ones(len(a))]); return (T @ h.T).T[:, :2]
        out.append(Polygon(tr(pg.exterior.coords), [tr(i.coords) for i in pg.interiors]))
    return unary_union([p.buffer(0) for p in out])


def extrude(poly, h, z0):
    ps = [poly] if poly.geom_type == "Polygon" else list(poly.geoms)
    m = trimesh.util.concatenate([trimesh.creation.extrude_polygon(p, h) for p in ps])
    m.apply_translation([0, 0, z0]); m.merge_vertices(); trimesh.repair.fix_normals(m); return m


# ---------- frame: closed floor + wall layer with holes shaped like the gems
sil = unary_union([polys_at(frame_src, z) for z in (1.5, 3.0, 4.0)]).buffer(0).simplify(0.02)
gem_out = unary_union([polys_at(gems, z) for z in (0.5, 1.0, 1.5)]).buffer(0).buffer(CLEAR)
holes = [gem_out] if gem_out.geom_type == "Polygon" else list(gem_out.geoms)
floor_part = extrude(sil, LAYER, 0.0)
walls = trimesh.boolean.difference([extrude(sil, LAYER, LAYER)] + [extrude(h.simplify(0.02), LAYER + 2, LAYER - 1) for h in holes], engine="manifold")
frame = trimesh.boolean.union([floor_part, walls], engine="manifold"); frame.merge_vertices()
print("frame: watertight", frame.is_watertight, "extents", frame.extents.round(2), "holes", len(holes))

# ---------- gems: thin to 1 mm, rest on the floor
gem = gems.copy(); gem.apply_scale([1, 1, GEM_T / gem.extents[2]]); gem.apply_translation([0, 0, LAYER - gem.bounds[0][2]])
print("gems: watertight", gem.is_watertight, "extents", gem.extents.round(2))

# ---------- ring: top plate at z = 0
ring.apply_translation([0, 0, -ring.bounds[1][2]])

frame.export(DL / "gold_frame_single.stl"); gem.export(DL / "gems_disk_1mm.stl"); ring.export(DL / "ring_assembled_pose.stl")

# ---------- html (decimated copies for the browser)
dec = lambda m, n: m.simplify_quadric_decimation(face_count=n) if len(m.faces) > n else m
parts = [("Khung vàng (1 khung: đáy đặc + lỗ cho đá)", "gf", frame, "#f2bd3c", 0.55, 0.35, "gold", 0.2),
         ("Đá + đĩa (gems)", "gem", dec(gem, 100000), "#06a857", 0.15, 0.18, "gem", 1.0),
         ("Thân nhẫn (ring)", "ring", dec(ring, 50000), "#5d6663", 0.0, 0.85, "ring", -1.0)]
out = []
for name, kind, m, color, metal, rough, group, up in parts:
    m = m.copy(); m.merge_vertices()
    out.append(dict(name=name, kind=kind, color=color, metal=metal, rough=rough, group=group, up=[0, 0, up],
                    v=base64.b64encode(m.vertices.astype("<f4").tobytes()).decode(), i=base64.b64encode(m.faces.astype("<u4").tobytes()).decode()))
html = (ROOT / "tools" / "template.html").read_text(encoding="utf-8")
for k, v in {"__NX__": "22.59", "__NY__": "21.18", "__NT__": f"{2 * LAYER:.2f}", "__NG__": "1", "__NC__": "55", "__NH__": "17.5",
             "__FLOORZ__": f"{ring.bounds[0][2] - 0.05:.2f}", "__FF__": "0.5", "__TL__": "Độ dày khung (tổng)",
             "__SUB__": "Nhẫn Lanterns (HBO) · STL của Yosh Studios, đã chỉnh", "__TAG__": "Bản gốc: Yosh Studios (Patreon)"}.items():
    html = html.replace(k, v)
(PUB / "index.html").write_text(html.replace("__DATA__", json.dumps(dict(parts=out), ensure_ascii=False)), encoding="utf-8")
print("wrote public/index.html", round((PUB / "index.html").stat().st_size / 1e6, 2), "MB")

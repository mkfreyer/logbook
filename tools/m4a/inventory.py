#!/usr/bin/env python3
"""Reproducible structural inventory of the official BodyParts3D OBJ archive.

Python standard library only. Never assesses anatomical accuracy from metrics.
Refuses incomplete archives, verifies every member's CRC before opening OBJ data,
and extracts requested element IDs only into fixed safe filenames.
"""
import argparse
import collections
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import time
import zipfile

EXPECTED_SIZE = 142903898
EXPECTED_SHA256 = '40665852c49f218326590e204db91064a1ecfc3c6f8cbd7bbbcaac62c7cd409e'
ELEMENT = re.compile(r"^FJ\d+M?$")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tables(paths):
    assignments = collections.defaultdict(list)
    table_meta = []
    for path in sorted(set(paths)):
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream, delimiter="\t"))
        table_meta.append({"path": str(path), "sha256": sha256(path), "rows": len(rows)})
        for row in rows:
            element = row.get("element file id", "")
            if element:
                assignments[element].append({
                    "concept_id": row.get("concept id"),
                    "name": row.get("name"),
                    "table": path.name,
                })
    return assignments, table_meta


def inventory_obj(data):
    vertices, normals, textures, faces, comments, objects = [], [], [], [], [], []
    issues = collections.Counter()
    for line_number, raw in enumerate(data.decode("utf-8-sig", errors="replace").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            if len(comments) < 12:
                comments.append(line[1:].strip()[:500])
            continue
        bits = line.split()
        kind = bits[0]
        if kind in ("v", "vn", "vt"):
            target = {"v": vertices, "vn": normals, "vt": textures}[kind]
            try:
                values = tuple(float(value) for value in bits[1:])
                minimum = 1 if kind == "vt" else 3
                if len(values) < minimum:
                    raise ValueError("too few coordinates")
                if not all(math.isfinite(value) for value in values):
                    issues[f"nonfinite_{kind}"] += 1
                target.append(values[:3])
            except ValueError:
                issues[f"malformed_{kind}"] += 1
                target.append((math.nan, math.nan, math.nan))
        elif kind == "f":
            # Negative indices are relative to counts at the face's position.
            face = []
            try:
                for corner in bits[1:]:
                    components = corner.split("/")
                    if len(components) > 3 or not components[0]:
                        raise ValueError("invalid corner")
                    indices = []
                    for index, count in zip(components, (len(vertices), len(textures), len(normals))):
                        if not index:
                            indices.append(None)
                            continue
                        number = int(index)
                        if number == 0:
                            raise ValueError("OBJ indices are nonzero")
                        indices.append(number - 1 if number > 0 else count + number)
                    face.append(indices)
                if len(face) < 3:
                    raise ValueError("face has fewer than three corners")
                faces.append(face)
            except ValueError:
                issues["malformed_faces"] += 1
        elif kind in ("o", "g"):
            objects.append({"type": kind, "name": " ".join(bits[1:])[:500]})

    finite_vertices = [vertex for vertex in vertices if all(math.isfinite(value) for value in vertex)]
    minimum = [min(vertex[axis] for vertex in finite_vertices) for axis in range(3)] if finite_vertices else None
    maximum = [max(vertex[axis] for vertex in finite_vertices) for axis in range(3)] if finite_vertices else None
    edges = collections.Counter()
    edge_winding = collections.Counter()
    used_vertices = set()
    triangle_count = 0
    degenerate_triangles = 0
    surface_area = 0.0
    valid_faces = 0
    polygon_sizes = collections.Counter()
    for face in faces:
        invalid = False
        for corner in face:
            for index, size in zip(corner, (len(vertices), len(textures), len(normals))):
                if index is not None and not 0 <= index < size:
                    invalid = True
            vertex_index = corner[0]
            if 0 <= vertex_index < len(vertices) and not all(math.isfinite(value) for value in vertices[vertex_index]):
                invalid = True
        if invalid:
            issues["faces_invalid_index_or_nonfinite_vertex"] += 1
            continue
        indices = [corner[0] for corner in face]
        valid_faces += 1
        polygon_sizes[str(len(indices))] += 1
        used_vertices.update(indices)
        for start, end in zip(indices, indices[1:] + indices[:1]):
            edge = (min(start, end), max(start, end))
            edges[edge] += 1
            edge_winding[edge] += 1 if start < end else -1
        for offset in range(1, len(indices) - 1):
            triangle_count += 1
            a, b, c = (vertices[indices[index]] for index in (0, offset, offset + 1))
            ab = [b[axis] - a[axis] for axis in range(3)]
            ac = [c[axis] - a[axis] for axis in range(3)]
            cross = (ab[1]*ac[2] - ab[2]*ac[1], ab[2]*ac[0] - ab[0]*ac[2], ab[0]*ac[1] - ab[1]*ac[0])
            area2_squared = sum(value*value for value in cross)
            if area2_squared <= 1e-24:
                degenerate_triangles += 1
            surface_area += math.sqrt(area2_squared) / 2.0

    return {
        "vertices": len(vertices), "normals": len(normals), "texture_coordinates": len(textures),
        "faces": len(faces) + issues["malformed_faces"], "valid_faces": valid_faces,
        "triangles_if_fan_triangulated": triangle_count, "polygon_sizes": dict(polygon_sizes),
        "bounds": {"min": minimum, "max": maximum,
                   "size": [maximum[axis]-minimum[axis] for axis in range(3)] if minimum else None},
        "structural_issues": dict(issues), "degenerate_triangles": degenerate_triangles,
        "degeneracy_threshold_cross_product_squared": 1e-24,
        "unused_vertices": len(vertices)-len(used_vertices),
        "boundary_edges": sum(count == 1 for count in edges.values()),
        "nonmanifold_edges": sum(count > 2 for count in edges.values()),
        "inconsistent_winding_edges": sum(edges[edge] == 2 and abs(winding) == 2 for edge, winding in edge_winding.items()),
        "surface_area_in_coordinate_units_squared": surface_area,
        "obj_comments": comments, "objects_and_groups": objects,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--expected-bytes", type=int, default=EXPECTED_SIZE)
    parser.add_argument("--expected-sha256", default=EXPECTED_SHA256)
    parser.add_argument("--tables-dir", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--extract-dir", type=Path)
    parser.add_argument("--element", action="append", default=[])
    parser.add_argument("--elements-file", type=Path, help="JSON list or object with element_ids list")
    parser.add_argument("--selected-only", action="store_true", help="Inventory only requested extraction IDs")
    parser.add_argument("--extract-only", action="store_true", help="Verify, extract, and record metadata without mesh statistics")
    args = parser.parse_args()
    started = time.monotonic()
    size = args.archive.stat().st_size
    if size != args.expected_bytes:
        parser.error(f"archive size {size} differs from required {args.expected_bytes}; refusing to open archive")
    archive_sha256 = sha256(args.archive)
    if archive_sha256 != args.expected_sha256:
        parser.error(f"archive SHA-256 {archive_sha256} differs from required {args.expected_sha256}; refusing to open archive")
    wanted = set(args.element)
    if args.elements_file:
        selection = json.loads(args.elements_file.read_text())
        wanted.update(selection if isinstance(selection, list) else selection["element_ids"])
    if any(not ELEMENT.fullmatch(element) for element in wanted):
        parser.error("all element IDs must be FJ digits with optional M suffix")
    if (args.selected_only or args.extract_only) and not wanted:
        parser.error("selected-only/extract-only requires element IDs")
    assignments, table_meta = read_tables([path for folder in args.tables_dir for path in folder.glob("*.txt")])
    result = {"schema_version": 1, "source": {
        "archive": str(args.archive), "bytes": size, "sha256": archive_sha256,
        "official_url": "https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/isa_BP3D_4.0_obj_99.zip",
    }, "tables": table_meta, "method": {
        "anatomical_accuracy": "Not assessed by this structural inventory. Table membership can include broad parent concepts, not just direct anatomical names.",
        "triangles": "Fan triangulation count; archive source geometry is preserved.",
        "coordinates": "Raw source OBJ coordinates. Anatomical directions and units require source documentation and visual verification.",
        "topology": "Undirected polygon edges; boundary/nonmanifold counts describe structure and do not establish anatomical validity.",
    }, "elements": []}
    with zipfile.ZipFile(args.archive) as archive:
        bad = archive.testzip()
        if bad:
            raise SystemExit(f"ZIP CRC verification failed for {bad}; no extraction or OBJ inventory performed")
        result["source"]["all_member_crc32_verified"] = True
        members = {}
        for info in archive.infolist():
            if info.is_dir() or not info.filename.lower().endswith(".obj"):
                continue
            element = Path(info.filename).stem
            if not ELEMENT.fullmatch(element):
                raise SystemExit(f"Unexpected OBJ element name: {info.filename!r}")
            if element in members:
                raise SystemExit(f"Duplicate element ID: {element}")
            members[element] = info
        missing = wanted - members.keys()
        if missing:
            raise SystemExit(f"Requested element IDs absent from archive: {sorted(missing)}")
        result["source"]["obj_members"] = len(members)
        result["source"]["uncompressed_obj_bytes"] = sum(info.file_size for info in members.values())
        if args.extract_dir:
            args.extract_dir.mkdir(parents=True, exist_ok=True)
        selected = wanted if args.selected_only or args.extract_only else members.keys()
        for position, element in enumerate(sorted(selected), 1):
            info = members[element]
            data = archive.read(info)
            record = {"element_id": element, "archive_member": info.filename,
                      "bytes": info.file_size, "zip_crc32": f"{info.CRC:08x}",
                      "sha256": hashlib.sha256(data).hexdigest(),
                      "table_assignments": assignments.get(element, [])}
            if element in wanted and args.extract_dir:
                target = args.extract_dir / f"{element}.obj"
                if target.is_symlink():
                    raise SystemExit(f"Refusing symlink extraction target: {target}")
                target.write_bytes(data)
                record["extracted_path"] = str(target)
            if not args.extract_only:
                record.update(inventory_obj(data))
            result["elements"].append(record)
            if position % 100 == 0:
                print(f"Inventoried {position}/{len(selected)} OBJ files", flush=True)
    if not args.extract_only:
        records = result["elements"]
        bounds = [record["bounds"] for record in records if record["bounds"]["min"] is not None]
        result["summary"] = {
            "inventoried_elements": len(records),
            **{key: sum(record[key] for record in records) for key in (
                "vertices", "faces", "valid_faces", "triangles_if_fan_triangulated",
                "degenerate_triangles", "boundary_edges", "nonmanifold_edges", "inconsistent_winding_edges")},
            "elements_with_structural_issues": [record["element_id"] for record in records if any(record["structural_issues"].values())],
            "bounds": {
                "min": [min(bound["min"][axis] for bound in bounds) for axis in range(3)],
                "max": [max(bound["max"][axis] for bound in bounds) for axis in range(3)],
            } if bounds else None,
        }
    result["elapsed_seconds"] = round(time.monotonic()-started, 3)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(f"Wrote {args.output} in {result['elapsed_seconds']}s", flush=True)


if __name__ == "__main__":
    main()

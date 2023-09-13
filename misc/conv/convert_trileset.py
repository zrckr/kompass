import click
import logging
import mako.template

from common import Geometry, Vector2, Vector3, read_geometry_from_xml, read_xml_file, generate_scene_unique_id
from dataclasses import dataclass, field, astuple
from gltf_builder import GltfBuilder
from pathlib import Path
from typing import Any


@dataclass
class Trile(Geometry):
    id: int = 0
    atlas: Vector2 = field(default_factory=Vector2)
    size: Vector3 = field(default_factory=Vector3)
    faces: dict[str, str] = field(default_factory=dict)
    actor: dict[str, str] = field(default_factory=dict)
    surface: str = ''
    immaterial: bool = False
    rid: str = ''


@dataclass
class TrileSet:
    name: str = ''
    triles: list[Trile] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


def parse_trile_from_xml(xml: dict) -> TrileSet:
    trileset = TrileSet(getattr(xml.TrileSet, '@name'))

    if type(xml.TrileSet.Triles.TrileEntry) is not list:
        xml.TrileSet.Triles.TrileEntry = [xml.TrileSet.Triles.TrileEntry]
    
    for index, entry in enumerate(xml.TrileSet.Triles.TrileEntry):
        trile = Trile()
        trile.id = int(getattr(entry, '@key'))
        trile.name = getattr(entry.Trile, '@name')
        trile.surface = getattr(entry.Trile, '@surfaceType')
        trile.immaterial = eval(getattr(entry.Trile, '@immaterial'))
        trile.actor = {
            getattr(entry.Trile.ActorSettings, '@type'):
            getattr(entry.Trile.ActorSettings, '@face')
        }

        trile.atlas = Vector2.parse(entry.Trile.AtlasOffset.Vector2)
        trile.size = Vector3.parse(entry.Trile.Size.Vector3)

        primitives = entry.Trile.Geometry.ShaderInstancedIndexedPrimitives
        has_geometry = read_geometry_from_xml(trile, primitives)
        
        for face in entry.Trile.Faces.Face:
            key = getattr(face, '@key')
            trile.faces[key] = face.CollisionType

        trileset.triles.append(trile)
        trileset.meta[trile.name] = {
            'meshId': index,
            'trileId': trile.id,
            'hasMesh': has_geometry,
            'surfaceType': trile.surface,
            'isImmaterial': trile.immaterial,
            'actorType': trile.actor,
            'collisionFaces': trile.faces,
            'collisionSize': astuple(trile.size),
            'textureAtlas': astuple(trile.atlas),
        }
    
    return trileset


def convert_trileset_to_gltf(trileset: TrileSet, embed_texture: bool) -> GltfBuilder:
    builder = GltfBuilder(trileset.name) \
        .set_image(trileset.name.lower(), embed_texture) \
        .set_material(trileset.name)
    
    translation = Vector3()
    count = 0

    for trile in trileset.triles:
        if not trile.vertex:
            builder.create_node(trile.name, translation)
        else:
            builder.create_mesh(trile.name, translation) \
                .set_vertices(trile.vertex) \
                .set_normals(trile.normal) \
                .set_texcoords(trile.texture) \
                .set_indices(trile.index) \

        count += 1
        translation.x += 2

        if (count % 15 == 0):
            translation.x = 0
            translation.z -= 2
    
    return builder


def save_to_gltf_file(builder: GltfBuilder, texture_path: Path, save_path: Path, meta: dict[str, Any]) -> None:
    import datetime
    
    calendar = datetime.date.today().isocalendar()
    yy = f'{calendar.year - 2000}'
    ww = f'{calendar.week:02}'
    dw = chr(calendar.weekday + 96)

    copyright = f'converted by zerocker at {yy}w{ww}{dw}'
    generator = 'kompass'
    
    builder.set_asset(copyright, generator, **meta) \
        .build(texture_path.parent, save_path)


def generate_mesh_library_tscn(trileset: TrileSet, path: Path) -> None:
    for trile in trileset.triles:
        trile.rid = generate_scene_unique_id('BoxShape3D')
    
    template = mako.template.Template(filename='templates/mesh_library.tscn')
    text = template.render(
        folder = 'meshes',
        name = path.stem,
        steps = len(trileset.triles) + 2,
        triles = trileset.triles,
        scene_name = trileset.name,
        id = generate_scene_unique_id(1)
    )

    with open(path, 'wt', encoding='utf-8') as tscn:
        tscn.write(text)


@click.command()
@click.argument('xml')
@click.argument('texture')
@click.option('--embedded', '-e', is_flag=True, help='Embedd *.png image to GLTF file')
@click.option('--generate-tscn', '-g', 'generate_tscn', is_flag=True, help='Generates mesh library TSCN')
def main(xml: str, texture: str, embedded: bool, generate_tscn: bool):
    xml_path = Path(xml).resolve()
    texture_path = Path(texture).resolve()
    gltf_path = Path(xml_path).with_suffix('.gltf')
    tscn_path = Path(xml_path).with_suffix('.tscn')

    logging.info('parsing the %s', xml_path.name)

    raw = read_xml_file(xml_path)
    trileset = parse_trile_from_xml(raw)
    
    logging.info('converting to %s', gltf_path.name)

    gltf = convert_trileset_to_gltf(trileset, embedded)
    save_to_gltf_file(gltf, texture_path, gltf_path, trileset.meta)

    if generate_tscn:
        logging.info('generate mesh library scene as %s', tscn_path.name)
        generate_mesh_library_tscn(trileset, tscn_path)


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(levelname)s] %(funcName)s: %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    
    main()

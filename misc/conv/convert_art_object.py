import click
import logging

from common import Geometry, Vector2, Vector3, read_geometry_from_xml, read_xml_file
from dataclasses import dataclass, field
from gltf_builder import GltfBuilder
from pathlib import Path


@dataclass
class ArtObject(Geometry):
    size: Vector3 = field(default_factory=Vector3)


def parse_art_object_from_xml(xml: dict) -> ArtObject:
    art_object = ArtObject()
    art_object.name = getattr(xml.ArtObject, '@name')
    art_object.size = Vector3.parse(xml.ArtObject.Size.Vector3)
    
    primitives = xml.ArtObject.ShaderInstancedIndexedPrimitives
    read_geometry_from_xml(art_object, primitives)
    
    return art_object


def convert_art_object_to_gltf(art_object: ArtObject, texture_path: Path, embed_texture: bool) -> GltfBuilder:
    return GltfBuilder(art_object.name) \
        .set_image(texture_path.stem, embed_texture) \
        .set_material(art_object.name) \
        .create_mesh(art_object.name, Vector3()) \
        .set_vertices(art_object.vertex) \
        .set_normals(art_object.normal) \
        .set_texcoords(art_object.texture) \
        .set_indices(art_object.index)


def save_to_gltf_file(builder: GltfBuilder, texture_path: Path, save_path: Path) -> None:
    import datetime
    
    calendar = datetime.date.today().isocalendar()
    yy = f'{calendar.year - 2000}'
    ww = f'{calendar.week:02}'
    dw = chr(calendar.weekday + 96)

    copyright = f'converted by zerocker at {yy}w{ww}{dw}'
    generator = 'kompass'
    
    builder.set_asset(copyright, generator) \
        .build(texture_path.parent, save_path)


@click.command()
@click.argument('xml')
@click.argument('texture')
@click.option('--embedded', '-e', is_flag=True, help='Embedd *.png image to GLTF file')
def main(xml: str, texture: str, embedded: bool):
    xml_path = Path(xml).resolve()
    texture_path = Path(texture).resolve()
    gltf_path = Path(xml_path).with_suffix('.gltf')

    logging.info('parsing the %s', xml_path.name)

    raw = read_xml_file(xml_path)
    trileset = parse_art_object_from_xml(raw)
    
    logging.info('converting to %s', gltf_path.name)

    gltf = convert_art_object_to_gltf(trileset, texture_path, embedded)
    save_to_gltf_file(gltf, texture_path, gltf_path)


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(levelname)s] %(funcName)s: %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    
    main()

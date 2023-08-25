import json
import xmltodict

from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace


@dataclass
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def parse(element):
        return Vector3(
            float(getattr(element, '@x')),
            float(getattr(element, '@y')),
            float(getattr(element, '@z')),
        )


@dataclass
class Vector2:
    x: float = 0.0
    y: float = 0.0

    def parse(element: object):
        return Vector2(
            float(getattr(element, '@x')),
            float(getattr(element, '@y')),
        )


@dataclass
class Quaternion:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 0.0

    def parse(element: object):
        return Vector3(
            float(getattr(element, '@x')),
            float(getattr(element, '@y')),
            float(getattr(element, '@z')),
            float(getattr(element, '@w')),
        )


@dataclass
class Face:
    a: int = 0
    b: int = 0
    c: int = 0

    def parse(chunk):
        return Face(
            a=int(chunk[0]),
            b=int(chunk[1]),
            c=int(chunk[2]),
        )


@dataclass
class Geometry:
    name: str = ''
    vertex: list[Vector3] = field(default_factory=list)
    normal: list[Vector3] = field(default_factory=list)
    texture: list[Vector2] = field(default_factory=list)
    index: list[Face] = field(default_factory=list)


NORMALS = [
    Vector3(-1, 0, 0),
    Vector3(0, -1, 0),
    Vector3(0, 0, -1),
    Vector3(1, 0, 0),
    Vector3(0, 1, 0),
    Vector3(0, 0, 1)
]


def read_xml_file(path: Path) -> SimpleNamespace:
    with open(path, 'rt') as file:
        dictionary = xmltodict.parse(file.read())
    
    string = json.dumps(dictionary)
    xml = json.loads(string, object_hook=lambda x: SimpleNamespace(**x))

    return xml


def divide_to_chunks(lst: list, size: int):
    for i in range(0, len(lst), size):
        yield lst[i:i+size]


def read_geometry_from_xml(geometry: Geometry, xml: object) -> bool:
    if not hasattr(xml.Vertices, 'VertexPositionNormalTextureInstance'):
        return False

    vertices = xml.Vertices.VertexPositionNormalTextureInstance
    for vertex in vertices:
        position = Vector3.parse(vertex.Position.Vector3)
        geometry.vertex.append(position)

        texture = Vector2.parse(vertex.TextureCoord.Vector2)
        geometry.texture.append(texture)

        normal_idx = int(vertex.Normal)
        normal = NORMALS[normal_idx]
        geometry.normal.append(normal)

    indices = xml.Indices.Index
    indices = divide_to_chunks(indices, 3)

    for idx in indices:
        face = Face.parse(idx)
        geometry.index.append(face)
    
    return True
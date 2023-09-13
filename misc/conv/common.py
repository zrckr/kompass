import json
import mmh3
import time
import random
import wordsegment
import xmltodict

from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Self


@dataclass
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    @staticmethod
    def parse(element):
        return Vector3(
            float(getattr(element, '@x')),
            float(getattr(element, '@y')),
            float(getattr(element, '@z')),
        )

    def __str__(self: Self) -> str:
        return f'Vector3( {self.x}, {self.y}, {self.z} )'


@dataclass
class Vector2:
    x: float = 0.0
    y: float = 0.0

    @staticmethod
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

    @staticmethod
    def parse(element: object):
        return Quaternion(
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

    @staticmethod
    def parse(chunk: list[str]):
        return Face(
            a=int(chunk[0]),
            b=int(chunk[1]),
            c=int(chunk[2]),
        )


@dataclass
class Rect2:
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0

    @staticmethod
    def parse(element: object):
        return Rect2(
            int(getattr(element, '@x')),
            int(getattr(element, '@y')),
            int(getattr(element, '@w')),
            int(getattr(element, '@h')),
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

WORDSEGMENT_LOADED = False


def read_xml_file(path: Path) -> SimpleNamespace:
    with open(path, 'rt') as file:
        dictionary = xmltodict.parse(file.read())
    
    string = json.dumps(dictionary)
    xml = json.loads(string, object_hook=lambda x: SimpleNamespace(**x))

    return xml


def divide_to_chunks(lst: list, size: int):
    for i in range(0, len(lst), size):
        yield lst[i:i+size]


def read_geometry_from_xml(geometry: Geometry, xml: SimpleNamespace) -> bool:
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

def to_snake_case(string: str) -> str:
    global WORDSEGMENT_LOADED
    if not WORDSEGMENT_LOADED:
        wordsegment.load()
        WORDSEGMENT_LOADED = True

    splitted_string = wordsegment.segment(string)
    snake_string = '_'.join(splitted_string).lower()

    return snake_string


def generate_scene_unique_id(prefix: int | str) -> str:
    timestamp = int(time.time()).to_bytes(4)
    hash = mmh3.hash(signed=False, key=timestamp)
    
    for _ in range(7):
        number = random.getrandbits(32).to_bytes(4)
        hash = mmh3.hash(signed=False, seed=hash, key=number)

    characters = 5
    char_count = ord('z') - ord('a')
    base = char_count + (ord('9') - ord('0'))

    id = ''
    for _ in range(characters):
        c = hash % base
        if c < char_count:
            id += chr(ord('a') + c)
        else:
            id += chr(ord('0') + (c - char_count))
        hash //= base

    return f'"{prefix}_{id}"'
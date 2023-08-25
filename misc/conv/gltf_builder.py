import numpy as np
import pygltflib as gltf

from common import Face, Vector2, Vector3
from dataclasses import astuple
from pathlib import Path
from typing import Self


def _as_bytes(lst: list, type: str, flat: bool = False) -> bytes:
    mapped = list(map(astuple, lst))
    array = np.array(mapped, dtype=type)
    array = array.flatten() if flat else array
    return array.tobytes()


def _find_min_max(lst: list, type: str) -> list[float]:
    mapped = list(map(astuple, lst))
    array = np.array(mapped, dtype=type)
    return [
        array.min(axis=0).tolist(),
        array.max(axis=0).tolist()
    ]


class GltfBuilder:
    # Common
    name: str
    binary_blob: bytes
    length: int
    buffer: int
    image_format: str

    # Scene
    asset: gltf.Asset
    nodes: list[gltf.Node]
    meshes: list[gltf.Mesh]
    accessors: list[gltf.Accessor]
    views: list[gltf.BufferView]
    
    # Texturing
    image: gltf.Image
    material: gltf.Material
    sampler: gltf.Sampler
    texture: gltf.Texture


    def __init__(self: Self, name: str) -> None:
        self.name = name
        self.binary_blob = b''
        self.length = 0
        self.buffer = 0
        self.message = ''
        self.image_format = ''

        self.nodes = []
        self.meshes = []
        self.accessors = []
        self.views = []

        self.image = gltf.Image()
        self.material = gltf.Material()
        self.sampler = gltf.Sampler()
        self.texture = gltf.Texture()
    

    def create_node(self: Self, name: str, translation: Vector3 = Vector3()) -> Self:
        self.nodes.append(gltf.Node(
            name=name,
            translation=astuple(translation)
        ))

        return self
    

    def create_mesh(self: Self, name: str, translation: Vector3 = Vector3()) -> Self:
        self.nodes.append(gltf.Node(
            name=name,
            mesh=len(self.meshes),
            translation=astuple(translation)
        ))

        self.meshes.append(gltf.Mesh(
            name=name,
            primitives=[
                gltf.Primitive(
                    attributes=gltf.Attributes(
                        POSITION=-1,
                        NORMAL=-1,
                        TEXCOORD_0=-1
                    ),
                    indices=-1,
                    material=0
                )
            ]
        ))

        return self


    def set_vertices(self: Self, vertices: list[Vector3]) -> Self:
        assert self.meshes, 'Create the mesh first'

        blob = _as_bytes(vertices, 'float32')
        min, max = _find_min_max(vertices, 'float32')

        self.views.append(gltf.BufferView(
            buffer=self.buffer,
            byteOffset=len(self.binary_blob),
            byteLength=len(blob)
        ))

        view_id = len(self.views) - 1
        self.binary_blob += blob
        self.length += len(blob)

        self.accessors.append(gltf.Accessor(
            bufferView=view_id,
            type=gltf.VEC3,
            componentType=gltf.FLOAT,
            count=len(vertices),
            min=min,
            max=max,
        ))

        accessor_id = len(self.accessors) - 1
        self.meshes[-1].primitives[0].attributes.POSITION = accessor_id
        return self


    def set_normals(self: Self, normals: list[Vector3]) -> Self:
        assert self.meshes, 'Create the mesh first'
        
        blob = _as_bytes(normals, 'float32')

        self.views.append(gltf.BufferView(
            buffer=self.buffer,
            byteOffset=len(self.binary_blob),
            byteLength=len(blob)
        ))

        view_id = len(self.views) - 1
        self.binary_blob += blob
        self.length += len(blob)

        self.accessors.append(gltf.Accessor(
            bufferView=view_id,
            type=gltf.VEC3,
            componentType=gltf.FLOAT,
            count=len(normals)
        ))

        accessor_id = len(self.accessors) - 1
        self.meshes[-1].primitives[0].attributes.NORMAL = accessor_id
        return self
    

    def set_texcoords(self: Self, texcoords: list[Vector2]) -> Self:
        assert self.meshes, 'Create the mesh first'
        
        blob = _as_bytes(texcoords, 'float32')

        self.views.append(gltf.BufferView(
            buffer=self.buffer,
            byteOffset=len(self.binary_blob),
            byteLength=len(blob)
        ))

        view_id = len(self.views) - 1
        self.binary_blob += blob
        self.length += len(blob)

        self.accessors.append(gltf.Accessor(
            bufferView=view_id,
            type=gltf.VEC2,
            componentType=gltf.FLOAT,
            count=len(texcoords)
        ))

        accessor_id = len(self.accessors) - 1
        self.meshes[-1].primitives[0].attributes.TEXCOORD_0 = accessor_id
        return self


    def set_indices(self: Self, indices: list[Face]) -> Self:
        assert self.meshes, 'Create the mesh first'
        
        blob = _as_bytes(indices, 'uint32')

        self.views.append(gltf.BufferView(
            buffer=self.buffer,
            byteOffset=len(self.binary_blob),
            byteLength=len(blob)
        ))

        view_id = len(self.views) - 1
        self.binary_blob += blob
        self.length += len(blob)

        self.accessors.append(gltf.Accessor(
            bufferView=view_id,
            type=gltf.SCALAR,
            componentType=gltf.UNSIGNED_INT,
            count=len(indices) * 3
        ))

        accessor_id = len(self.accessors) - 1
        self.meshes[-1].primitives[0].indices = accessor_id
        return self


    def set_material(self: Self, name: str) -> Self:
        self.material = gltf.Material(
            name=name,
            doubleSided=True,
            emissiveFactor=[
                0,
                0,
                0
            ],
            pbrMetallicRoughness=gltf.PbrMetallicRoughness(
                baseColorTexture=gltf.TextureInfo(
                    index=0,
                    texCoord=0
                ),
                metallicFactor=0,
                roughnessFactor=1
            ),
            alphaMode=gltf.OPAQUE,
            alphaCutoff=None
        )
        return self


    def set_image(self: Self, name: str, embed_texture: bool) -> Self:
        self.image.mimeType = 'image/png'
        self.image.uri = name + '.png'

        self.image_format = (
            gltf.ImageFormat.DATAURI if embed_texture
            else gltf.ImageFormat.FILE
        )

        self.sampler.magFilter = gltf.NEAREST
        self.sampler.minFilter = gltf.NEAREST_MIPMAP_NEAREST

        self.texture.sampler = 0
        self.texture.source = 0
        return self


    def set_asset(self: Self, copyright: str, generator: str, **extras) -> Self:
        self.asset = gltf.Asset(
            copyright=copyright,
            generator=generator,
            extras=extras
        )
        return self


    def build(self: Self, texture_path: Path, save_path: Path) -> None:
        instance = gltf.GLTF2()
        instance.scenes.append(gltf.Scene(name=self.name))
        instance.buffers.append(gltf.Buffer(byteLength=0))

        instance.scenes[0].nodes += [x for x in range(len(self.nodes))]
        instance.scene = 0

        instance.nodes += self.nodes
        instance.meshes += self.meshes
        instance.accessors += self.accessors
        instance.bufferViews += self.views

        instance.samplers.append(self.sampler)
        instance.images.append(self.image)
        instance.textures.append(self.texture)
        instance.materials.append(self.material)

        instance.set_binary_blob(self.binary_blob)
        instance.buffers[0].byteLength = self.length

        instance.convert_buffers(gltf.BufferFormat.DATAURI)
        instance.convert_images(self.image_format, path=texture_path)

        instance.save(save_path, self.asset)

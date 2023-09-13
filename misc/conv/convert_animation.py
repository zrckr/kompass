import math
import click
import logging
import mako.template

from pathlib import Path
from common import Rect2, Vector2, read_xml_file, to_snake_case, generate_scene_unique_id
from dataclasses import asdict, dataclass, field
from types import SimpleNamespace


@dataclass
class AnimatedTexturePC:
    size: Vector2 = field(default_factory=Vector2)
    actualSize: Vector2 = field(default_factory=Vector2)
    durations: list[float] = field(default_factory=list)
    frames: list[Rect2] = field(default_factory=list)
    speed: float = 0.0


@dataclass
class AnimationResource:
    id: str = ''
    name: str = ''
    folder: str = ''
    length: float = 0.0
    times: list[float] = field(default_factory=list)
    transitions: list[float] = field(default_factory=list)
    values: list[Rect2] = field(default_factory=list)
    offset: Vector2 = field(default_factory=Vector2)


@dataclass
class TextureResource:
    id: str = ''
    name: str = ''
    folder: str = ''


@dataclass
class AtlasTexture:
    id: str = ''
    texture: str = ''
    region: Rect2 = field(default_factory=Rect2)


@dataclass
class SpriteFrame:
    duration: float = 0.0
    texture: str = ''


@dataclass
class SpriteFramesAnimation:
    frames: list[SpriteFrame] = field(default_factory=list)
    loop: bool = False
    speed: float = 0.0
    name: str = ''


def parse_anim_from_xml(xml: SimpleNamespace) -> AnimatedTexturePC:
    def parse_sizes(xml, target):
        target.size = Vector2(
            float(getattr(xml, '@width')),
            float(getattr(xml, '@height')))
    
        target.actualSize = Vector2(
            float(getattr(xml, '@actualWidth')),
            float(getattr(xml, '@actualHeight')))
    
    def parse_pc(xml, target):
        for frame in xml.Frames.FramePC:
            duration = int(getattr(frame, '@duration'))
            target.durations.append(duration)
            
            rect = Rect2.parse(frame.Rectangle)
            target.frames.append(rect)

    def parse_xbox(xml, target):
        offset_y = 0
        
        if type(xml.Frames.Frame) is not list:
            xml.Frames.Frame = [xml.Frames.Frame]

        for frame in xml.Frames.Frame:
            duration = int(getattr(frame, '@duration'))
            target.durations.append(duration)
            
            rect = Rect2(
                x = 0,
                y = offset_y,
                w = target.size.x,
                h = target.size.y
            )

            target.frames.append(rect)
            offset_y += target.size.y


    anim_texture = AnimatedTexturePC()
    
    if hasattr(xml, 'AnimatedTexture'):
        parse_sizes(xml.AnimatedTexture, anim_texture)
        parse_xbox(xml.AnimatedTexture, anim_texture)
    elif hasattr(xml, 'AnimatedTexturePC'):
        parse_sizes(xml.AnimatedTexturePC, anim_texture)
        parse_pc(xml.AnimatedTexturePC, anim_texture)
    
    return anim_texture


def convert_anim_to_sprite_frames(anim_textures: list[tuple[Path, AnimatedTexturePC]]) -> str:
    textures: list[TextureResource] = []
    atlases: list[AtlasTexture] = []
    animations: list[SpriteFramesAnimation] = []

    for i, (path, anim_texture) in enumerate(anim_textures, 1):
        textures.append(TextureResource(
            id = generate_scene_unique_id(i),
            name = path.stem,
            folder = path.parent.stem,
        ))

        sprites: list[SpriteFrame] = []

        for frame, duration in zip(anim_texture.frames, anim_texture.durations):
            atlases.append(AtlasTexture(
                id = generate_scene_unique_id('AtlasTexture'),
                texture = textures[-1].id,
                region = frame,
            ))

            sprites.append(SpriteFrame(
                duration = 1.0,
                texture = atlases[-1].id,
            ))
        
        animations.append(SpriteFramesAnimation(
            frames = sprites,
            loop = True,
            speed = anim_texture.speed,
            name = path.stem
        ))

    steps = len(atlases) + len(textures) + 1

    template = mako.template.Template(filename='templates/sprite_frames.tres')
    text = template.render(
        steps = steps,
        textures = textures,
        atlases = atlases,
        animations = animations
    )

    return text


def convert_anim_to_animations(anim_texture: AnimatedTexturePC, path: Path) -> str:
    def concat(lst: list) -> str:
        return ', '.join(map(str, lst))
    
    resource = AnimationResource()
    resource.name = path.stem
    resource.folder = path.parent.stem
    resource.id = generate_scene_unique_id(1)

    resource.values += anim_texture.frames
    for duration in anim_texture.durations:
        resource.transitions.append(1)
        resource.times.append(round(resource.length, 2))
        resource.length += duration / 10**7

    resource.times = concat(resource.times)
    resource.values = concat(resource.values)
    resource.transitions = concat(resource.transitions)
    resource.length = '%.3f' % resource.length
    resource.offset = str(Vector2(0, 2))

    template = mako.template.Template(filename='templates/animation.tres')
    text = template.render(**asdict(resource))

    return text


def rename_anim_texture(texture_path: Path, name: str) -> None:
    new_path = Path(texture_path.parent, name).with_suffix('.png')

    if not texture_path.exists():
        logging.warning('skipping %s', texture_path)
        return
    
    logging.info('renaming %s -> %s', texture_path.name, new_path.name)
    texture_path.rename(new_path)


def save_to_tres_file(tres_text: str, tres_path) -> None:
    with open(tres_path, 'wt', encoding='utf-8') as tres:
        tres.write(tres_text)


@click.command()
@click.argument('xml')
@click.option('--output', '-o', type=click.Choice(['sprite-frames', 'animations']), required=True)
@click.option('--fps', '-s', default=7.0)
@click.option('--rename-texture', '-rt', 'rename_texture', is_flag=True)
def main(xml: str, output: str, fps: float, rename_texture: bool):
    xml_path = Path(xml).resolve()
    texture_path = xml_path.with_suffix('.ani.png')

    logging.info('parsing the %s', xml_path.name)

    raw = read_xml_file(xml_path)
    anim_data = parse_anim_from_xml(raw)
    anim_data.speed = fps

    converted_name = to_snake_case(xml_path.stem)
    tres_path = Path(xml_path.parent, converted_name).with_suffix('.tres')

    logging.info('converting to %s', tres_path.name)

    match output:
        case 'sprite-frames':
            tres_text = convert_anim_to_sprite_frames( [(tres_path, anim_data)] )
        case 'animations':
            tres_text = convert_anim_to_animations(anim_data, tres_path)
    
    save_to_tres_file(tres_text, tres_path)
    if rename_texture:
        rename_anim_texture(texture_path, converted_name)


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(levelname)s] %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    
    main()
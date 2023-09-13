import click

from pathlib import Path
from convert_animation import main as convert_animation
from convert_art_object import main as convert_art_object
from convert_trileset import main as convert_trileset


OVERRIDE_CONVERTED = True


def is_converted(path: Path, suffix: str) -> bool:
    if OVERRIDE_CONVERTED:
        return False
    return path.with_suffix(suffix).exists()


def process_art_objects(root: Path):
    art_objects = root / Path('art objects')
    for art_object in art_objects.glob('*.xml'):
        if is_converted(art_object, '.gltf'):
            continue

        print(f'[ART OBJECT] {art_object.name}')
        
        path = str(art_object)
        if 'ao_b.xml' in path:
            path = path.replace('ao_b.xml', '_bao.xml')

        # replace 'ao.xml' suffix with '.png'
        texture = Path(path[:-6]).with_suffix('.png')
        
        convert_art_object.callback(
            xml=art_object,
            texture=texture,
            embedded=False
        )


def process_trilesets(root: Path):
    trilesets = root / Path('trile sets')
    for trileset in trilesets.glob('*.xml'):
        if is_converted(trileset, '.gltf'):
            continue

        print(f'[TRILE SET] {trileset.name}')
        
        texture = trileset.with_suffix('.png')
        convert_trileset.callback(
            xml=trileset,
            texture=texture,
            embedded=False,
            generate_tscn=True
        )


def process_character_animations(root: Path):
    character_animations = root / Path('character animations')
    for character in character_animations.iterdir():
        for animation in character.glob('*.xml'):
            if is_converted(animation, '.tres'):
                continue
            
            if animation.stem == 'metadata':
                continue

            print(f'[CHARACTER ANIMATION] {animation.parent.name}/{animation.name}')
            
            convert_animation.callback(
                xml=animation,
                output='animations',
                fps=7,
                rename_texture=False
            )


def process_animated_background_planes(root: Path):
    background_planes = root / Path('background planes')
    for background_plane in background_planes.glob('**/*.xml'):
        if is_converted(background_plane, '.tres'):
            continue
        
        print(f'[BACKGROUND PLANE] {background_plane.name}')

        convert_animation.callback(
            xml=background_plane,
            output='sprite-frames',
            fps=7,
            rename_texture=False
        )


@click.command()
@click.argument('assets')
def main(assets: str):
    root = Path(assets).resolve()
    assert root.is_dir, f"The '{root}' is not a folder"

    process_art_objects(root)
    process_trilesets(root)
    process_character_animations(root)
    process_animated_background_planes(root)


if __name__ == '__main__':
    main()
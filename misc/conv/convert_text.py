import click
import logging
import mako.template

from common import read_xml_file
from pathlib import Path


def parse_text_from_xml(xml: dict) -> dict[str, dict[str, str]]:
    text = {}

    for dictionary in xml.Dict.Entry:
        name = getattr(dictionary, '@key')
        name = name if name else 'en'
        
        text[name] = {}
        for entry in dictionary.Dict.Entry:
            key = getattr(entry, '@key')
            message = getattr(entry, '#text')
            text[name][key] = message

    return text

def convert_text_to_po(locale: str, text: dict[str, str], path: Path):
    messages: dict[str, str | list[str]] = {}

    for key in text.keys():
        message = text[key]

        if '\n' in message:
            message = message.split('\n')

        if type(message) is list:
            message = [msg.replace('\r', '\\n') for msg in message]

        messages[key] = message
    
    template = mako.template.Template(filename='templates/fez.po')
    text = template.render(locale=locale, messages=messages)

    with open(path, 'wt', encoding='utf-8') as po:
        po.write(text)


@click.command()
@click.argument('xml')
def main(xml: str):
    xml_path = Path(xml).resolve()

    logging.info('parsing the %s', xml_path.name)
    raw = read_xml_file(xml_path)
    entries = parse_text_from_xml(raw)

    for locale, entries in entries.items():
        po_path = xml_path.with_suffix(f'.{locale}.po')
        logging.info('converting to %s', po_path.name)
        convert_text_to_po(locale, entries, po_path)



if __name__ == '__main__':
    logging.basicConfig(
        format='[%(levelname)s] %(funcName)s: %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    
    main()
import click
import csv
import json
from .gemini import get_json as gemini_get_json
from .fyb import get_json as fyb_get_json


@click.group()
def main():
    pass


@main.command()
@click.argument('exchange', type=click.Choice(['fyb', 'gemini']))
@click.argument('path', type=click.Path(exists=True))
@click.option('--sep', '-s', type=click.Choice([';', ',']))
def tojson(exchange, path, sep):
    if exchange == 'gemini':
        with open(path, 'rU') as fi:
            reader = csv.reader(fi, dialect=csv.excel_tab, delimiter=sep)
            header = reader.next()
        if 'Specification' in header:
            print 'start converting gemini'
            obj = gemini_get_json(path, sep)
            with open('.'.join(path.split('.')[:-1])+'.json', 'w') as fo:
                json.dump(obj, fo)
            print 'done converting gemini'
    if exchange == 'fyb':
        print 'start converting fyb'
        obj = fyb_get_json(path)
        with open('.'.join(path.split('.')[:-1])+'.json', 'w') as fo:
            json.dump(obj, fo)
        print 'done converting fyb'

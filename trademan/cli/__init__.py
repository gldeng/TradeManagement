import click
import csv
import json
from .gemini import get_json as gemini_get_json


@click.group()
def main():
    pass


@main.command()
@click.argument('csvfile', type=click.Path(exists=True))
@click.option('--sep', '-s', type=click.Choice([';', ',']))
def tojson(csvfile, sep):
    with open(csvfile, 'rU') as fi:
        reader = csv.reader(fi, dialect=csv.excel_tab, delimiter=sep)
        header = reader.next()
    print sep
    if 'Specification' in header:
        print 'start converting gemini'
        with open(csvfile[:-4]+'.json', 'w') as fo:
            obj = gemini_get_json(csvfile, sep)
            json.dump(obj, fo)
        print 'done converting gemini'

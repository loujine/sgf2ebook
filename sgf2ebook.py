#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZipFile

import jinja2
from sente import sgf  # type: ignore

__version__ = (1, 0, 0)

SGF_RENDER_EXECUTABLE = './sgf-render'

TEMPLATEDIR = Path(__file__, '..', 'epub_template').resolve()


def load_sgf(sgfpath: Path):
    game = sgf.load(str(sgfpath))
    comments = {}
    seq = game.get_default_sequence()
    for idx, move in enumerate(seq, 1):
        game.play(move)
        if game.comment:
            comments[idx] = game.comment
    return {
        # read only main sequence, not variations
        'nb_moves': len(seq),
        'metadata': game.get_properties(),
        'comments': comments,
    }


def main(sgfpath: Path, output_path: Path) -> None:
    print()
    print(f'Load content of {sgfpath}')
    sgf_content = load_sgf(sgfpath)
    nb_moves = sgf_content['nb_moves']
    metadata = sgf_content['metadata']
    comments = sgf_content['comments']

    uuid = uuid4()

    with TemporaryDirectory() as tmpdir:
        print('Prepare structure of the ebook')
        shutil.copytree(TEMPLATEDIR, tmpdir, dirs_exist_ok=True)

        template = jinja2.Template(
            TEMPLATEDIR.joinpath('EPUB', 'Text', 'page_001.html').open().read())

        print('Prepare SVG diagrams')
        svgdirpath = Path(tmpdir, 'EPUB', 'Images')
        for move in range(1, nb_moves + 1):
            svgpath = f'diagram_{move:03}.svg'
            # generate SVG files with sgf-render
            subprocess.check_call([
                SGF_RENDER_EXECUTABLE,
                str(sgfpath),
                '--move-numbers',
                '--first-move-number', str(move),
                '-n', str(move),
                '--style', 'minimalist',
                '-o', svgdirpath.joinpath(svgpath),
            ])
            # create HTML page with SVG element
            html_content = template.render(
                title=sgfpath.stem,
                svgpath=svgpath,
                info=metadata,
                last_flag=(move == nb_moves),
                comment=comments.get(move, ''),
            )
            with Path(tmpdir, 'EPUB', 'Text', f'page_{move:03}.html').open('w') as fd:
                fd.write(html_content)

        # Declare all HTML/SVG files in master file
        print('Prepare content.opf file')
        template = jinja2.Template(
            TEMPLATEDIR.joinpath('EPUB', 'content.opf').open().read())
        opf_content = template.render(
            title=sgfpath.stem,
            creator='sgf2ebook',
            UUID=uuid,
            svgpath=sorted(svgdirpath.glob('*.svg')),
            enumerate=enumerate,
        )
        with Path(tmpdir, 'EPUB', 'content.opf').open('w') as fd:
            fd.write(opf_content)

        # Generate table of contents
        print('Prepare table of contents')
        template = jinja2.Template(
            TEMPLATEDIR.joinpath('EPUB', 'toc.ncx').open().read())
        toc_content = template.render(
            title=sgfpath.stem,
            UUID=uuid,
            nb_moves=nb_moves,
            range=range,
        )
        with Path(tmpdir, 'EPUB', 'toc.ncx').open('w') as fd:
            fd.write(toc_content)

        # zip all content in EPUB file
        output_path.mkdir(exist_ok=True, parents=True)
        output_name = f"{metadata.get('EV', 'unknown_event')}{'_' if 'RO' in metadata else ''}{metadata.get('RO', '')}.epub".replace(' ', '_')
        with ZipFile(output_path.joinpath(output_name), 'w') as zf:
            os.chdir(tmpdir)
            # "The first file in the OCF ZIP Container MUST be the mimetype file"
            zf.write('mimetype')
            for root, dirs, files in os.walk('.'):
                for file in sorted(files):
                    if file != 'mimetype':
                        zf.write(Path(root, file))
            os.chdir(Path(__file__).parent)
    print(f'{output_path.joinpath(output_name)} generated')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='')
    parser.add_argument('--input-path', '-i', help='Input files or directory')
    parser.add_argument('--output-path', '-o', help='Output directory')
    args = parser.parse_args()

    path = Path(args.input_path)
    outpath = Path(args.output_path)
    if not path.exists():
        print(f'Input path {path} not found')
        sys.exit(1)
    if path.is_file():
        main(path, outpath)
    if path.is_dir():
        for filepath in sorted(path.rglob('*.sgf')):
            main(filepath, outpath)

"""Qt-free project inspection and lossless batch export for Mellow Studio.

python -m mellowstudio.cli info examples/mellow_original.mellowzip
python -m mellowstudio.cli export project.mellowzip --format frames --out frames/
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from PIL import Image
from .model import Document, blank, project_load


def project_info(doc: Document) -> dict:
    return {
        'name': doc.name,
        'size': [doc.width, doc.height],
        'frame_count': len(doc.frames),
        'layer_count': len(doc.layers),
        'layers': [{'name': item.name, 'id': item.id, 'visible': item.visible,
                    'locked': item.locked, 'opacity': item.opacity}
                   for item in doc.layers],
        'durations_ms': [frame.duration_ms for frame in doc.frames],
        'linked_exposure_groups': {
            layer.name: _linked_groups(doc, layer.id) for layer in doc.layers
        },
        'guides': doc.guides,
        'embedded_references': [{'frame': i + 1, 'name': ref.name,
            'source_size': list(ref.source_size), 'calibration': ref.calibration,
            'registration': ref.registration} for i, f in enumerate(doc.frames)
            if (ref := doc.reference_for_frame(i)) is not None],
    }


def _linked_groups(doc: Document, layer_id: str) -> list[list[int]]:
    consumed = set()
    groups = []
    for i in range(len(doc.frames)):
        if i in consumed:
            continue
        frames = doc.linked_frames(layer_id, i)
        consumed.update(frames)
        if len(frames)>1:
            groups.append([n+1 for n in frames])
    return groups


def export(doc: Document, dest: Path, kind: str, frame: int = 1,
           layout: str = 'horizontal') -> list[Path]:
    """Export the project's composite, never screenshot-scale pixels."""
    if kind == 'png':
        if frame < 1 or frame > len(doc.frames):
            raise ValueError('Requested frame is outside the animation.')
        dest.parent.mkdir(parents=True, exist_ok=True)
        doc.composite(frame-1).save(dest, format='PNG')
        return [dest]

    if kind == 'frames':
        dest.mkdir(parents=True, exist_ok=True)
        files=[]
        for i in range(len(doc.frames)):
            out=dest/f'frame_{i+1:04d}.png'
            doc.composite(i).save(out, format='PNG')
            files.append(out)
        manifest=dest/'frames.json'
        manifest.write_text(json.dumps({'frame_count':len(doc.frames),
            'width':doc.width, 'height':doc.height,
            'durations_ms':[frame.duration_ms for frame in doc.frames]},indent=2),encoding='utf-8')
        return [*files, manifest]

    if kind == 'sheet':
        dest.parent.mkdir(parents=True, exist_ok=True)
        horizontal = layout == 'horizontal'
        count = len(doc.frames)
        w,h=doc.width,doc.height
        sheet=blank(w*count if horizontal else w,h if horizontal else h*count)
        for i in range(count):
            sheet.paste(doc.composite(i),(w*i if horizontal else 0,0 if horizontal else h*i))
        sheet.save(dest,format='PNG')
        manifest=dest.with_suffix('.json')
        manifest.write_text(json.dumps({'frame_count':count,'width':w,'height':h,
            'layout':layout,'durations_ms':[frame.duration_ms for frame in doc.frames]},indent=2),encoding='utf-8')
        return [dest,manifest]

    raise ValueError('Unsupported export format.')


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description='Mellow Studio headless project tools')
    subs=parser.add_subparsers(dest='command',required=True)
    info=subs.add_parser('info',help='Inspect a native .mellowzip project')
    info.add_argument('project',type=Path)
    validate=subs.add_parser('validate',help='Validate project and every cel')
    validate.add_argument('project',type=Path)
    exp=subs.add_parser('export',help='Export lossless native-resolution PNGs')
    exp.add_argument('project',type=Path)
    exp.add_argument('--format',choices=('png','frames','sheet'),default='sheet')
    exp.add_argument('--out',required=True,type=Path)
    exp.add_argument('--frame',type=int,default=1,help='1-based frame number for PNG')
    exp.add_argument('--layout',choices=('horizontal','vertical'),default='horizontal')
    args=parser.parse_args(argv)
    try:
        doc=project_load(args.project)
        if args.command=='info':
            print(json.dumps(project_info(doc),indent=2))
        elif args.command=='validate':
            print(f'VALID · {doc.width}×{doc.height} · {len(doc.frames)} frames · {len(doc.layers)} layers')
        else:
            files=export(doc,args.out,args.format,args.frame,args.layout)
            for path in files:
                print(path)
    except (OSError,ValueError,KeyError,IndexError) as error:
        parser.exit(2,f'Mellow Studio: {error}\n')
    return 0


if __name__=='__main__':
    raise SystemExit(main())

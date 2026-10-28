"""Repeatable headless Mellow Studio performance baseline (not a CI speed gate).

Run from repository root: python scripts/benchmark.py --output benchmark.json
Reports wall time and Python-tracked peak allocations, not GPU/frame timing.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import time
import tracemalloc

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mellowstudio.model import Document, History, project_save, project_load


def measured(fn, iterations: int = 8) -> dict:
    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000)
    return {'median_ms': round(statistics.median(times), 3),
            'max_ms': round(max(times), 3), 'samples': iterations}


def sample(size, layers, frames):
    d = Document(size[0], size[1], f'{size[0]}x{size[1]} benchmark')
    for i in range(layers-1):
        d.add_layer('Layer ' + str(i+2))
    for i in range(frames-1):
        d.duplicate_frame(linked=(i % 4 == 0))
    for i, frame in enumerate(d.frames):
        # Non-trivial image content with repeatable patterns and transparency.
        for li, layer in enumerate(d.layers):
            img = frame.cels[layer.id]
            if li == 0 and i > 0 and frame.cels[layer.id] is d.frames[i-1].cels[layer.id]:
                continue
            img.putpixel(((i * 7 + li * 3) % d.width, (i * 5 + li * 11) % d.height),
                         ((li * 17) % 256, (i * 11) % 256, 182, 255))
    d.active_frame = 0
    return d


def run():
    cases = [((41,55),2,8), ((128,128),8,24), ((256,256),4,24)]
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        for (w,h), layers, frames in cases:
            d = sample((w,h), layers, frames)
            target = Path(tmp) / f'{w}x{h}.mellowzip'
            tracemalloc.start()
            composite = measured(lambda: d.composite(d.active_frame), 20)
            frame_switch = measured(lambda: [d.composite(i) for i in range(len(d.frames))],3)
            history = History()
            history_measure = measured(lambda: (history.begin(d),
                d.cel.putpixel((w//2,h//2),(220,30,40,255)),history.commit(d)),3)
            save = measured(lambda: project_save(d,target), 3)
            load = measured(lambda: project_load(target), 3)
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            results.append({'logical_size':[w,h],'layers':layers,'frames':frames,
                'composite_one':composite,'composite_all':frame_switch,
                'history_edit':history_measure,'save':save,'load':load,
                'tracemalloc_peak_mib':round(peak/1048576,2),
                'notes':'Python tracked allocations only, may exclude PIL/Qt/native buffers'})
    return {'platform':platform.platform(),'python':sys.version.split()[0],
        'machine':platform.machine(), 'gpu_timing':'not measured',
        'results':results}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    report=run()
    data=json.dumps(report,indent=2)
    if args.output:
        args.output.write_text(data+'\n',encoding='utf-8')
    print(data)


if __name__ == '__main__':
    main()

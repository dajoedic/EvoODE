"""Assemble WP-X2 with lossless interning of repeated display arrays."""
from pathlib import Path
import argparse
import copy
import json
from build_wisp_explainer import BASE

def transport(data):
    """Presentation transport only; results.json remains schema version 2 verbatim."""
    data=copy.deepcopy(data)
    arrays,indices=[],{}
    def bundle(curves):
        if not curves:return
        for key in ('t','truth','model'):
            encoded=json.dumps(curves[key],separators=(',',':'),ensure_ascii=False)
            if encoded not in indices:
                indices[encoded]=len(arrays);arrays.append(curves[key])
            curves[key]={'$display':indices[encoded]}
        if curves.get('generalization'):bundle(curves['generalization'])
    for cell in data['results']['cells']:bundle(cell.get('curves'))
    for feature in data['live'].get('featured',[]):
        for candidate in feature['candidates']:bundle(candidate.get('curves'))
    data['display_arrays']=arrays
    return data

def build(base=BASE):
    src=base/'src'
    data={n:json.loads((base/'data'/f'{n}.json').read_text(encoding='utf8')) for n in ('live','results','manifest')}
    page=(src/'index.html').read_text(encoding='utf8')
    values={'STYLE':(src/'style.css').read_text(encoding='utf8'),
            'DATA':json.dumps(transport(data),ensure_ascii=False,separators=(',',':'),sort_keys=True).replace('<','\\u003c'),
            'COMPUTE':(src/'compute.js').read_text(encoding='utf8'),'APP':(src/'app.js').read_text(encoding='utf8')}
    for key,value in values.items():page=page.replace('<!--'+key+'-->',value)
    encoded=page.encode('utf8')
    if len(encoded)>14_000_000:raise ValueError(f'HTML size budget exceeded: {len(encoded)}')
    if sum(p.stat().st_size for p in (base/'data').rglob('*') if p.is_file())>17_000_000:raise ValueError('Data size budget exceeded')
    output=base/'dist/wisp_explainer.html';output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(encoded)
    print(json.dumps(dict(output=str(output),bytes=len(encoded))))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--base',type=Path,default=BASE)
    build(parser.parse_args().base)

"""Static, data-only update protocol. No executable rules or remote URLs in a database."""
from __future__ import annotations

import base64
import hashlib
import itertools
import json
from pathlib import Path
import re
import struct
import zlib

SCHEMA = 1
LAYOUT = 'white-footer-1400x220-v1'
FORMAT = 'LiquidGlassCamera.Database'
CACHE_MAGIC = 'LiquidGlassCameraCache/1'
CACHE_FILE = 'LiquidGlassCamera-database.txt'
BACKUP_FILE = 'LiquidGlassCamera-database-backup.txt'
MAX_PAYLOAD_BYTES = 8 * 1024 * 1024
MAX_ASSETS = 1000
TABLES = ('assets', 'brands', 'maker_aliases', 'model_brand_aliases',
          'model_art', 'partnerships', 'partnership_defaults')
OPTIONAL_TABLES = ('model_rows',)


def normalize(value):
    return re.sub(r'[^A-Za-z0-9\u4e00-\u9fff]', '', value.replace('+', 'plus')).lower()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def finite_aliases(pattern):
    """Expand the existing finite optional-prefix/alternative patterns at build time."""
    from re import _parser, _constants as c
    def expand(tokens):
        result = ['']
        for kind, value in tokens:
            if kind == c.AT:
                pieces = ['']
            elif kind == c.LITERAL:
                pieces = [chr(value)]
            elif kind == c.SUBPATTERN:
                pieces = expand(value[-1])
            elif kind == c.BRANCH:
                pieces = list(itertools.chain.from_iterable(expand(x) for x in value[1]))
            elif kind == c.MAX_REPEAT:
                low, high, child = value
                if high > 2:
                    raise ValueError('A database alias cannot contain an open-ended pattern')
                alphabet = expand(child)
                pieces = [''.join(x) for n in range(low, high + 1)
                          for x in itertools.product(alphabet, repeat=n)]
            elif kind == c.IN and all(t == c.LITERAL for t, _ in value):
                pieces = [chr(v) for _, v in value]
            else:
                raise ValueError(f'Unsupported finite alias token: {kind}')
            result = [a + b for a in result for b in pieces]
            if len(result) > 10000:
                raise ValueError('Too many finite aliases')
        return result
    return sorted(set(s.lower() for s in expand(_parser.parse(pattern, 0))))


def validate_png(raw):
    if not raw.startswith(b'\x89PNG\r\n\x1a\n') or len(raw) > 1024 * 1024:
        raise ValueError('Asset must be a PNG smaller than 1 MiB')
    offset, seen, compressed = 8, [], bytearray()
    while offset < len(raw):
        if offset + 12 > len(raw):
            raise ValueError('Truncated PNG')
        length = struct.unpack('>I', raw[offset:offset+4])[0]
        tag = raw[offset+4:offset+8]
        data = raw[offset+8:offset+8+length]
        end = offset + 12 + length
        if end > len(raw) or zlib.crc32(tag + data) & 0xffffffff != struct.unpack('>I', raw[end-4:end])[0]:
            raise ValueError('Invalid PNG chunk CRC')
        seen.append(tag)
        if tag == b'IHDR':
            if len(data) != 13 or struct.unpack('>II', data[:8]) != (1400, 220):
                raise ValueError('Asset dimensions must be 1400 x 220')
        if tag == b'IDAT':
            compressed.extend(data)
        offset = end
        if tag == b'IEND':
            break
    if not seen or seen[0] != b'IHDR' or seen[-1] != b'IEND' or offset != len(raw):
        raise ValueError('Invalid PNG structure')
    decoder = zlib.decompressobj()
    decoder.decompress(bytes(compressed), 4 * 1024 * 1024)
    if not decoder.eof:
        raise ValueError('Invalid or oversized PNG image data')


def validate_database(db):
    if not isinstance(db, dict) or db.get('format') != FORMAT or db.get('schema') != SCHEMA or db.get('layout') != LAYOUT:
        raise ValueError('Incompatible database schema/layout')
    revision = db.get('revision')
    if type(revision) is not int or not 1 <= revision <= 999999999999:
        raise ValueError('Revision must be a positive integer of at most 12 digits')
    for name in TABLES:
        if not isinstance(db.get(name), dict):
            raise ValueError(f'Missing dictionary: {name}')
    for name in OPTIONAL_TABLES:
        if name in db and not isinstance(db[name], dict):
            raise ValueError(f'Invalid optional dictionary: {name}')
    assets = db['assets']
    if not 1 <= len(assets) <= MAX_ASSETS:
        raise ValueError('Asset count is outside supported bounds')
    for key, encoded in assets.items():
        if not re.fullmatch(r'[A-Za-z0-9-]+', key) or not isinstance(encoded, str):
            raise ValueError('Unsafe asset key or value')
        validate_png(base64.b64decode(encoded, validate=True))
    if 'unknown' not in db['brands']:
        raise ValueError('Missing unknown-brand footer')
    for name in ('brands', 'model_art', 'partnerships', 'partnership_defaults', 'model_rows'):
        for key, asset in db.get(name, {}).items():
            pattern = (r'[a-z0-9]+' if name in ('brands', 'partnership_defaults')
                       else r'[a-z0-9]+/[a-z0-9\u4e00-\u9fff]+')
            if not re.fullmatch(pattern, key):
                raise ValueError(f'Unsafe lookup key in {name}')
            if asset not in assets:
                raise ValueError(f'Missing asset referenced by {name}: {asset}')
            if name == 'model_rows' and base64.b64decode(assets[asset], validate=True)[25] != 2:
                raise ValueError('Model rows must be opaque RGB PNG images')
    for name in ('maker_aliases', 'model_brand_aliases'):
        for alias, brand in db[name].items():
            if not alias or normalize(alias) != alias or brand not in db['brands']:
                raise ValueError(f'Invalid manufacturer alias: {alias}')
    if len(canonical(db)) > MAX_PAYLOAD_BYTES:
        raise ValueError('Database is too large')
    return db


def envelope(db):
    payload = canonical(validate_database(db))
    return {'format': 'LiquidGlassCamera.Package', 'schema': SCHEMA, 'layout': LAYOUT,
            'revision': db['revision'], 'payload_sha256': hashlib.sha256(payload).hexdigest(),
            'payload_base64': base64.b64encode(payload).decode('ascii')}


def read_envelope(package):
    if package.get('format') != 'LiquidGlassCamera.Package' or package.get('schema') != SCHEMA or package.get('layout') != LAYOUT:
        raise ValueError('Incompatible package')
    payload = base64.b64decode(package['payload_base64'], validate=True)
    if len(payload) > MAX_PAYLOAD_BYTES or hashlib.sha256(payload).hexdigest() != package['payload_sha256']:
        raise ValueError('Payload checksum mismatch')
    db = validate_database(json.loads(payload))
    if db['revision'] != package['revision']:
        raise ValueError('Package revision mismatch')
    return db


def cache_text(package):
    read_envelope(package)
    return CACHE_MAGIC + '\n' + package['payload_base64'] + '\n' + package['payload_sha256']


def publish(db, destination):
    """Immutable data file first, manifest last; a previous revision stays downloadable."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    package = envelope(db)
    name = f'database-{db["revision"]}.json'
    raw = canonical(package) + b'\n'
    target = destination / name
    if target.exists() and target.read_bytes() != raw:
        raise ValueError('A published revision is immutable; increase revision')
    old_manifest = destination / 'manifest.json'
    if old_manifest.exists():
        old = json.loads(old_manifest.read_text())
        if old['revision'] > db['revision']:
            raise ValueError('Refusing to downgrade published manifest')
        if old['revision'] == db['revision'] and old['payload_sha256'] != package['payload_sha256']:
            raise ValueError('Revision already published with a different checksum')
    target.write_bytes(raw)
    manifest = {k: package[k] for k in ('schema', 'layout', 'revision', 'payload_sha256')}
    manifest.update(format='LiquidGlassCamera.Manifest', database=name,
                    payload_bytes=len(base64.b64decode(package['payload_base64'])),
                    assets=len(db['assets']), model_aliases=len(db['model_art']),
                    partnership_aliases=len(db['partnerships']))
    temp = destination / 'manifest.json.tmp'
    temp.write_bytes(canonical(manifest) + b'\n')
    temp.replace(old_manifest)
    return manifest


def initial_database(source, revision=2026110501):
    source = Path(source)
    catalog = json.loads((source / 'Style-Catalog.json').read_text())
    assets = {}
    for pattern in ('Footer-*.png', 'CoBrand-*.png', 'ModelArt-*.png', 'ModelRow-*.png'):
        for path in sorted((source / 'Assets').glob(pattern)):
            assets[path.stem] = base64.b64encode(path.read_bytes()).decode('ascii')
    brands = {p.stem.removeprefix('Footer-'): p.stem for p in (source / 'Assets').glob('Footer-*.png')}
    aliases = {key: key for key in brands}
    additional = {
        'nikon': ['NIKON CORPORATION', '尼康'], 'canon': ['Canon Inc.', '佳能'],
        'sony': ['SONY CORPORATION', '索尼'], 'fujifilm': ['FUJI PHOTO FILM', '富士'],
        'panasonic': ['Panasonic Corporation', '松下'], 'leica': ['Leica Camera AG', '徕卡'],
        'hasselblad': ['Victor Hasselblad AB', '哈苏'], 'pentax': ['PENTAX Corporation', '宾得'],
        'omsystem': ['OM Digital Solutions', 'OM SYSTEM', '奥之心'], 'olympus': ['OLYMPUS CORPORATION', '奥林巴斯'],
        'ricoh': ['RICOH IMAGING COMPANY LTD.', '理光'], 'dji': ['大疆'], 'insta360': ['影石'],
        'apple': ['Apple Inc.', '苹果'], 'huawei': ['华为'], 'xiaomi': ['Redmi', 'POCO', '小米', '红米'],
        'oppo': ['OPPO Mobile'], 'vivo': ['iQOO', '维沃'], 'samsung': ['Samsung Electronics', '三星'],
        'oneplus': ['One Plus', '一加'], 'honor': ['荣耀'], 'realme': ['真我'],
        'motorola': ['motorola mobility llc', '摩托罗拉'], 'nokia': ['HMD Global', '诺基亚'],
        'google': ['谷歌'], 'asus': ['ASUSTeK COMPUTER INC.', '华硕'],
        'lenovo': ['联想'], 'zte': ['Nubia', '中兴', '努比亚'],
    }
    for brand, names in additional.items():
        for name in names:
            aliases[normalize(name)] = brand
    db = {'format': FORMAT, 'schema': SCHEMA, 'layout': LAYOUT, 'revision': revision,
          'assets': assets, 'brands': brands, 'maker_aliases': aliases, 'model_brand_aliases': {},
          'model_art': {}, 'model_rows': {}, 'partnerships': {}, 'partnership_defaults': {}}
    for row in catalog['artwork']:
        for key in finite_aliases(row['pattern']):
            db['model_art'][key] = Path(row['asset']).stem
            opaque = 'ModelRow-' + row['key']
            if opaque in assets:
                db['model_rows'][key] = opaque
    for row in catalog['partnerships']:
        for key in finite_aliases(row['pattern']):
            db['partnerships'][key] = Path(row['asset']).stem
        db['partnership_defaults'][row['brand']] = Path(row['asset']).stem
    return validate_database(db)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Build a data-only camera watermark database')
    parser.add_argument('--source', type=Path)
    parser.add_argument('--input', type=Path, help='Edited database-source.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision', type=int)
    args = parser.parse_args()
    if args.input:
        database = json.loads(args.input.read_text())
        if args.revision is not None:
            database['revision'] = args.revision
    elif args.source:
        database = initial_database(args.source, args.revision or 2026110501)
    else:
        parser.error('Choose --input or --source')
    result = publish(database, args.output)
    (args.output.parent / 'database-source.json').write_bytes(canonical(database) + b'\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))

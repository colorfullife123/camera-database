#!/usr/bin/env python3
"""Validate the public source catalog and GET each source's manifest/package."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import argparse
import datetime
import hashlib
import json
import re
import sys
import time

from database_protocol import canonical, read_envelope

ROOT = Path(__file__).resolve().parent.parent
HOSTS = {'gcore': 'gcore.jsdelivr.net', 'fastly': 'fastly.jsdelivr.net',
         'github': 'raw.githubusercontent.com'}


def validate_catalog(catalog):
    assert catalog['format'] == 'LiquidGlassCamera.UpdateSources' and catalog['schema'] == 1
    assert catalog['default'] == 'gcore'
    sources = catalog['sources']
    assert [source['key'] for source in sources] == ['gcore', 'fastly', 'github']
    for source in sources:
        address = urlsplit(source['root'])
        assert address.scheme == 'https' and address.netloc == HOSTS[source['key']]
        assert not address.query and not address.fragment
        expected = ('/colorfullife123/camera-database/main/database' if source['key'] == 'github'
                    else '/gh/colorfullife123/camera-database@main/database')
        assert address.path == expected
    return sources


def get_json(url, timeout):
    request = Request(url, headers={'User-Agent': 'CameraDatabase-MirrorCheck/1.5.3'})
    with urlopen(request, timeout=timeout) as response:
        raw = response.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError('Response exceeds 4 MiB')
    return json.loads(raw)


def probe(source, expected_revision, timeout, expected_hash=None):
    start = time.monotonic()
    result = {'source': source['key'], 'root': source['root'], 'ok': False}
    try:
        manifest = get_json(source['root'] + '/manifest.json', timeout)
        assert manifest['format'] == 'LiquidGlassCamera.Manifest'
        revision = manifest['revision']
        assert type(revision) is int and re.fullmatch(r'[1-9][0-9]{0,11}', str(revision))
        filename = f'database-{revision}.json'
        assert manifest['database'] == filename
        package = get_json(source['root'] + '/' + filename, timeout)
        database = read_envelope(package)
        payload = canonical(database)
        assert database['revision'] == revision
        assert database['schema'] == manifest['schema'] and database['layout'] == manifest['layout']
        assert hashlib.sha256(payload).hexdigest() == manifest['payload_sha256']
        assert manifest['payload_bytes'] == len(payload)
        assert manifest['assets'] == len(database['assets'])
        if revision == expected_revision and expected_hash is not None:
            assert manifest['payload_sha256'] == expected_hash, 'Mirror differs from checked-out repository'
        result.update(ok=True, revision=revision, sha256=manifest['payload_sha256'],
                      assets=len(database['assets']), behind_repository=revision < expected_revision)
    except Exception as error:
        result['error'] = f'{type(error).__name__}: {error}'
    result['seconds'] = round(time.monotonic() - start, 2)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog-only', action='store_true')
    parser.add_argument('--timeout', type=float, default=30)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    catalog = json.loads((ROOT / 'update-sources.json').read_text())
    sources = validate_catalog(catalog)
    if args.catalog_only:
        print('Validated 3 HTTPS update sources; default: gcore')
        return 0
    expected = json.loads((ROOT / 'database/manifest.json').read_text())
    expected_revision = expected['revision']
    with ThreadPoolExecutor(max_workers=len(sources)) as pool:
        results = list(pool.map(lambda source: probe(source, expected_revision, args.timeout,
                                                    expected['payload_sha256']), sources))
    report = {'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'repository_revision': expected_revision,
              'probe_location': 'execution environment; not a mainland ISP availability guarantee',
              'sources': results}
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(text)
    print(text)
    for result in results:
        if result.get('behind_repository'):
            print(f"::warning::{result['source']} is behind the repository; CDN caches may lag.")
    return 0 if all(result['ok'] for result in results) else 1


if __name__ == '__main__':
    sys.exit(main())

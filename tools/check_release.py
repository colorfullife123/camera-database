"""Reject inconsistent or corrupt releases before they are used as updates."""
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from database_protocol import canonical, envelope, read_envelope, validate_database

root=Path(__file__).resolve().parent.parent
db=validate_database(json.loads((root/'database-source.json').read_text()))
manifest=json.loads((root/'database/manifest.json').read_text())
assert manifest['format']=='LiquidGlassCamera.Manifest'
assert manifest['revision']==db['revision']
assert manifest['schema']==db['schema'] and manifest['layout']==db['layout']
assert manifest['database']==f'database-{db["revision"]}.json'
package=json.loads((root/'database'/manifest['database']).read_text())
assert canonical(read_envelope(package))==canonical(db)
assert package==envelope(db)
assert manifest['payload_sha256']==package['payload_sha256']
assert manifest['payload_bytes']==len(canonical(db))
print(f'Validated revision {db["revision"]}: {len(db["assets"])} PNG assets; manifest and package match source')

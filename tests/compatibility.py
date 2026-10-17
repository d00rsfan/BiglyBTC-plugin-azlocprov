"""Offline file/lookup contract using an official synthetic MMDB (never GeoLite)."""
import hashlib
import pathlib
import shutil
import subprocess
import sys
import tempfile
import zipfile

driver, module, fixture = map(pathlib.Path, sys.argv[1:])
assert hashlib.sha256(fixture.read_bytes()).hexdigest() == 'ff5a273c91d332bcfb4d808cc128c4f98cb59bb55f75931b64ff69022ddfa1bc'
root = pathlib.Path(tempfile.mkdtemp(prefix='biglybtc-location-'))
owned_module = root / 'plugin.so'
shutil.copyfile(module, owned_module)
owned_module.chmod(0o400)
module = owned_module
plugin = root / 'plugins' / 'LocationProvider'
plugin.mkdir(parents=True)
descriptor = b'plugin.id=azlocprov\nplugin.version=0.6.9\nplugin.name=Location Provider\n'
(plugin / 'plugin.properties').write_bytes(descriptor)
def run(*args, version='0.6.9', code=0):
    result = subprocess.run([str(driver), str(module), str(plugin), version, *args], capture_output=True)
    assert result.returncode == code, (args, result.returncode, result.stderr)
    return result.stdout

run('81.2.69.160', 'en', code=10)  # missing DB
(plugin / 'GeoLite2-Country.mmdb').write_bytes(b'corrupt')
run('81.2.69.160', 'en', code=10)
shutil.copyfile(fixture, plugin / 'GeoLite2-Country.mmdb')
assert run('81.2.69.160', 'en') == b'GB\tUnited Kingdom\n'
assert run('81.2.69.160', 'fr') == 'GB\tRoyaume-Uni\n'.encode()
assert run('2001:218::1', 'en') == b'JP\tJapan\n'
assert run('2001:218::1', 'ja') == 'JP\t日本\n'.encode()
run('127.0.0.1', 'en', code=10)
run('::1', 'en', code=10)
# Corrupt preferred version falls back. The unversioned DB is never changed.
(plugin / 'GeoLite2-Country_0.6.9.mmdb').write_bytes(b'bad preferred')
assert run('81.2.69.160', 'en').startswith(b'GB\t')
# Version exactly .1.1 must not use a versioned database.
(plugin / 'GeoLite2-Country.mmdb').unlink()
shutil.copyfile(fixture, plugin / 'GeoLite2-Country_0.1.1.mmdb')
run('81.2.69.160', 'en', version='0.1.1', code=10)
shutil.copyfile(fixture, plugin / 'GeoLite2-Country_0.6.9.mmdb')
assert run('81.2.69.160', 'en').startswith(b'GB\t')
# JAR resources remain available without extraction or Java bytecode execution.
with zipfile.ZipFile(plugin / 'azlocprov_0.6.9.jar', 'w', compression=zipfile.ZIP_DEFLATED) as jar:
    for size in ['18x12', '25x15']:
        jar.writestr(f'com/vuze/plugins/azlocprov/images/{size}/gb.png', b'fixture flag ' + size.encode())
originals = {p.name: (p.stat().st_ino, hashlib.sha256(p.read_bytes()).hexdigest())
    for p in plugin.iterdir() if p.is_file()}
assert run('flag', 'GB', '0') == b'fixture flag 18x12'
assert run('flag', 'gb', '1') == b'fixture flag 25x15'
assert run('flag', 'GB', '-1') == b'fixture flag 25x15'
images = plugin / 'images' / '18x12'
images.mkdir(parents=True)
(images / 'gb.png').write_bytes(b'external override')
assert run('flag', 'GB', '0') == b'external override'
(images / 'gb.png').unlink()
# Reject traversal, leave missing country/flag as absent, never invent a result.
run('flag', '..', '0', code=5)
run('flag', 'ZZ', '0', code=10)
for name, before in originals.items():
    p = plugin / name
    assert (p.stat().st_ino, hashlib.sha256(p.read_bytes()).hexdigest()) == before
assert (plugin / 'plugin.properties').read_bytes() == descriptor
print('PASS location IPv4/IPv6, locales, fallback, JAR/loose flags and original file identities:', root)

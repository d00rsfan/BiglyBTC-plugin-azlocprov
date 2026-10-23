# BiglyBTC-plugin-azlocprov

C++23 development port of Location Provider, original runtime ID **azlocprov**.
Original source: BiglySoftware/BiglyBT-plugin-azlocprov at
`8e8224030ac772fcc8fcb22e80954342d6a66be1`; LocationProviderImpl copyright2013
Azureus Software, Inc., GPL-2.0-or-later. No GeoIP database, flag collection or Java
bytecode is included in this repository.

The module reads an existing original plugin directory: preferred
`GeoLite2-Country_<java-version>.mmdb` when the original numeric version exceeds
0.1.1, otherwise/fallback `GeoLite2-Country.mmdb`. It reads flags from
`images/{18x12,25x15}` first, then matching existing `azlocprov_<java-version>.jar`
or `azlocprov.jar` resources. It never extracts or executes the Java JAR and never
writes original files. Localized country display names come from a host callback;
database English is the fallback. Native release and Java plugin versions differ.

Two additive opt-in operations support hosts that must distinguish unavailable
geography from a usable database with no matching country. Existing
`BT_LOCATION_LOOKUP` and `BT_LOCATION_FLAG` layouts and behavior are unchanged.
`BT_LOCATION_DATABASE_STATUS` (`0x1003`) returns `BT_OK` with `available=1` only
while the bound database remains usable; unavailable data returns `BT_NOT_FOUND`
with `available=0`. `BT_LOCATION_LOOKUP_CHECKED` (`0x1004`) returns `BT_IO` for
unavailable/unusable data and `BT_NOT_FOUND` for a usable lookup without a country.
Both operations require the current additive SDK header; the ABI and native
version remain 1 and 0.1.0 respectively.

The strict operations require an owned private database directory and a nonempty
owned regular database with one link, no group/world write permission, a 256 MiB
bound and stable inode/metadata. Readiness is checked rather than inferred from
an old successful lookup. Replace data atomically and rebind after installing a
previously missing database. No database is bundled, discovered or downloaded by
these operations. Hosts authenticate native module code before loading it and
provide the explicit data directory; this module is not a native-code sandbox.

Build/install the shared SDK from `d00rsfan/BiglyBTC` first. Dependencies are a
C++23 compiler, CMake>=3.25, libmaxminddb>=1.12.2 and libarchive>=3.8. Tests additionally
use ICU>=78.2 as a host locale service. Qt is not a module dependency.

```sh
python3 tests/fetch_fixture.py /tmp/biglybtc-location-data/GeoIP2-Country-Test.mmdb
cmake -S . -B /tmp/biglybtc-location-build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=/tmp/biglybtc-sdk \
  -DBIGLYBTC_MMDB_FIXTURE=/tmp/biglybtc-location-data/GeoIP2-Country-Test.mmdb
cmake --build /tmp/biglybtc-location-build -j2
ctest --test-dir /tmp/biglybtc-location-build --output-on-failure
```

The test fixture is MaxMind's synthetic database at
`0ee49278e35fd7bdf341ac236edbba20de1aceb9`, SHA256
`ff5a273c91d332bcfb4d808cc128c4f98cb59bb55f75931b64ff69022ddfa1bc`.
Its upstream repository supplies Apache2/MIT licenses. It is not production
geolocation data. Tests generate private profiles only, covering IPv4/IPv6,
locales, missing/corrupt databases, loose/JAR flags and preserved original inodes.

This is an experimental module, not a complete compatible plugin release. Normal
host discovery/UI, original Java dependency and broader locale/version edge-case
qualification, native asset fallback when no Java resources exist, tag-example
menus and production update trust remain pending. Do not use the development
installer against a live profile. Binary release publication is not enabled.

## Continuous integration

The workflow is [`.github/workflows/linux.yml`](.github/workflows/linux.yml). [View runs](https://github.com/d00rsfan/BiglyBTC-plugin-azlocprov/actions).

The workflow runs on GitHub-hosted `ubuntu-26.04` amd64 runners on pushes, pull requests, and manual dispatch. It installs the exact GCC16/libstdc++16 snapshot and pinned Ubuntu dependency packages declared in the workflow; no separately provisioned runner is needed. It checks the SDK/module and pinned synthetic MaxMind file compatibility. Build/test logs and installed package versions are retained as workflow artifacts. This CI does not publish a release or qualify other distributions.

The workflow pins SDK commit `5ea3fb7391a3e5df107754b5bba95492f19efd1b`; its [SDK contract run](https://github.com/d00rsfan/BiglyBTC/actions/runs/40010131879) passed. The host's GCC qualification covered 24 unique Statistics suites, including Country provider, binding, observed-byte and worker tests. This update does not claim a successful standalone run; its result is available on the Actions page above.

For future workflow changes, push using this repository's SSH URL (`git@github.com:d00rsfan/BiglyBTC-plugin-azlocprov.git`). HTTPS pushes authenticated with an OAuth token require the additional `workflow` scope to add or update workflow files. Viewing public Actions runs does not require that scope.

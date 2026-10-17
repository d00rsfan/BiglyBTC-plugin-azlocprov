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

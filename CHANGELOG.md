# Changelog

## [1.1.2](https://github.com/equinor/completor/compare/v1.1.1...v1.1.2) (2024-12-16)


### 🧹 Chores

* Bump python-multipart from 0.0.17 to 0.0.18 in the pip group across 1 directory ([#199](https://github.com/equinor/completor/issues/199)) ([4c93998](https://github.com/equinor/completor/commit/4c93998484072fd697928b82abc5844ebe2df220))

## [1.1.1](https://github.com/equinor/completor/compare/v1.1.0...v1.1.1) (2024-12-16)


### 🐛 Bug Fixes

* Additional wells on case file and schedule file should be untouched ([#200](https://github.com/equinor/completor/issues/200)) ([ebf0b33](https://github.com/equinor/completor/commit/ebf0b33b500c0e569df449cdf4f200ef4b249703))
* Similar well name is mixed while replacing schedule files ([#207](https://github.com/equinor/completor/issues/207)) ([88211f5](https://github.com/equinor/completor/commit/88211f5c9325ece0b599acc251da4e83516cf0fa))


### 🧹 Chores

* Docusaurus dependencies ([#206](https://github.com/equinor/completor/issues/206)) ([26dce1d](https://github.com/equinor/completor/commit/26dce1db412b195b6592b4f2ee1a1ae25667c536))
* Relax dependencies ([#205](https://github.com/equinor/completor/issues/205)) ([ca79c34](https://github.com/equinor/completor/commit/ca79c3488a0a92432e391edca89e154b685eeca8))

## [1.1.0](https://github.com/equinor/completor/compare/v1.0.1...v1.1.0) (2024-11-25)


### ✨ Features

* Make completor compatible with pandas 2.1.4 ([d74d019](https://github.com/equinor/completor/commit/d74d019a6f58b8777dd6f49607e9716ddd60f14d))
* Make completor compatible with Pandas 2.1.4 ([#194](https://github.com/equinor/completor/issues/194)) ([d74d019](https://github.com/equinor/completor/commit/d74d019a6f58b8777dd6f49607e9716ddd60f14d))


### 🐛 Bug Fixes

* Revert after refactor ([#192](https://github.com/equinor/completor/issues/192)) ([965222d](https://github.com/equinor/completor/commit/965222d7c2f37cf7e394741a0918f563abcd6902))


### 🧹 Chores

* Update poetry.lock ([#198](https://github.com/equinor/completor/issues/198)) ([7a20a5b](https://github.com/equinor/completor/commit/7a20a5b96fd7a74e7ec7f984332aeb8d863acd98))

## [1.0.1](https://github.com/equinor/completor/compare/v1.0.0...v1.0.1) (2024-11-15)


### 🐛 Bug Fixes

* Ert dependency ([#189](https://github.com/equinor/completor/issues/189)) ([49a77b5](https://github.com/equinor/completor/commit/49a77b5bbfa17b2820eb2742d3106c8d1c9113a2))
* Partially initialized module ([#188](https://github.com/equinor/completor/issues/188)) ([df17a3c](https://github.com/equinor/completor/commit/df17a3c528da1c8c3d703abda3b39c0fc67fad57))
* Replace shortened imports with full versions ([df17a3c](https://github.com/equinor/completor/commit/df17a3c528da1c8c3d703abda3b39c0fc67fad57))


### 🧹 Chores

* Improved error message ([#185](https://github.com/equinor/completor/issues/185)) ([505e941](https://github.com/equinor/completor/commit/505e941392225b1c6aaf7ba2dbdd69e055b6028c))
* **SNYK:** Upgrade ([#186](https://github.com/equinor/completor/issues/186)) ([d07ae95](https://github.com/equinor/completor/commit/d07ae95793b03034183f61c3cf627dfa8a89d736))
* **SNYK:** Upgrade ([#187](https://github.com/equinor/completor/issues/187)) ([75a40ff](https://github.com/equinor/completor/commit/75a40ffb2767d4e9ac078ffd68e556c3ba869127))
* Update documentation dependency ([#191](https://github.com/equinor/completor/issues/191)) ([5fb1e05](https://github.com/equinor/completor/commit/5fb1e05c72e5a19c038194bb48a0496e5aca1351))


### 🧪 Tests

* Add tests for [#163](https://github.com/equinor/completor/issues/163) ([#165](https://github.com/equinor/completor/issues/165)) ([475d149](https://github.com/equinor/completor/commit/475d14959106ecc00aea61ed9f537b2c7ce195e6))

## [1.0.0](https://github.com/equinor/completor/compare/v0.1.3...v1.0.0) (2024-10-30)


### 👷 Continuous Integration

* Allow release-please to bump major versions! ([#182](https://github.com/equinor/completor/issues/182)) ([6dfb5de](https://github.com/equinor/completor/commit/6dfb5de1ad2daf2d96abbedcfe999a9cace1e614))


### 🐛 Bug Fixes

* Error when non-active wells are specified with separate WELSPECS ([#163](https://github.com/equinor/completor/issues/163)) ([92bf4b7](https://github.com/equinor/completor/commit/92bf4b7f57bd8c24859b06d9280fdb682864470f))
* Explicitly opt in to future pandas option "no-silent-downcasting" ([#175](https://github.com/equinor/completor/issues/175)) ([2f9cb3d](https://github.com/equinor/completor/commit/2f9cb3d118bc64fd42d427c484495319e109e782))
* Handle pandas deprecation warnings ([#156](https://github.com/equinor/completor/issues/156)) ([e5d101f](https://github.com/equinor/completor/commit/e5d101f1ef534608f9b733abe60f289beea3f941))
* Output keyword ordering ([#172](https://github.com/equinor/completor/issues/172)) ([7499aaa](https://github.com/equinor/completor/commit/7499aaa4a875e4d9f27c1a8c528fa888a4943f36))
* Output width limit ([#167](https://github.com/equinor/completor/issues/167)) ([0a184ef](https://github.com/equinor/completor/commit/0a184ef4dd785818590da04df56fa413e53a509b))
* **security:** Update dependencies for documentation build ([#135](https://github.com/equinor/completor/issues/135)) ([5c51da4](https://github.com/equinor/completor/commit/5c51da4f8c9566aa4cbd51ab2ac891273ebbfb53))
* Testing of string building ([#157](https://github.com/equinor/completor/issues/157)) ([d10a399](https://github.com/equinor/completor/commit/d10a3995e108c65365eea0cbd61d0cce70d0faa9))


### 🧹 Chores

* Bump aiohttp from 3.9.5 to 3.10.2 in the pip group across 1 directory ([#148](https://github.com/equinor/completor/issues/148)) ([e3cfc70](https://github.com/equinor/completor/commit/e3cfc701fcef8904879cc18ae69609277b07ae58))
* Bump certifi from 2024.6.2 to 2024.7.4 in the pip group across 1 directory ([#129](https://github.com/equinor/completor/issues/129)) ([75d0dce](https://github.com/equinor/completor/commit/75d0dce54a7e7c8009075ee963986651cd03fa21))
* Bump cryptography from 43.0.0 to 43.0.1 in the pip group across 1 directory ([#151](https://github.com/equinor/completor/issues/151)) ([7be0edb](https://github.com/equinor/completor/commit/7be0edbe40a72bb6c50fed6c6239181898a27276))
* Bump http-proxy-middleware from 2.0.6 to 2.0.7 in /documentation in the npm_and_yarn group across 1 directory ([#174](https://github.com/equinor/completor/issues/174)) ([b23703b](https://github.com/equinor/completor/commit/b23703b8d6a60f5e90bd3e12bba16cd46079e095))
* Bump starlette from 0.38.5 to 0.40.0 in the pip group across 1 directory ([#171](https://github.com/equinor/completor/issues/171)) ([d50c73c](https://github.com/equinor/completor/commit/d50c73c2876373064b4cac97ed5addcdb5842abb))
* Bump the npm_and_yarn group across 1 directory with 3 updates ([#155](https://github.com/equinor/completor/issues/155)) ([dbb331f](https://github.com/equinor/completor/commit/dbb331fcb7fcb692faae0a57bcfbf490a1dd61a0))
* Bump webpack from 5.93.0 to 5.94.0 in /documentation in the npm_and_yarn group across 1 directory ([#144](https://github.com/equinor/completor/issues/144)) ([d0a9275](https://github.com/equinor/completor/commit/d0a92754c4db9145b8c0a057ee9e6546308e42db))
* Class-structure ([#136](https://github.com/equinor/completor/issues/136)) ([9e5fae2](https://github.com/equinor/completor/commit/9e5fae2be48daeae24fdd3a1a551eb920a01fe9a))
* Make more conventional commit formats not hidden from release-please ([#176](https://github.com/equinor/completor/issues/176)) ([a5fc75a](https://github.com/equinor/completor/commit/a5fc75a845fb3cfbaa0cb34c5d34c544835d998c))
* Make pdf figure context managed ([#138](https://github.com/equinor/completor/issues/138)) ([5681387](https://github.com/equinor/completor/commit/5681387e353cd24213244d5e13a5e67f8a46f5ac))
* Migrate to `importlib` ([#177](https://github.com/equinor/completor/issues/177)) ([3b25258](https://github.com/equinor/completor/commit/3b2525850237572461211d0e0a3122f69766afdb))
* Recast error to be more informative. ([#116](https://github.com/equinor/completor/issues/116)) ([668ce0c](https://github.com/equinor/completor/commit/668ce0cff869fe12ecc3ba7f347c4401c8f02650))
* Remove TODO 142 ([#150](https://github.com/equinor/completor/issues/150)) ([9d80518](https://github.com/equinor/completor/commit/9d80518f4f045cc40813265c190f44b03b359dcd))


### 📝 Documentation

* Improve docstrings with too much find and replace ([#178](https://github.com/equinor/completor/issues/178)) ([ff2871b](https://github.com/equinor/completor/commit/ff2871be59d07ccc81193c0674d7d3ed790f291a))


### ⚡️ Performance Improvements

* Use list append when string building ([#154](https://github.com/equinor/completor/issues/154)) ([db7ed5c](https://github.com/equinor/completor/commit/db7ed5cac214108b1de7eb03eca8c10632d68b70))


### ♻️ Code Refactoring

* `main.py` ([#132](https://github.com/equinor/completor/issues/132)) ([b1343a1](https://github.com/equinor/completor/commit/b1343a18a939b549f1f6a2d40399944c94157d01))
* Constants content ([#139](https://github.com/equinor/completor/issues/139)) ([e1b1984](https://github.com/equinor/completor/commit/e1b19847031a9327c2d02883803c0dcc67c0fbb7))
* First pass `WellSchedule` class ([#134](https://github.com/equinor/completor/issues/134)) ([9f82069](https://github.com/equinor/completor/commit/9f820694e0130d16a89074902bb4755ccc45ea48))
* Naming convention ([#143](https://github.com/equinor/completor/issues/143)) ([5a2e33d](https://github.com/equinor/completor/commit/5a2e33d91646506388e27715e763278bc7da287f))
* Refactor `create_output.py` ([#140](https://github.com/equinor/completor/issues/140)) ([2fd5cc6](https://github.com/equinor/completor/commit/2fd5cc65acf18d7b5ebb91ffe01d4554df8eb32f))
* Remove PVT Model ([#181](https://github.com/equinor/completor/issues/181)) ([d677e95](https://github.com/equinor/completor/commit/d677e95be49b7c649bae02efe2241df8936d88ba))
* Rename `utils.py` in tests to `utils_for_tests.py` ([#141](https://github.com/equinor/completor/issues/141)) ([e589bef](https://github.com/equinor/completor/commit/e589befe111b1cf19ca5644280fa4d2a85d955ed))
* Rename aliased imports `val` & `po` to their non-aliased names ([#137](https://github.com/equinor/completor/issues/137)) ([5b4d1fc](https://github.com/equinor/completor/commit/5b4d1fca2ae5c94113f4952513094ef51ecafaee))
* Rename constants ([#130](https://github.com/equinor/completor/issues/130)) ([d7f4107](https://github.com/equinor/completor/commit/d7f410742280cc858c0fed8cd4cc07f2f9b145eb))
* Structure ([#131](https://github.com/equinor/completor/issues/131)) ([d8fffc4](https://github.com/equinor/completor/commit/d8fffc411dbb1b2868d14055725c8e9ec3effea6))


### 🧪 Tests

* Add stricter file assertion test ([#153](https://github.com/equinor/completor/issues/153)) ([83778d9](https://github.com/equinor/completor/commit/83778d92eb776f1c59620d9ffb49dfd0b3168351))

## [0.1.3](https://github.com/equinor/completor/compare/v0.1.2...v0.1.3) (2024-07-04)


### 🧹 Chores

* Bump ws from 7.5.9 to 7.5.10 in /documentation in the npm_and_yarn group across 1 directory ([#104](https://github.com/equinor/completor/issues/104)) ([2e3e82a](https://github.com/equinor/completor/commit/2e3e82a1a39d941931697956edd15f5ef6111c0d))
* Downgrade pandas ([#118](https://github.com/equinor/completor/issues/118)) ([a8a7c2e](https://github.com/equinor/completor/commit/a8a7c2ed036c1a7553a9553986fb250947f907ea))
* **main:** release 0.1.3 ([3564fe7](https://github.com/equinor/completor/commit/3564fe737d6f3643ed7ed539de23d7437fd3d699))
* **main:** Release 0.1.3 ([#124](https://github.com/equinor/completor/issues/124)) ([3564fe7](https://github.com/equinor/completor/commit/3564fe737d6f3643ed7ed539de23d7437fd3d699))
* Release 0.1.3 ([#123](https://github.com/equinor/completor/issues/123)) ([b97787e](https://github.com/equinor/completor/commit/b97787e074f43148f098ee10cca8709e1d12d5d7))

## [0.1.3](https://github.com/equinor/completor/compare/v0.1.2...v0.1.3) (2024-07-03)


### Miscellaneous Chores

* Release 0.1.3 ([#123](https://github.com/equinor/completor/issues/123)) ([b97787e](https://github.com/equinor/completor/commit/b97787e074f43148f098ee10cca8709e1d12d5d7))

## [0.1.2](https://github.com/equinor/completor/compare/v0.1.1...v0.1.2) (2024-06-18)


### Bug Fixes

* Fix mypy in `pre-commit-config.yaml` ([#102](https://github.com/equinor/completor/issues/102)) ([7432aca](https://github.com/equinor/completor/commit/7432aca0556289a16d0426331b350b99bc9c4239))


### Documentation

* Fix URL ([#105](https://github.com/equinor/completor/issues/105)) ([d72df4b](https://github.com/equinor/completor/commit/d72df4b513b60ee805f5a8148bee04789d465cf6))

## [0.1.1](https://github.com/equinor/completor/compare/v0.1.0...v0.1.1) (2024-06-18)


### Bug Fixes

* Header variable names ([#98](https://github.com/equinor/completor/issues/98)) ([fdf41cd](https://github.com/equinor/completor/commit/fdf41cd05758ee5a8b8d68339ffa4b6af3b5ff44))

## [0.1.0](https://github.com/equinor/completor/compare/v0.0.1...v0.1.0) (2024-06-13)


### Features

* Read wsegvalv table from schedule ([#78](https://github.com/equinor/completor/issues/78)) ([7372e2f](https://github.com/equinor/completor/commit/7372e2f3698d8476df541737ec72f60bafee2a28))
* Replace setuptools with poetry ([#55](https://github.com/equinor/completor/issues/55)) ([d55db32](https://github.com/equinor/completor/commit/d55db323232f3417b817d9b127bb6fa99759c36e))


### Bug Fixes

* Loglevel 0 bug ([#43](https://github.com/equinor/completor/issues/43)) ([a65c526](https://github.com/equinor/completor/commit/a65c52653a83e027d171e126b301b83a36b651ba))
* Path parsing ([#32](https://github.com/equinor/completor/issues/32)) ([74fcf11](https://github.com/equinor/completor/commit/74fcf11c597557e1fc9215ac6e5dcd6a83c47ff4))
* Revert clean up of '/' ([#46](https://github.com/equinor/completor/issues/46)) ([38322b4](https://github.com/equinor/completor/commit/38322b4b5833fa15b138305579322d7ec9572390))
* Versioning ([#58](https://github.com/equinor/completor/issues/58)) ([9c60333](https://github.com/equinor/completor/commit/9c603337307989656c0a9c915a7ea7d417f3928a))


### Documentation

* Add ICV on documentations ([#63](https://github.com/equinor/completor/issues/63)) ([ee7860b](https://github.com/equinor/completor/commit/ee7860b000fd8bd15440e9f19c09384bbcb7f591))
* Add Security policy ([#27](https://github.com/equinor/completor/issues/27)) ([f5255de](https://github.com/equinor/completor/commit/f5255de00b86d521e1497c028129c14177b9baa6))
* Fix error message in Completor ([#70](https://github.com/equinor/completor/issues/70)) ([8570918](https://github.com/equinor/completor/commit/85709180c773fbed30670ed95736ac6521c6e586))
* Make documentation more simulator-agnostic ([#66](https://github.com/equinor/completor/issues/66)) ([f62a135](https://github.com/equinor/completor/commit/f62a135a278197178b8c8989c77528cbd2e40502))
* Remove external parties ([#73](https://github.com/equinor/completor/issues/73)) ([52827ae](https://github.com/equinor/completor/commit/52827ae19f5209ea57f7b632501d84444146b51d))
* Rename Code of Conduct file ([#30](https://github.com/equinor/completor/issues/30)) ([d4ff0ad](https://github.com/equinor/completor/commit/d4ff0adc7d0252385b58b05fa09a800894c2f6c8))
* Revise docstring style ([#87](https://github.com/equinor/completor/issues/87)) ([3e31740](https://github.com/equinor/completor/commit/3e3174086f3ff7d725c69222b007e7d4cb011935))
* Update README to include explicit reference to pre-commit ([#7](https://github.com/equinor/completor/issues/7)) ([d409489](https://github.com/equinor/completor/commit/d40948966edd8e23c4d520075a5ad603d253cfd9))

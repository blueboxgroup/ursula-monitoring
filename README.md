# ursula-monitoring

Monitoring and Logging modules and tools used by Ursula

## Sensu

All files in `sensu/plugins` should have executable bit set.

## Building packages

Package version numbers are derived from annotated tags with `git describe`.

General build procedure:

1. Use `git checkout` to point HEAD to desired commit.
2. Use `git tag -a 'vX.Y.Z' -m'version X.Y.Z'` to create an annotated tag at that commit.
3. To build packages, call `make`.
4. To upload to packagecloud.io, `make upload PACKAGECLOUD_REPO=username/repo` (or set `PACKAGECLOUD_REPO` in your environment).

Requires [fpm](https://github.com/jordansissel/fpm) to build packages and the [package_cloud](https://rubygems.org/gems/package_cloud) gem to upload to packagecloud.io.

## License

All original work released under Apache 2.0 license. Note: this repository does contain vendored plugins and checks that may be licensed differently.

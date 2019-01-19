# ursula-monitoring

This repo contains monitoring and logging modules used by Ursula and Site Controller.


## Updates and tags

Place updated sensu plugin scripts into the `sensu/plugins/` directory, ensuring the files have the executable bit set.

After committing your updates, create an annotated tag using the next available version number.  The latest tag will be used as the version number when building either a DEB package or downloading the tarball.

To create a new annotated tag:
```
git tag -a 'X.Y.Z' -m'version X.Y.Z'
```


## Deployment

You can deploy to Ursula from a tarball, and to Site Controller from a Debian package.


### Tarball deployment

Select the tagged version you want, and download the tar.gz file.  This can be uploaded to your file mirror as needed for deployment.


### Package deployment

To deploy from a debian package, you build the package, and upload to the repo(s) used by your system.


#### Docker package build


First you need to build a local docker image named `ursula-monitoring`.  You'll use this in the next step to build the DEB package.  Make sure you have the desired annotated tag checked out, as this is how the package version number will be set.

```
cd ursula-monitoring/
docker build -t ursula-monitoring .
```

Now you just run this command, which builds the package within the container and makes it available under the `build/` subdirectory.
```
docker run -v $PWD:/ursula-monitoring ursula-monitoring
```

As stated above, the new debian package file is in the `build/` directory.  You can upload that to the mirrors used by your system to deploy.


#### Manual package build

If you'd like to build the package outside of docker, you can. However, the system requires [fpm](https://github.com/jordansissel/fpm) to build packages and the [package_cloud](https://rubygems.org/gems/package_cloud) gem to upload to packagecloud.io.

1. Checkout desired version.
   Use `git checkout` to point HEAD to desired commit.
2. Ensure desired tag (package version).
   If you need to create a new annotated tag, use `git tag -a 'X.Y.Z' -m'version X.Y.Z'`.
3. To build the package, call `make`.
4. To upload to packagecloud.io, `make upload PACKAGECLOUD_REPO=username/repo` (or set `PACKAGECLOUD_REPO` in your environment).



## License

All original work released under Apache 2.0 license. Note: this repository does contain vendored plugins and checks that may be licensed differently.

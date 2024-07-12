# rapid-watershed-delineation

A docker image and fork of @nazmussazib's [Rapid Watershed Delineation](https://github.com/nazmussazib/RapidWatersheDelineation) project, for use in [Model My Watershed](https://github.com/WikiWatershed/model-my-watershed).

[![Docker Repository on GitHub Container Registry](https://ghcr-badge.egpl.dev/WikiWatershed/rwd/latest_tag?color=%2344cc11&ignore=sha256*%2Clatest&label=version)](https://github.com/WikiWatershed/rapid-watershed-delineation/pkgs/container/rwd)
[![Apache V2 License](https://img.shields.io/badge/license-Apache%20V2-blue.svg)](https://github.com/wikiwatershed/rapid-watershed-delineation/blob/develop/LICENSE)

### Quick Start

```
docker run --rm -ti ghcr.io/wikiwatershed/rwd
```

### Getting started
* Define environment variables (see below)
* Run `./scripts/update.sh`
* Run `./scripts/server.sh`

#### Linux & Docker for Mac on macOS
* Run `curl http://localhost:5000/rwd/39.892986/-75.276639`

#### Docker Machine on macOS
* Find the IP of the default VM using `docker-machine ip default`
* Run `curl http://<default_vm_ip>:5000/rwd/39.892986/-75.276639`

### Environment Variables

| Name       | Description                          | Example                     |
| ---------- | ------------------------------------ | --------------------------- |
| `RWD_DATA` | Path to RWD data                     | `/media/passport/rwd-nhd`   |

### RWD Data

Folder structure:

```
> tree -L 2 /media/passport/rwd-nhd/
|-- drb
|   |-- Main_Watershed
|   `-- Subwatershed_ALL
`-- nhd
    |-- Main_Watershed
    |-- Subwatershed_ALL
```

### Running inside Model My Watershed

To run RWD inside the MMW application during development, follow these
instructions.

In the MMW project:

```
# Change the rwd_host setting to 10.0.2.2
vim deployment/ansible/roles/model-my-watershed.rwd/defaults/main.yml
vagrant reload worker --provision
```

Note that `10.0.2.2` should point to your host. Verify this by running
`route -n` inside the worker VM. It should be the default gateway.
For Mac OS X, this IP should be the result of `docker-machine ip`.

Then in this project, run:

```
./scripts/server.sh
```

## Deployments

To create a new release, use the following git commands:

``` bash
$ git flow release start 0.1.0
$ vim CHANGELOG.md
$ vim setup.py
$ git commit -m "0.1.0"
$ git flow release finish -p 0.1.0
```

Afterward, push your `develop` and `master` branches to remote using:

```
$ git push origin develop:develop
$ git push origin master:master
```

## RWD API

### Request

| Name | Method | Description |
| ---- | ------ | ----------- |
| /rwd/lat/lng | GET | Run RWD for DRB for client-supplied `<lat>` & `<lng>` coordinates. |
| /rwd-nhd/lat/lng | GET | Run RWD for NHD for client-supplied `<lat>` & `<lng>` coordinates. |

### Parameters

| Name | Type | Required/Optional | Description |
| ---- | ---- | ----------------- | ----------- |
| simplify | number | optional | Simplify tolerance for response GeoJSON. Request unsimplified shape with `simplify=0`. Defaults to `0.0001` for DRB and is [derived from the shape's area](https://github.com/WikiWatershed/rapid-watershed-delineation/blob/1.2.1/src/api/main.py#L195) for NHD when not supplied. |
| maximum_snap_distance | number | optional | Maximum distance to snap input point. Defaults to `10000` when not supplied. |

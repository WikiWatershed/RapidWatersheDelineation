# rapid-watershed-delineation

A docker image and fork of @nazmussazib's [Rapid Watershed Delineation](https://github.com/nazmussazib/RapidWatersheDelineation) project, for use in [Model My Watershed](https://github.com/WikiWatershed/model-my-watershed).

[![Travis CI](https://api.travis-ci.org/WikiWatershed/docker-rwd.svg "Build Status on Travis CI")](https://travis-ci.org/WikiWatershed/docker-rwd/)
[![Docker Repository on Quay.io](https://quay.io/repository/wikiwatershed/rwd/status "Docker Repository on Quay.io")](https://quay.io/repository/wikiwatershed/rwd)
[![Apache V2 License](http://img.shields.io/badge/license-Apache%20V2-blue.svg)](https://github.com/wikiwatershed/rapid-watershed-delineation/blob/develop/LICENSE)

### Getting started
* Define environment variables (see below)
* Run `./scripts/update.sh`
* Run `./scripts/server.sh`

#### Linux
* Run `curl http://localhost:5000/rwd/-75.276639/39.892986`

#### OS X
* Find the IP of the default VM using `docker-machine ip default`
* Run `curl http://<default_vm_ip>:5000/rwd/-75.276639/39.892986`

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

## Deployments

To create a new release, use the following git commands:

``` bash
$ git flow release start 0.1.0
$ vim CHANGELOG.md
$ vim setup.py
$ vim src/api/main.py
$ git commit -m "0.1.0"
$ git flow release publish 0.1.0
$ git flow release finish 0.1.0
$ git push --tags
```

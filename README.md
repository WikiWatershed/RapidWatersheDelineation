# rapid-watershed-delineation

A docker image and fork of @nazmussazib's [Rapid Watershed Delineation](https://github.com/nazmussazib/RapidWatersheDelineation) project, for use in [Model My Watershed](https://github.com/WikiWatershed/model-my-watershed).

[![Travis CI](https://api.travis-ci.org/WikiWatershed/rapid-watershed-delineation.svg "Build Status on Travis CI")](https://travis-ci.org/WikiWatershed/rapid-watershed-delineation/)
[![Docker Repository on Quay.io](https://quay.io/repository/wikiwatershed/rwd/status "Docker Repository on Quay.io")](https://quay.io/repository/wikiwatershed/rwd)
[![Apache V2 License](https://img.shields.io/badge/license-Apache%20V2-blue.svg)](https://github.com/wikiwatershed/rapid-watershed-delineation/blob/develop/LICENSE)

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
$ vim src/api/main.py
$ git commit -m "0.1.0"
$ git flow release publish 0.1.0
$ git flow release finish 0.1.0
$ git push --tags
```

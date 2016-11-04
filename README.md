# rapid-watershed-delineation

A fork of @nazmussazib's [Rapid Watershed Delineation](https://github.com/nazmussazib/RapidWatersheDelineation) project, for use in [Model My Watershed](https://github.com/WikiWatershed/model-my-watershed).

A Docker container of this repo and it's dependencies is available at [docker-rwd](https://github.com/WikiWatershed/docker-rwd).

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

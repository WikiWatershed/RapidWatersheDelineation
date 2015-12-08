# rapid-watershed-delineation

## Deployments

Deployments to PyPi are handled through [Travis-CI](https://travis-ci.org/WikiWatershed/rapid-watershed-delineation). The following git flow commands approximate a release using Travis:

``` bash
$ git flow release start 0.1.0
$ vim CHANGELOG.md
$ vim setup.py
$ git commit -m "0.1.0"
$ git flow release publish 0.1.0
$ git flow release finish 0.1.0
```

To kick off the deployment, you'll still need to push the local tags remotely
`git push --tags`

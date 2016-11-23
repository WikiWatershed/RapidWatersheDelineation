## 1.1.1
- Store input point properties "Lat" and "Lon" in their original LatLng projection
- Simplify output NHD shapes in proportion to their area

## 1.1.0
- Add `rwd-nhd` api endpoint to delineate points using NHD data (ie points beyond the Delaware River Basin
- Update data file paths to `/opt/rwd-data/nhd` and `/opt/rwd-data/drb` for the new NHD data set and the old DRB data set respectively

## 1.0.1

- Merge upstream changes to fix invalid watershed GeoJSON

## 1.0.0

- Merge upstream changes to speed up RWD functions
- Simplify watershed shapes
- Include stack trace in web API responses
- Add 404 page to web API

## 0.3.0

- Preserve input and snapped points in API results

## 0.2.2

- Fix bug for output directory when snapping=0

## 0.2.1

- Add logging

## 0.2.0

- Conform to PEP8 code style
- Add complete RWD python requirements
- Add Flask HTTP API
- Remove support for Travis CI

## 0.1.2

- Change password.

## 0.1.1

- Initial development release.

## 0.1.0

- Initial development release.

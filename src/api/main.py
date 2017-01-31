import logging
import os.path
import shutil
import json
import tempfile
import uuid
import traceback

from math import floor
from subprocess import call

import ogr
from flask import Flask, jsonify, request, render_template

from rwd_drb import Rapid_Watershed_Delineation
from rwd_nhd import NHD_Rapid_Watershed_Delineation


VERSION = '1.2.0'

# Keep in sync with src/mmw/js/src/draw/utils.js in model-my-watershed.
MAX_AREA_KM2 = 112700

app = Flask(__name__)

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())


def error_response(error_message, stack_trace):
    response = jsonify({
        'error': error_message,
        'stackTrace': stack_trace
    })
    return response, 400


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/version.txt', methods=['GET'])
def version_route():
    return '{}\n'.format(VERSION)


@app.route('/rwd/<lat>/<lon>', methods=['GET'])
def run_rwd(lat, lon):
    """
    Runs RWD for lat/lon and returns the GeoJSON
    for the computed watershed boundary, outlet point
    and snapped point.
    """
    snapping = request.args.get('snapping', '1')
    maximum_snap_distance = request.args.get('maximum_snap_distance', '10000')
    simplify = str(request.args.get('simplify', 0.0001))

    num_processors = '1'
    data_path = '/opt/rwd-data/drb'

    # Create a temporary directory to hold the output.
    output_path = tempfile.mkdtemp()

    try:
        Rapid_Watershed_Delineation.Point_Watershed_Function(
            lon,
            lat,
            snapping,
            maximum_snap_distance,
            data_path,
            'Delaware_Ocean_stream_dissolve',
            'delaware_gw_5000_diss',
            'Delaware_5000_GW_ID.txt',
            'Delaware_Missing_Coast_Watershed',
            num_processors,
            '/opt/taudem',
            '/usr/local/bin/',
            output_path,
        )

        # The Watershed and input coordinates (possibly snapped to stream)
        # are written to disk.  Load them and convert to json
        wshed_shp_path = os.path.join(output_path, 'New_Point_Watershed.shp')
        input_shp_path = os.path.join(output_path, 'New_Outlet.shp')

        output = {
            'watershed': load_json(wshed_shp_path, output_path, simplify),
            'input_pt': load_json(input_shp_path, output_path)
        }

        shutil.rmtree(output_path)
        return jsonify(**output)

    except Exception as exc:
        log.exception('Error running Point_Watershed_Function')
        stack_trace = traceback.format_exc()
        return error_response(exc.message, stack_trace)


@app.route('/rwd-nhd/<lat>/<lon>', methods=['GET'])
def run_rwd_nhd(lat, lon):
    """
    Runs RWD NHD for lat/lon and returns the GeoJSON
    for the computed watershed boundary, outlet point
    and snapped point.
    """
    snapping = request.args.get('snapping', '1')
    maximum_snap_distance = request.args.get('maximum_snap_distance', '10000')
    num_processors = '1'
    data_path = '/opt/rwd-data/nhd'

    # Create a temporary directory to hold the output.
    output_path = tempfile.mkdtemp()

    try:
        NHD_Rapid_Watershed_Delineation.Point_Watershed_Function(
            float(lon),
            float(lat),
            snapping,
            maximum_snap_distance,
            data_path,
            'gwgrid.tif',
            'gwmaster',
            num_processors,
            '/opt/taudem',
            '/usr/local/bin/',
            output_path,
        )

        # The Watershed and input coordinates (possibly snapped to stream)
        # are written to disk.  Load them and convert to json
        wshed_shp_path = os.path.join(output_path, 'New_Point_Watershed.shp')
        input_shp_path = os.path.join(output_path, 'New_Outlet.shp')

        simplify = str(request.args.get(
            'simplify',
            create_simplify_tolerance_by_area(wshed_shp_path)))

        output = {
            'watershed': load_json(wshed_shp_path, output_path, simplify,
                                   # From NAD83 / Conus Albers to WGS 84 Latlong
                                   from_epsg=5070, to_epsg=4326),
            'input_pt': load_json(input_shp_path, output_path,
                                  # From NAD83 / Conus Albers to WGS 84 Latlong
                                  from_epsg=5070, to_epsg=4326)
        }

        shutil.rmtree(output_path)
        return jsonify(**output)

    except Exception as exc:
        log.exception('Error running Point_Watershed_Function')
        stack_trace = traceback.format_exc()
        return error_response(exc.message, stack_trace)


def load_json(shp_path, output_path, simplify_tolerance=None,
              from_epsg=None, to_epsg=None):
    name = '%s.json' % uuid.uuid4().hex
    output_json_path = os.path.join(output_path, name)
    ogr_cmd = ['ogr2ogr', output_json_path, shp_path, '-f', 'GeoJSON']

    # Simplify the polygon as we convert to JSON if there
    # is a tolerance setting
    cmd = ogr_cmd + ['-simplify', simplify_tolerance] if simplify_tolerance \
        else ogr_cmd

    cmd = cmd + ['-t_srs', "EPSG: " + str(from_epsg),
                 '-a_srs', "EPSG: " + str(to_epsg)] \
        if from_epsg and to_epsg else cmd

    call(cmd)

    try:
        with open(output_json_path, 'r') as output_json_file:
            output = json.load(output_json_file)
            return output
    except:
        log.exception('Could not get GeoJSON from output.')
        return None


def get_shp_area(shp_file_path):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataSource = driver.Open(shp_file_path, 1)
    layer = dataSource.GetLayer()
    return layer[0].GetField('Area_km2')


def linear_interpolate(value, lo, hi):
    return value * (hi - lo) + lo


def create_simplify_tolerance_by_area(shp_file_path):
    area = get_shp_area(shp_file_path)
    return floor(linear_interpolate(min(1, area / MAX_AREA_KM2), 1, 2000))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

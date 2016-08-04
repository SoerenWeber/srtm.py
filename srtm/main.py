# -*- coding: utf-8 -*-

# Copyright 2013 Tomo Krajina
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pdb

import json     as mod_json
import os       as mod_os
import os.path  as mod_path

from . import data      as mod_data
from . import utils     as mod_utils
from . import retriever as mod_retriever

SRTMGL1_URL = 'http://e4ftl01.cr.usgs.gov/SRTM/SRTMGL1.003/2000.02.11/'
SRTM1_URL = 'http://dds.cr.usgs.gov/srtm/version2_1/SRTM1/'
SRTM3_URL = 'http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/'

package_location = mod_data.__file__[: mod_data.__file__.rfind(mod_path.sep)]
DEFAULT_LIST_JSON = package_location + mod_os.sep + 'list.json'


def get_data(srtmgl1=True, srtm1=True, srtm3=True, leave_zipped=False, file_handler=None,
             use_included_urls=True, http_user=None, http_password=None):
    """
    Get the utility object for querying elevation data.

    All data files will be stored in localy (note that it may be 
    gigabytes of data so clean it from time to time).

    On first run -- all files needed url will be stored and for every next 
    elevation query if the SRTM file is not found it will be retrieved and 
    saved.

    If you need to change the way the files are saved locally (for example if 
    you need to save them locally) -- change the file_handler. See 
    srtm.main.FileHandler.

    If leave_zipped is True then files will be stored locally as compressed 
    zip files. That means less disk space but more computing space for every 
    file loaded.

    If use_included_urls is True urls to SRTM files included in the library 
    will be used. Set to false if you need to reload them on first run.

    With srtmgl1, srtm1 or srtm3 params you can decide which SRTM format to use. Srtm3
    has a resolution of three arc-seconds (cca 90 meters between points). 
    Srtm1 and Srtmgl1 have a resolution of one arc-second (cca 30 meters). Srtm1 is
    available only for the United states. Srtmgl1 is available globally. If srtmgl1, srtm1 and srtm3 are True,
    they will be tried in this order.
    """
    if not file_handler:
        file_handler = FileHandler()

    if not srtmgl1 and not srtm1 and not srtm3:
        raise Exception('At least one of srtmgl1, srtm1 and srtm3 must be True')

    srtmgl1_files, srtm1_files, srtm3_files = _get_urls(use_included_urls, file_handler)

    assert srtmgl1_files
    assert srtm1_files
    assert srtm3_files

    if not srtmgl1:
        srtmgl1_files = {}
    if not srtm1:
        srtm1_files = {}
    if not srtm3:
        srtm3_files = {}

    assert srtmgl1_files or srtm1_files or srtm3_files

    return mod_data.GeoElevationData(srtmgl1_files, srtm1_files, srtm3_files, file_handler=file_handler,
                                     leave_zipped=leave_zipped, http_user=http_user, http_password=http_password)


def _get_urls(use_included_urls, file_handler):
    files_list_file_name = 'list.json'
    try:
        urls_json = _get_urls_json(use_included_urls, file_handler)
        return urls_json['srtmgl1'], urls_json['srtm1'], urls_json['srtm3']
    except:
        srtmgl1_files = None
        srtm1_files = mod_retriever.retrieve_all_files_urls(SRTM1_URL)
        srtm3_files = mod_retriever.retrieve_all_files_urls(SRTM3_URL)

        file_handler.write(files_list_file_name,
                           mod_json.dumps({'srtmgl1': srtmgl1_files, 'srtm1': srtm1_files, 'srtm3': srtm3_files},
                                          sort_keys=True, indent=4))

        return srtmgl1_files, srtm1_files, srtm3_files


def _get_urls_json(use_included_urls, file_handler):
    if use_included_urls:
        with open(DEFAULT_LIST_JSON, 'r') as f:
            return mod_json.loads(f.read())

    contents = file_handler.read(files_list_file_name)
    return mod_json.loads(contents)


class FileHandler:
    """
    The default file handler. It can be changed if you need to save/read SRTM 
    files in a database or Amazon S3.
    """

    def get_srtm_dir(self):
        """ The default path to store files. """
        # Local cache path:
        result = ""
        if 'HOME' in mod_os.environ:
            result = mod_os.sep.join([mod_os.environ['HOME'], '.cache', 'srtm'])
        elif 'HOMEPATH' in mod_os.environ:
            result = mod_os.sep.join([mod_os.environ['HOMEPATH'], '.cache', 'srtm'])
        else:
            raise Exception('No default HOME directory found, please specify a path where to store files')

        if not mod_path.exists(result):
            mod_os.makedirs(result)

        return result

    def exists(self, file_name):
        return mod_path.exists('%s/%s' % (self.get_srtm_dir(), file_name))

    def write(self, file_name, contents):
        with open('%s/%s' % (self.get_srtm_dir(), file_name), 'wb') as f:
            f.write(contents)

    def read(self, file_name):
        with open('%s/%s' % (self.get_srtm_dir(), file_name), 'rb') as f:
            return f.read()

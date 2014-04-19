#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import cherrypy
import girder.events
import os

from girder import constants
from girder.utility import plugin_utilities, model_importer
from girder.utility import config
from . import dev_endpoints


class Webroot(object):
    """
    The webroot endpoint simply serves the main index.html file.
    """
    exposed = True

    def GET(self):
        return cherrypy.lib.static.serve_file(
            os.path.join(constants.ROOT_DIR, 'clients', 'web', 'static',
                         'built', 'index.html'), content_type='text/html')


def setup(test=False, plugins=None):
    """
    Function to setup the cherrypy server. It configures it, but does
    not actually start it.

    :param test: Set to True when running in the tests.
    :type test: bool
    :param plugins: If you wish to start the server with a custom set of
                    plugins, pass this as a list of plugins to load. Otherwise,
                    will use the PLUGINS_ENABLED setting value from the db.
    """
    cur_config = config.getConfig()

    appconf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.staticdir.root': constants.ROOT_DIR,
            'request.show_tracebacks': test
        },
        '/static': {
            'tools.staticdir.on': 'True',
            'tools.staticdir.dir': 'clients/web/static'
        }
    }

    cur_config.update(appconf)

    if test:
        # Force the mode to be 'testing'
        cur_config.update({'server': {'mode': 'testing'}})

    # Don't import this until after the configs have been read; some module
    # initialization code requires the configuration to be set up.
    from girder.api import api_main

    root = Webroot()
    api_main.addApiToNode(root)

    if cur_config['server']['mode'] is 'development':
        dev_endpoints.addDevEndpoints(root, appconf)  # pragma: no cover

    cherrypy.engine.subscribe('start', girder.events.daemon.start)
    cherrypy.engine.subscribe('stop', girder.events.daemon.stop)

    if plugins is None:
        settings = model_importer.ModelImporter().model('setting')
        plugins = settings.get(constants.SettingKey.PLUGINS_ENABLED, default=())

    plugin_utilities.loadPlugins(plugins, root, appconf)

    application = cherrypy.tree.mount(root, '/', appconf)

    if test:
        application.merge({'server': {'mode': 'testing'}})

    return application
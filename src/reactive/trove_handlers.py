# Copyright 2016 TransCirrus Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# this is just for the reactive handlers and calls into the charm.
from __future__ import absolute_import

import charms.reactive as reactive
import charmhelpers.core.hookenv as hookenv

# This charm's library contains all of the handler code associated with trove
import charm.openstack.trove as trove


# use a synthetic state to ensure that it get it to be installed independent of
# the install hook.
@reactive.when_not('charm.installed')
def install_packages():
    trove.install()
    reactive.set_state('charm.installed')


@reactive.when('amqp.connected')
def setup_amqp_req(amqp):
    """
    Use the amqp interface to request access to the amqp broker using our
    local configuration.
    """
    amqp.request_access(username='trove', vhost='openstack')
    trove.assess_status()


@reactive.when('shared-db.connected')
def setup_database(database):
    """
    Configure the database on the interface.
    """
    database.configure(hookenv.config('database'),
                       hookenv.config('database-user'),
                       hookenv.unit_private_ip())
    trove.assess_status()


# this is to check if ha is running
@reactive.when('ha.connected')
def cluster_connected(hacluster):
    trove.configure_ha_resources(hacluster)


@reactive.when('identity-service.connected')
def setup_endpoint(keystone):
    trove.setup_endpoint(keystone)
    trove.assess_status()


@reactive.when('shared-db.available')
@reactive.when('identity-service.available')
@reactive.when('amqp.available')
def render_stuff(*args):
    # Get the optional hsm relation, if it is available for rendering.
    trove.render_configs(args)
    reactive.set_state('config.complete')
    trove.assess_status()


@reactive.when('config.complete')
@reactive.when_not('db.synced')
def run_db_migration():
    trove.db_sync()
    trove.restart_all()
    reactive.set_state('db.synced')
    trove.assess_status()


@reactive.when('cluster.available')
def update_peers(cluster):
    """Inform designate peers about this unit"""
    trove.update_peers(cluster)


@reactive.when('config.changed')
def config_changed():
    trove.assess_status()


@reactive.when('identity-service.available')
def configure_ssl(keystone):
    trove.configure_ssl(keystone)

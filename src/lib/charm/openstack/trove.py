# Copyright 2016 TransCirrus Inc.
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

import contextlib
import os
import subprocess
import uuid

import charmhelpers.contrib.openstack.utils as ch_utils
import openstack_adapters as openstack_adapters
import charms_openstack.charm as openstack_charm
import charms_openstack.ip as os_ip
import charmhelpers.core.decorators as decorators
import charmhelpers.core.hookenv as hookenv
import charmhelpers.core.host as host

TROVE_DIR = '/etc/trove'
TROVE_DEFAULT = '/etc/default/openstack'
TROVE_CONF = TROVE_DIR + '/trove.conf'
#RC_FILE = '/root/novarc'


# select the default release function to choose the right Charm class
openstack_charm.use_defaults('charm.default-select-release')

'''
def render_sink_configs(interfaces_list):
    """Use the singleton from the TroveCharm to render sink configs

    @param interfaces_list: List of instances of interface classes.
    @returns: None
    """
    configs = [TROVE_DEFAULT]
    TroveCharm.singleton.render_with_interfaces(
        interfaces_list,
        configs=configs)
'''

# Get database URIs for the two trove databases
@openstack_adapters.adapter_property('shared-db')
def trove_uri(db):
    """URI for trove DB"""
    return db.get_uri(prefix='trove')

'''
@openstack_adapters.adapter_property('dns')
def pool_config(dns):
    """List of DNS slave information from Juju attached DNS slaves

    Creates a dict for each backends and returns a list of those dicts.
    The trove config file has a section per backend. The template uses
    the nameserver and pool_target names to create a section for each
    backend

    @returns: list [{'nameserver': name, 'pool_target': name,
                     'address': slave_ip_addr},
                    ...]
    """
    pconfig = []
    for slave in dns.slave_ips:
        unit_name = slave['unit'].replace('/', '_').replace('-', '_')
        pconfig.append({
            'nameserver': 'nameserver_{}'.format(unit_name),
            'pool_target': 'nameserver_{}'.format(unit_name),
            'address': slave['address'],
        })
    return pconfig


@openstack_adapters.adapter_property('dns')
def pool_targets(dns):
    """List of pool_target section names

    @returns: str Comma delimited list of pool_target section names
    """
    return ', '.join([s['pool_target'] for s in dns.pool_config])


@openstack_adapters.adapter_property('dns')
def slave_addresses(dns):
    """List of slave IP addresses

    @returns: str Comma delimited list of slave IP addresses
    """
    return ', '.join(['{}:53'.format(s['address'])
                     for s in dns.pool_config])


@openstack_adapters.adapter_property('dns')
def rndc_info(dns):
    """Rndc key and algorith in formation.

    @returns: dict {'algorithm': rndc_algorithm,
                    'secret': rndc_secret_digest}
    """
    return dns.relation.rndc_info


## configuration adapter custom properties

@openstack_adapters.config_property
def pool_config(config):
    """List of DNS slave information from user defined config

    Creates a dict for each backends and returns a list of those dicts.
    The trove config file has a section per backend. The template uses
    the nameserver and pool_target names to create a section for each
    backend.

    @returns: list [{'nameserver': name,
                     'pool_target': name,
                     'address': slave_ip_addr,
                     'rndc_key_file': rndc_key_file},
                    ...]
    """
    pconfig = []
    for entry in config.dns_slaves.split():
        address, port, key = entry.split(':')
        unit_name = address.replace('.', '_')
        pconfig.append({
            'nameserver': 'nameserver_{}'.format(unit_name),
            'pool_target': 'nameserver_{}'.format(unit_name),
            'address': address,
            'rndc_key_file': '/etc/designate/rndc_{}.key'.format(
                unit_name),
        })
    return pconfig

@openstack_adapters.config_property
def pool_targets(config):
    """List of pool_target section names

    @returns: str Comma delimited list of pool_target section names
    """
    return ', '.join([s['pool_target'] for s in config.pool_config])


@openstack_adapters.config_property
def slave_addresses(config):
    """List of slave IP addresses

    @returns: str Comma delimited list of slave IP addresses
    """
    return ', '.join(['{}:53'.format(s['address'])
                     for s in config.pool_config])


@openstack_adapters.config_property
def nova_domain_id(config):
    """Returns the id of the domain corresponding to the user supplied
    'nova-domain'

    @returns nova domain id
    """
    domain = hookenv.config('nova-domain')
    if domain:
        return TroveCharm.get_domain_id(domain)
    return None


@openstack_adapters.config_property
def neutron_domain_id(config):
    """Returns the id of the domain corresponding to the user supplied
    'neutron-domain'

    @returns neutron domain id
    """
    domain = hookenv.config('neutron-domain')
    if domain:
        return TroveCharm.get_domain_id(domain)
    return None


@openstack_adapters.config_property
def nova_conf_args(config):
    """Returns config file directive to point daemons at nova config file.
    These directives are designed to be used in /etc/default/ files

    @returns startup config file option
    """
    daemon_arg = ''
    if os.path.exists(NOVA_SINK_FILE):
        daemon_arg = '--config-file={}'.format(NOVA_SINK_FILE)
    return daemon_arg


@openstack_adapters.config_property
def neutron_conf_args(config):
    """Returns config file directive to point daemons at neutron config
    file. These directives are designed to be used in /etc/default/ files

    @returns startup config file option
    """
    daemon_arg = ''
    if os.path.exists(NEUTRON_SINK_FILE):
        daemon_arg = '--config-file={}'.format(NEUTRON_SINK_FILE)
    return daemon_arg


@openstack_adapters.config_property
def rndc_master_ip(config):
    """Returns IP address slave DNS slave should use to query master
    """
    return os_ip.resolve_address(endpoint_type=os_ip.INTERNAL)
'''

class TroveCharm(openstack_charm.HAOpenStackCharm):

    name = 'trove'
    packages = [ 'build-essential', 'libxslt1-dev', 'qemu-utils',
                'mysql-client', 'git', 'python-dev', 'python-pexpect',
                'python-pymysql', 'libmysqlclient-dev', 'python-apt',
                'python-trove', 'python-troveclient', 'python-glanceclient',
                'trove-common', 'trove-api', 'trove-taskmanager','trove-conductor']

    services = ['trove-api', 'trove-taskmanager','trove-conductor']

    api_ports = {
        'trove-api': {
            os_ip.PUBLIC: 8779,
            os_ip.ADMIN: 8779,
            os_ip.INTERNAL: 8779,
        }
    }

    required_relations = ['shared-db', 'amqp', 'identity-service', 'image-service', 'cloud-compute', ]

    restart_map = {
        '/etc/default/openstack': services,
        '/etc/trove/trove.conf': services,
        '/etc/trove/trove-conductor.conf': services,
        '/etc/trove/trove-taskmanager.conf': services,
        RC_FILE: [''],
    }
    service_type = 'trove'
    default_service = 'trove-api'
    sync_cmd = ['trove-manage', 'db_sync']

    ha_resources = ['vips', 'haproxy']
    release = 'mitaka'

    def get_amqp_credentials(self):
        """Provide the default amqp username and vhost as a tuple.

        :returns (username, host): two strings to send to the amqp provider.
        """
        return ('trove', 'openstack')

    def get_database_setup(self):
        """Provide the default database credentials as a list of 3-tuples

        returns a structure of:
        [
            {'database': <database>,
             'username': <username>,
             'hostname': <hostname of this unit>
             'prefix': <the optional prefix for the database>, },
        ]

        :returns [{'database': ...}, ...]: credentials for multiple databases
        """
        ip = hookenv.unit_private_ip()
        return [
            dict(
                database='trove',
                username='trove',
                hostname=ip,
                prefix='trove'),
        ]

    def render_base_config(self, interfaces_list):
        """Render initial config to bootstrap Trove service

        @returns None
        """
        configs = [RC_FILE, TROVE_CONF, TROVE_DEFAULT]
        if self.haproxy_enabled():
            configs.append(self.HAPROXY_CONF)
        self.render_with_interfaces(
            interfaces_list,
            configs=configs)

    def render_full_config(self, interfaces_list):
        """Render all config for Trove service

        @returns None
        """
        # Render base config first to ensure Trove API is responding as
        # sink configs rely on it.
        self.render_base_config(interfaces_list)
        self.render_with_interfaces(interfaces_list)
    '''
    @classmethod
    def create_domain(cls, domain, email):
        """Create a domain

        @param domain: The name of the domain you are creating. The name must
                       end with a full stop.
        @param email: An email address of the person responsible for the
                      domain.
        @returns None
        """
        cls.ensure_api_responding()
        create_cmd = ['reactive/trove_utils.py', 'domain-create',
                      '--domain-name', domain, '--email', email]
        subprocess.check_call(create_cmd)
    '''

    @classmethod
    def create_server(cls, nsname):
        """ create a nameserver entry with the supplied name

        @param nsname: Name of NameserverS record
        @returns None
        """
        cls.ensure_api_responding()
        create_cmd = ['reactive/trove_utils.py', 'server-create',
                      '--server-name', nsname]
        subprocess.check_call(create_cmd)

    @classmethod
    def domain_init_done(cls):
        """Query leader db to see if domain creation is donei

        @returns boolean"""
        return hookenv.leader_get(attribute='domain-init-done')

    @classmethod
    @decorators.retry_on_exception(
        10, base_delay=5, exc_type=subprocess.CalledProcessError)
    def ensure_api_responding(cls):
        """Check that the api service is responding.

        The retry_on_exception decorator will cause this method to be called
        until it succeeds or retry limit is exceeded"""
        hookenv.log('Checking API service is responding',
                    level=hookenv.WARNING)
        check_cmd = ['reactive/trove_utils.py', 'server-list']
        subprocess.check_call(check_cmd)

    @classmethod
    @contextlib.contextmanager
    def check_zone_ids(cls, nova_domain_name, neutron_domain_name):
        zone_org_ids = {
            'nova-domain-id': cls.get_domain_id(nova_domain_name),
            'neutron-domain-id': cls.get_domain_id(neutron_domain_name),
        }
        yield
        zone_ids = {
            'nova-domain-id': cls.get_domain_id(nova_domain_name),
            'neutron-domain-id': cls.get_domain_id(neutron_domain_name),
        }
        if zone_org_ids != zone_ids:
            # Update leader-db to trigger peers to rerender configs
            # as sink files will need updating with new domain ids
            # Use host ID and current time UUID to help with debugging
            hookenv.leader_set({'domain-init-done': uuid.uuid1()})

    @classmethod
    def create_initial_servers_and_domains(cls):
        """Create the nameserver entry and domains based on the charm user
        supplied config

        @returns None
        """
        if hookenv.is_leader():
            cls.ensure_api_responding()
            nova_domain_name = hookenv.config('nova-domain')
            neutron_domain_name = hookenv.config('neutron-domain')
            with cls.check_zone_ids(nova_domain_name, neutron_domain_name):
                if hookenv.config('nameservers'):
                    for ns in hookenv.config('nameservers').split():
                        cls.create_server(ns)
                else:
                    hookenv.log('No nameserver specified, skipping creation of'
                                'nova and neutron domains',
                                level=hookenv.WARNING)
                    return
                if nova_domain_name:
                    cls.create_domain(
                        nova_domain_name,
                        hookenv.config('nova-domain-email'))
                if neutron_domain_name:
                    cls.create_domain(
                        neutron_domain_name,
                        hookenv.config('neutron-domain-email'))

    def update_pools(self):
        # designate-manage communicates with designate via message bus so no
        # need to set OS_ vars
        if hookenv.is_leader():
            cmd = ['trove-manage', 'pool', 'update']
            subprocess.check_call(cmd)

    def custom_assess_status_check(self):
        if (not hookenv.config('nameservers') and
                (hookenv.config('nova-domain') or
                 hookenv.config('neutron-domain'))):
            return 'blocked', ('nameservers must be set when specifying'
                               ' nova-domain or neutron-domain')
        return None, None
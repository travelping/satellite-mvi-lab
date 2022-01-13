from generatorPreProcessor import GeneratorPreProcessor
import sys

# Validating:
# ---
# openshift:
# - name: sample
#   ocp_version: 4.6
#   worker_flavour: bx2.16x64
#   number_of_workers: 3
#   infrastructure:
#     type: vpc
#     vpc_name: sample
#     subnets: 
#     - sample-subnet-zone-1
#     - sample-subnet-zone-2
#     - sample-subnet-zone-3
#   upstream_dns:
#   - name: sample-dns
#     zones:
#     - sample.com
#     dns_servers:
#     - 172.31.2.73:53
#   openshift_storage:
#   - storage_name: nfs-storage
#     storage_type: nfs
#     nfs_server_name: sample-nfs
#   - storage_name: ocs-storage
#     storage_type: ocs
#     ocs_storage_label: ocs
#     ocs_storage_size_gb: 500

def preprocessor(attributes=None, fullConfig=None):
    g = GeneratorPreProcessor(attributes,fullConfig)

    g('name').isRequired()
    g('ocp_version').isRequired()
    g('worker_flavour').isRequired()
    g('number_of_workers').isRequired()
    
    g('infrastructure').isRequired()
    g('infrastructure.type').mustBeOneOf(['vpc'])
    g('infrastructure.vpc_name').expandWith('vpc[*]',remoteIdentifier='name')
    g('infrastructure.subnets').isRequired()
    g('infrastructure.cos_name').isRequired()

    g('openshift_storage').isRequired()

    # Now that we have reached this point, we can check the attribute details if the previous checks passed
    if len(g.getErrors()) == 0:
        fc = g.getFullConfig()
        ge=g.getExpandedAttributes()

        # Number of subnets must be 1 or 3
        if len(ge['infrastructure']['subnets']) != 1 and len(ge['infrastructure']['subnets']) != 3:
            g.appendError(msg='Number of subnets specified is ' + str(len(ge['infrastructure']['subnets'])) + ' must be 1 or 3')

        # Number of workers must be a factor of the number of subnets
        if (ge['number_of_workers'] % len(ge['infrastructure']['subnets'])) != 0:
            g.appendError(msg='number_of_workers must be a factor of the number of subnets')

        # Check upstream DNS server
        if 'upstream_dns' in ge:
            for dns in ge['upstream_dns']:
                if 'name' not in dns:
                    g.appendError(msg='name must be specified for all upstream_dns elements')
                if 'zones' not in dns:
                    g.appendError(msg='zones must be specified for all upstream_dns elements')
                elif len(dns['zones']) < 1:
                    g.appendError(msg='At least 1 zones element must be specified for all upstream_dns configurations')
                if 'dns_servers' not in dns:
                    g.appendError(msg='dns_servers must be specified for all upstream_dns elements')
                elif len(dns['dns_servers']) < 1:
                    g.appendError(msg='At least 1 dns_servers element must be specified for all upstream_dns configurations')

        # Check openshift_storage atttributes
        if len(ge['openshift_storage']) < 1:
            g.appendError(msg='At least one openshift_storage element must be specified.')
        for os in ge['openshift_storage']:
            if "storage_name" not in os:
                g.appendError(msg='storage_name must be specified for all openshift_storage elements')
            if "storage_type" not in os:
                g.appendError(msg='storage_type must be specified for all openshift_storage elements')
            if "storage_type" in os and os['storage_type'] not in ['nfs','ocs']:
                g.appendError(msg='storage_type must be nfs or ocs')
            if "storage_type" in os and os['storage_type']=='nfs':
                nfs_server_names = []
                if 'nfs_server' in fc:
                    nfs_server_names = fc.match('nfs_server[*].name')
                if "nfs_server_name" not in os:
                    g.appendError(msg='nfs_server_name must be specified when storage_type is nfs')
                elif os['nfs_server_name'] not in nfs_server_names:
                    g.appendError(msg="'"+ os['nfs_server_name'] + "' is not an existing nfs_server name (Found nfs_server: ["+ ','.join(nfs_server_names) +"] )")
            if "storage_type" in os and os['storage_type']=='ocs':
                if "ocs_storage_label" not in os:
                    g.appendError(msg='ocs_storage_label must be specified when storage_type is ocs')
                if "ocs_storage_size_gb" not in os:
                    g.appendError(msg='ocs_storage_size_gb must be specified when storage_type is ocs')

    result = {
        'attributes_updated': g.getExpandedAttributes(),
        'errors': g.getErrors()
    }
    return result



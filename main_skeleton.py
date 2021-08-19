# -*- mode: python; python-indent: 4 -*-
import ncs
from ncs.application import Service
from ncs.dp import Action
import ipaddress
import re
import random
from passlib.hash import cisco_type7

# ------------------------
# SERVICE CALLBACK EXAMPLE
# ------------------------

class RoutePolicy():
    def __init__(self,log = None):
        self.log = log

    def deploy_prefix_set(self,service,root,device,prefix_set_name):
        self.log.info('Add prefix-set {} in {}'.format(prefix_set_name,device))
        if (root.devices.device[device].device_type.netconf.ned_id and root.devices.device[device].device_type.netconf.ned_id.startswith('cisco-iosxr-nc')):
            self.log.info('Creating prefix-set {} in Cisco device {}'.format(prefix_set_name,device))
            prefix_string = ''
            for prefix in root.routing_policy.defined_sets.prefix_sets.prefix_set[prefix_set_name].prefixes.prefix_list:
                if prefix_string == '':
                    prefix_string = prefix.ip_prefix + ' ge ' + str(prefix.masklength_lower) + ' le ' + str(prefix.masklength_upper) + '\n  '
                else:
                    prefix_string = prefix_string + prefix.ip_prefix + ' ge ' + str(prefix.masklength_lower) + ' le ' + str(prefix.masklength_upper) + '\n  '
            prefixset_vars = ncs.template.Variables()
            prefixset_template = ncs.template.Template(service)
            prefixset_vars.add('device', device)
            prefixset_vars.add('PREFIX_LIST_NAME', prefix_set_name)
            prefixset_vars.add('IP_PREFIX', prefix.ip_prefix)
            prefixset_vars.add('PREFIX_STRING', prefix_string)
            prefixset_template.apply('prefix-set-template', prefixset_vars)

        else:
            for prefix in root.routing_policy.defined_sets.prefix_sets.prefix_set[prefix_set_name].prefixes.prefix_list:
                prefixset_vars = ncs.template.Variables()
                prefixset_template = ncs.template.Template(service)
                prefixset_vars.add('device', device)
                prefixset_vars.add('PREFIX_LIST_NAME', prefix_set_name)
                prefixset_vars.add('IP_PREFIX', prefix.ip_prefix)
                prefixset_vars.add('PREFIX_STRING', '')
                prefixset_template.apply('prefix-set-template', prefixset_vars)

    def set_extcommset(self,service,root,device,import_policy_set,ietf_route_target):
        self.log.info('Set RT_SET {} add RT {} in {}'.format(import_policy_set,ietf_route_target,device))

        # Transform the RD in IETF format to the device RD format
        rt_fields = ietf_route_target.split(':')
        route_target = rt_fields[1] + ':' + rt_fields[2]

        extcommset_vars = ncs.template.Variables()
        extcommset_template = ncs.template.Template(service)
        extcommset_vars.add('device', device)
        extcommset_vars.add('RT_VALUE', route_target)
        extcommset_vars.add('RT_COMMUNITY_SET', import_policy_set)
        extcommset_template.apply('rt-ext-community-set', extcommset_vars)

    def set_rt_policy(self,service,root,device,policy_set,policy_name,stm_name='', default_action='', stm_description='', stm_action='', stm_comm_oper='', stm_comm='', stm_match_line='', stm_protocol='', prefix_set ='', dest_protocol='false', stm_dst_protocol='',tag_values='',policy_string=''):
        self.log.info('Set RT_POLICY {} with RT_SET {} in {}'.format(policy_set,policy_name,device))
        self.log.info('device {} policy_set {} policy_name {} stm_name {} default_action {} stm_description {} stm_action {} stm_comm_oper {} stm_comm {} stm_match_line {} stm_protocol {} prefix-set {}'.format(device,policy_set,policy_name,stm_name,default_action,stm_description,stm_action,stm_comm_oper,stm_comm,stm_match_line,stm_protocol,prefix_set))

        if stm_name== '':
            stm_name = policy_name + '_stm'

        tag = ''
        for index in tag_values:
            tag = index

        rt_policy_vars = ncs.template.Variables()
        rt_policy_template = ncs.template.Template(service)
        rt_policy_vars.add('device', device)
        rt_policy_vars.add('RT_POLICY', policy_name)
        rt_policy_vars.add('RT_COMMUNITY_SET', policy_set)
        rt_policy_vars.add('STM_NAME', stm_name)
        rt_policy_vars.add('DEFAULT_ACTION', default_action)
        rt_policy_vars.add('STM_DESCRIPTION', stm_description)
        rt_policy_vars.add('STM_ACTION', stm_action)
        rt_policy_vars.add('STM_COMM_OPER', stm_comm_oper)
        rt_policy_vars.add('STM_COMM', stm_comm)
        rt_policy_vars.add('STM_MATCH_LINE', stm_match_line)
        rt_policy_vars.add('STM_PROTOCOL', stm_protocol)
        rt_policy_vars.add('STM_PREFIX_SET', prefix_set)
        rt_policy_vars.add('DST_PROTOCOL', dest_protocol)
        rt_policy_vars.add('STM_DST_PROTOCOL', stm_dst_protocol)
        rt_policy_vars.add('TAG', tag)
        rt_policy_vars.add('ROUTE_POLICY_STRING', policy_string)
        rt_policy_template.apply('rt-policy', rt_policy_vars)

    def deploy_extcommset(self,service,root,device,extcommset_name):
        extcommset = root.rt_pol__routing_policy.defined_sets.bp__bgp_defined_sets.ext_community_sets.ext_community_set[extcommset_name]
        for route_target in extcommset.member:
            self.set_extcommset(service,root,device,extcommset_name,route_target)

    def deploy_route_policy(self,service,root,device,policy_name):
        self.log.info('Creating policy-definition {} in device {}'.format(policy_name,device))
        if (root.devices.device[device].device_type.netconf.ned_id and root.devices.device[device].device_type.netconf.ned_id.startswith('cisco-iosxr-nc')):
            self.log.info('Creating policy-definition {} in Cisco device {}'.format(policy_name,device))
            final_item = ''
            if (policy_name and root.routing_policy.policy_definitions.policy_definition[policy_name]):
                policy_string=''
                policy=root.routing_policy.policy_definitions.policy_definition[policy_name]
                default_action = policy.default_action

                for stm in policy.policy_statements.statement:
                    stm_string = ''
                    stm_comment = ''
                    if stm.description:
                        stm_comment = "# " + stm.description +"\n"

                    # Now we gor for the condition

                    prot_string = ''
                    if (stm.conditions.source_protocol == 'rt:bgp'):
                        # string is: if protocol is bgp LOCAL_AS
                        local_as = ''
                        for asn in root.devices.device[device].config.Cisco_IOS_XR_ipv4_bgp_cfg__bgp.instance['default'].instance_as['0'].four_byte_as:
                            local_as = asn.Cisco_IOS_XR_ipv4_bgp_cfg__as

                        prot_string = 'protocol is bgp ' + str(local_as)
                    elif (stm.conditions.source_protocol == 'rt:direct'):
                        # string is: if protocol is bgp LOCAL_AS
                        prot_string = 'protocol is connected'
                    elif (stm.conditions.source_protocol == 'rt:aggregate'):
                        # aggregates in Cisco will be configured as static routes
                        prot_string = 'protocol is static'

                    tag_string = ''
                    if stm.conditions.match_tag_set.tag_set:
                        # string is: if tag in (tag_value)
                        tag_values = root.routing_policy.defined_sets.tag_sets.tag_set[stm.conditions.match_tag_set.tag_set].tag_value
                        for tag in tag_values:
                            if tag_string:
                                tag_string = str(tag)
                            else:
                                tag_string = tag_string + ' , ' + str(tag)
                        tag_string = 'tag in (' + tag_string + ')'

                    comm_string = ''
                    if stm.conditions.bp__bgp_conditions.match_ext_community_set.ext_community_set and \
                      stm.conditions.bp__bgp_conditions.match_ext_community_set.match_set_options == 'any':
                        # string is: extcommunity rt matches-any SERVICO-LTE_HRT or extcommunity rt matches-any SERVICO-LTE_SRT
                        for ext_comm in stm.conditions.bp__bgp_conditions.match_ext_community_set.ext_community_set:
                            self.deploy_extcommset(service,root,device,ext_comm)
                            if not comm_string:
                                comm_string = 'extcommunity rt matches-any ' + ext_comm
                            else:
                                comm_string = comm_string + ' or ' + 'extcommunity rt matches-any ' + ext_comm
                        comm_string = '( ' + comm_string + ' )'

                    prefix_string = ''
                    if stm.conditions.match_prefix_set.prefix_set:
                        self.deploy_prefix_set(service,root,device,stm.conditions.match_prefix_set.prefix_set)
                        prefix_set = stm.conditions.match_prefix_set.prefix_set
                        prefix_string = 'destination in ' + prefix_set

                    # And now for the "then" part:
                    # policy_result can be accept or reject
                    stm_action = stm.actions.policy_result

                    then_string = ''
                    if stm_action == 'reject-route':
                        then_string = 'drop\n'
                    elif stm_action == 'accept-route':
                        if stm.actions.bp__bgp_actions.set_ext_community.method:
                            # string is:     set extcommunity rt SERVICO-LTE_HRT (additive)
                            stm_comm_oper = stm.actions.bp__bgp_actions.set_ext_community.options.string
                            # stm_comm_oper can be 
                            #remove, delete extcommunity rt in DENY-RPS
                            #add, set extcommunity rt DENY-RPS additive
                            #replace, set extcommunity rt DENY-RPS 
                            stm_comm = stm.actions.bp__bgp_actions.set_ext_community.reference.ext_community_set_ref
                            if stm_comm_oper == 'remove':
                                then_string= 'delete extcommunity rt in ' + stm_comm + '\n'
                            elif stm_comm_oper == 'replace':
                                then_string= 'set extcommunity rt ' + stm_comm + '\n'
                            elif stm_comm_oper == 'add':
                                then_string= 'set extcommunity rt ' + stm_comm + ' additive\n'
                        else:
                            then_string = 'done\n'

                    # tie the statament all nice
                    # No source protocol is needed in Cisco case
                    #if prot_string:
                    #    stm_string = stm_comment + ' if ' + prot_string
                    if comm_string:
                        stm_string = stm_comment + ' if ' + comm_string
                    if tag_string:
                        # Nothing to do here with a tag in the VRF export policy
                        # stm_string = stm_comment + ' if ' + tag_string
                        continue
                    if prefix_string:
                        stm_string = stm_comment + ' if ' + prefix_string
                    if ' if ' in stm_string:
                        stm_string = stm_string + ' then\n  ' + then_string +' endif\n  '
                    else: # last item will override default
                        stm_string = stm_comment + then_string +' \n  '
                        final_item = 'found'

                    policy_string = policy_string + stm_string
                # default_action
                if not final_item:
                    if default_action == 'accept-route':
                        policy_string = policy_string + ' pass\n'
                    else:
                        policy_string = policy_string + ' drop\n'
                # Now deploy the policy
                self.set_rt_policy(service,root,device,'',policy_name,'', '', '', '', '', '', '', '', '', '', '','',policy_string)



        elif (policy_name and root.routing_policy.policy_definitions.policy_definition[policy_name]):
            policy_set=''
            policy=root.routing_policy.policy_definitions.policy_definition[policy_name]
            policy_name=policy.name
            default_action = policy.default_action
            for stm in policy.policy_statements.statement:
                stm_name = stm.name
                stm_description = stm.description
                stm_action = stm.actions.policy_result
                if stm.actions.bp__bgp_actions.set_ext_community.method:
                    stm_comm_oper = stm.actions.bp__bgp_actions.set_ext_community.options.string
                    stm_comm = stm.actions.bp__bgp_actions.set_ext_community.reference.ext_community_set_ref
                else:
                    stm_comm_oper = ''
                    stm_comm = ''

                if (stm.conditions.source_protocol == 'rt:bgp'):
                    if 'l3vpn-ipv4-unicast' in stm.conditions.bp__bgp_conditions.afi_safi_in:
                        stm_protocol = 'bgp-vpn'
                    else:
                        stm_protocol = 'bgp'
                elif (stm.conditions.source_protocol == 'rt:direct'):
                    stm_protocol = 'direct'
                elif (stm.conditions.source_protocol == 'rt:aggregate'):
                    stm_protocol = 'aggregate'
                else:
                    stm_protocol=''

                if (stm.conditions.destination_protocol == 'rt:bgp'):
                    stm_dst_protocol = 'bgp'
                    dest_protocol = 'true'
                elif (stm.conditions.destination_protocol == 'rt:direct'):
                    stm_dst_protocol = 'direct'
                    dest_protocol = 'true'
                elif (stm.conditions.destination_protocol == 'rt:aggregate'):
                    stm_dst_protocol = 'aggregate'
                    dest_protocol = 'true'
                else:
                    stm_dst_protocol=''
                    dest_protocol = 'false'

                if stm.conditions.match_tag_set.tag_set:
                    tag_values = root.routing_policy.defined_sets.tag_sets.tag_set[stm.conditions.match_tag_set.tag_set].tag_value
                else:
                    tag_values = []

                if stm.conditions.bp__bgp_conditions.match_ext_community_set.match_set_options == 'any':
                    stm_match_line = ''
                    for ext_comm in stm.conditions.bp__bgp_conditions.match_ext_community_set.ext_community_set:
                        self.deploy_extcommset(service,root,device,ext_comm)
                        if stm_match_line == '':
                            stm_match_line = '[' + ext_comm + ']'
                        else:
                            stm_match_line = stm_match_line + ' OR ' + '[' + ext_comm + ']'
                if stm.conditions.match_prefix_set.prefix_set:
                    self.deploy_prefix_set(service,root,device,stm.conditions.match_prefix_set.prefix_set)
                    stm_match_line = 'prefix-set'
                    prefix_set = stm.conditions.match_prefix_set.prefix_set
                else:
                    prefix_set=''

                self.set_rt_policy(service,root,device,policy_set,policy_name,stm_name, default_action, stm_description, stm_action, stm_comm_oper, stm_comm, stm_match_line, stm_protocol, prefix_set, dest_protocol, stm_dst_protocol,tag_values,'')


class L3VPN_VPNNode(Service):

    def create_ni(self,service,root,device,customer,ni_name,ni_desc,vpn_id,ni_routerid,ni_af,route_distinguisher,import_policy_name,export_policy_name,global_as,rd_as,rd_idx,export_rt_as,export_rt_idx,import_rt_as,import_rt_idx,both_rt_as,both_rt_idx,target_type,ecmp):
        self.log.info('Create Network Instance {} with RD {} add policies {} {} in {}'.format(ni_name,route_distinguisher,import_policy_name,export_policy_name,device))

        create_ni_vars = ncs.template.Variables()
        create_ni_template = ncs.template.Template(service)
        create_ni_vars.add('device', device)
        create_ni_vars.add('NI_NAME', ni_name)
        create_ni_vars.add('NI_CUSTOMER_ID', customer)
        create_ni_vars.add('NI_VPN_ID', vpn_id)
        create_ni_vars.add('NI_DESC', ni_desc)
        create_ni_vars.add('NI_AF', ni_af)
        create_ni_vars.add('NI_RD', route_distinguisher)
        create_ni_vars.add('NI_ROUTERID', ni_routerid)
        create_ni_vars.add('RT_EXPORT_POLICY', export_policy_name)
        create_ni_vars.add('RT_IMPORT_POLICY', import_policy_name)
        create_ni_vars.add('GLOBAL_AS', global_as)
        create_ni_vars.add('ECMP', ecmp)
        create_ni_vars.add('RD_AS', rd_as)
        create_ni_vars.add('RD_IDX', rd_idx)
        create_ni_vars.add('EXPORT_RT_AS', export_rt_as)
        create_ni_vars.add('EXPORT_RT_IDX', export_rt_idx)
        create_ni_vars.add('IMPORT_RT_AS', import_rt_as)
        create_ni_vars.add('IMPORT_RT_IDX', import_rt_idx)
        create_ni_vars.add('TARGET_TYPE', target_type)
        create_ni_vars.add('BOTH_RT_AS', both_rt_as)
        create_ni_vars.add('BOTH_RT_IDX', both_rt_idx)

        create_ni_template.apply('pe-ni', create_ni_vars)

    def create_bgp_routing(self,service,root,device,ni_name,ni_routerid,ni_as,address_family):
        self.log.info('Create BGP in Network Instance {} in {}'.format(ni_name,device))

        create_bgp_routing_vars = ncs.template.Variables()
        create_bgp_routing_template = ncs.template.Template(service)
        create_bgp_routing_vars.add('device', device)
        create_bgp_routing_vars.add('NI_NAME', ni_name)
        create_bgp_routing_vars.add('AF', address_family)
        create_bgp_routing_vars.add('AS', ni_as)
        create_bgp_routing_vars.add('ROUTER_ID', ni_routerid)
        create_bgp_routing_template.apply('bgp-routing', create_bgp_routing_vars)

    def create_ipv4_aggregate(self,service,root,device,ni_vpnid,ipv4_aggregate):
        self.log.info('Create Aggregate {} in Network Instance {} in {}'.format(ipv4_aggregate,ni_vpnid,device))

        create_ipv4_aggregate_vars = ncs.template.Variables()
        create_ipv4_aggregate_template = ncs.template.Template(service)
        create_ipv4_aggregate_vars.add('device', device)
        create_ipv4_aggregate_vars.add('NI_VPN_ID', ni_vpnid)
        create_ipv4_aggregate_vars.add('AGGREGATE', ipv4_aggregate)
        create_ipv4_aggregate_vars.add('AGG_PFX', ipaddress.ip_network(ipv4_aggregate).network_address)
        create_ipv4_aggregate_vars.add('AGG_MASK', ipaddress.ip_network(ipv4_aggregate).prefixlen)
        create_ipv4_aggregate_template.apply('pe-ni-ipv4-aggregate', create_ipv4_aggregate_vars)

    def set_vrf_in_vpn_node(self,service,customer,root,vpn_id,vpn_node_id,device):
        # Try to encapsulate
        route_policy = RoutePolicy(self.log)
        # Take all parameters
        ni_name = customer + '_' + vpn_id
        ni_desc = service.description
        ni_routerid = root.l3vpn_ntw.vpn_services.vpn_service[vpn_id].vpn_nodes.vpn_node[vpn_node_id,device].router_id
        ni_as = root.l3vpn_ntw.vpn_services.vpn_service[vpn_id].vpn_nodes.vpn_node[vpn_node_id,device].autonomous_system
        node_role = root.l3vpn_ntw.vpn_services.vpn_service[vpn_id].vpn_nodes.vpn_node[vpn_node_id,device].node_role
        node_ie_profile = root.l3vpn_ntw.vpn_services.vpn_service[vpn_id].vpn_nodes.vpn_node[vpn_node_id,device].node_ie_profile

        # Names for the policies
        
        # Transform the RD in IETF format to the device RD format
        rd_fields = root.l3vpn_ntw.vpn_services.vpn_service[vpn_id].ie_profiles.ie_profile[node_ie_profile].rd.split(':')
        if (rd_fields[0]=='0'):
            route_distinguisher = rd_fields[1] + ':' + rd_fields[2]
            rd_as=rd_fields[1]
            rd_idx=rd_fields[2]

        import_policy_name = ''
        export_policy_name = ''
        import_rt_as = ''
        import_rt_idx = ''
        export_rt_as = ''
        export_rt_idx = ''
        both_rt_as = ''
        both_rt_idx = ''
        target_type = ''



        # Processing RT's if used
        if root.l3vpn_ntw.vpn_services.vpn_service[vpn_id].ie_profiles.ie_profile[node_ie_profile].vpn_targets.vpn_target:
            import_policy_name = 'RT_IMPORT_POLICY_' + vpn_node_id
            export_policy_name = 'RT_EXPORT_POLICY_' + vpn_node_id
            import_policy_set = 'RT_IMPORT_SET_' + vpn_node_id
            export_policy_set = 'RT_EXPORT_SET_' + vpn_node_id

            for vpn_target in root.l3vpn_ntw.vpn_services.vpn_service[vpn_id].ie_profiles.ie_profile[node_ie_profile].vpn_targets.vpn_target:
                rt_fields = vpn_target.route_target.split(':')
                if vpn_target.route_target_type == 'import':
                    if (root.devices.device[device].device_type.cli.ned_id and root.devices.device[device].device_type.cli.ned_id.startswith('alu-sr-cli')):
                        target_type="import"
                        import_policy_name = ''
                        export_policy_name = ''

                    else:
                        route_policy.set_extcommset(service,root,device,import_policy_set,vpn_target.route_target)
                        route_policy.set_rt_policy(service,root,device,import_policy_set,import_policy_name)
                    import_rt_as = rt_fields[1]
                    import_rt_idx = rt_fields[2]
                if vpn_target.route_target_type == 'export':
                    if (root.devices.device[device].device_type.cli.ned_id and root.devices.device[device].device_type.cli.ned_id.startswith('alu-sr-cli')):
                        target_type="export"
                        import_policy_name = ''
                        export_policy_name = ''
                    else:
                        route_policy.set_extcommset(service,root,device,export_policy_set,vpn_target.route_target)
                        route_policy.set_rt_policy(service,root,device,export_policy_set,export_policy_name)
                    export_rt_as = rt_fields[1]
                    export_rt_idx = rt_fields[2]
                if vpn_target.route_target_type == 'both':
                    import_rt_as = rt_fields[1]
                    import_rt_idx = rt_fields[2]
                    export_rt_as = rt_fields[1]
                    export_rt_idx = rt_fields[2]
                    if (root.devices.device[device].device_type.cli.ned_id and root.devices.device[device].device_type.cli.ned_id.startswith('alu-sr-cli')):
                        target_type="both"
                        both_rt_as = rt_fields[1]
                        both_rt_idx = rt_fields[2]
                        import_policy_name = ''
                        export_policy_name = ''
                    else:
                        route_policy.set_extcommset(service,root,device,import_policy_set,vpn_target.route_target)
                        route_policy.set_extcommset(service,root,device,export_policy_set,vpn_target.route_target)
                        route_policy.set_rt_policy(service,root,device,import_policy_set,import_policy_name)
                        route_policy.set_rt_policy(service,root,device,export_policy_set,export_policy_name)
        elif root.l3vpn_ntw.vpn_services.vpn_service[vpn_id].ie_profiles.ie_profile[node_ie_profile].vpn_policies:
            import_policy_name = root.l3vpn_ntw.vpn_services.vpn_service[vpn_id].ie_profiles.ie_profile[node_ie_profile].vpn_policies.import_policy
            export_policy_name = root.l3vpn_ntw.vpn_services.vpn_service[vpn_id].ie_profiles.ie_profile[node_ie_profile].vpn_policies.export_policy
            route_policy.deploy_route_policy(service,root,device,import_policy_name)
            route_policy.deploy_route_policy(service,root,device,export_policy_name)

            
        # Create network instance
        self.create_ni(service,root,device,customer,ni_name,ni_desc,vpn_id,ni_routerid,'IPV4',route_distinguisher,import_policy_name,export_policy_name, ni_as, rd_as, rd_idx, export_rt_as, export_rt_idx, import_rt_as, import_rt_idx, both_rt_as, both_rt_idx, target_type, service.ecmp)
        #Enable BGP, only for Openconfig
        self.create_bgp_routing(service,root,device,ni_name,ni_routerid,ni_as,'IPV4')         
        #Add aggregates, only for Nokia so far
        for aggregate in service.ipv4_aggregate:
            self.create_ipv4_aggregate(service,root,device,vpn_id,aggregate)

    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ')')
        vpn_node_id = service.vpn_node_id
        device = service.ne_id
        


        # VPN service parameters
        vpn_id = self.get_vpnid_from_vpnnode(root,vpn_node_id,device)
        customer = self.get_customer_from_vpnid(root,vpn_id)


        # estamos ignorando QOS por ahora
        self.log.info("Activate VPN service {} on vpn_node_id {} on device {} for customer {}".format(vpn_id,vpn_node_id,device,customer))
        # derive parameters
        if device:
            # First, configure the VPN in the VPN Node
            self.set_vrf_in_vpn_node(service,customer,root,vpn_id,vpn_node_id,device)
        
        else:
            self.log.error("Cannot get device name for device : {}".format(device))

# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    def setup(self):
        # The application class sets up logging for us. It is accessible
        # through 'self.log' and is a ncs.log.Log instance.
        self.log.info('Main RUNNING')

        # Service callbacks require a registration for a 'service point',
        # as specified in the corresponding data model.
        #
        self.register_service('network-slice-ns-endpoint-servicepoint', NSlice_end_point)

        # If we registered any callback(s) above, the Application class
        # took care of creating a daemon (related to the service/action point).

        # When this setup method is finished, all registrations are
        # considered done and the application is 'started'.

    def teardown(self):
        # When the application is finished (which would happen if NCS went
        # down, packages were reloaded or some error occurred) this teardown
        # method will be called.

        self.log.info('Main FINISHED')

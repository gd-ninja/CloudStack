# -*- encoding: utf-8 -*-
#
# Copyright (c) 2012 Citrix.  All rights reserved.
#
""" P1 tests for routers
"""
#Import Local Modules
from cloudstackTestCase import *
from cloudstackAPI import *
import remoteSSHClient
from testcase.libs.utils import *
from testcase.libs.base import *
from testcase.libs.common import *

#Import System modules
import time


class Services:
    """Test router Services
    """

    def __init__(self):
        self.services = {
                         "service_offering": {
                                    "name": "Tiny Instance",
                                    "displaytext": "Tiny Instance",
                                    "cpunumber": 1,
                                    "cpuspeed": 100, # in MHz
                                    "memory": 256, # In MBs
                                    },
                        "virtual_machine":
                                    {
                                        "displayname": "Test VM",
                                        "username": "root",
                                        "password": "fr3sca",
                                        "ssh_port": 22,
                                        "hypervisor": 'XenServer',
                                        # Hypervisor type should be same as
                                        # hypervisor type of cluster
                                        "domainid": 1,
                                        "privateport": 22,
                                        "publicport": 22,
                                        "protocol": 'TCP',
                                },
                        "account": {
                                        "email": "test@test.com",
                                        "firstname": "Test",
                                        "lastname": "User",
                                        "username": "testuser",
                                        "password": "password",
                                    },
                        "natrule":
                                {
                                    "privateport": 22,
                                    "publicport": 222,
                                    "protocol": "TCP"
                                },
                         "lbrule":
                                {
                                    "name": "SSH",
                                    "alg": "roundrobin",
                                    # Algorithm used for load balancing
                                    "privateport": 80,
                                    "publicport": 2222,
                                },
                         "fw_rule":{
                                    "startport": 1,
                                    "endport": 6000,
                                    "cidr": '55.55.0.0/11',
                                    # Any network (For creating FW rule
                                    },
                         "ostypeid":12,
                         # Used for Get_Template : CentOS 5.3 (64 bit)
                         "zoneid": 1,
                         # Optional, if specified the mentioned zone will be
                         # used for tests
                         "mode": 'advanced', # Networking mode: Advanced, basic
                        }


class TestRouterServices(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):

        cls.api_client = fetch_api_client()
        cls.services = Services().services
        # Get Zone, Domain and templates
        cls.zone = get_zone(cls.api_client, cls.services)
        cls.template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostypeid"]
                            )
        cls.services["virtual_machine"]["zoneid"] = cls.zone.id

        #Create an account, network, VM and IP addresses
        cls.account = Account.create(
                                     cls.api_client,
                                     cls.services["account"],
                                     admin=True
                                     )
        cls.service_offering = ServiceOffering.create(
                                            cls.api_client,
                                            cls.services["service_offering"]
                                            )
        cls.vm_1 = VirtualMachine.create(
                                    cls.api_client,
                                    cls.services["virtual_machine"],
                                    templateid=cls.template.id,
                                    accountid=cls.account.account.name,
                                    serviceofferingid=cls.service_offering.id
                                    )
        cls.vm_2 = VirtualMachine.create(
                                    cls.api_client,
                                    cls.services["virtual_machine"],
                                    templateid=cls.template.id,
                                    accountid=cls.account.account.name,
                                    serviceofferingid=cls.service_offering.id
                                    )
        cls.cleanup = [
                       cls.account,
                       cls.service_offering
                       ]
        return

    @classmethod
    def tearDownClass(cls):
        try:
            cls.api_client = fetch_api_client()
            #Clean up, terminate the created templates
            cleanup_resources(cls.api_client, cls.cleanup)

        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def tearDown(self):
        try:
            cleanup_resources(self.apiclient, self._cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def setUp(self):
        self.apiclient = self.testClient.getApiClient()
        self._cleanup = []
        return

    def test_01_AdvancedZoneRouterServices(self):
        """Test advanced zone router services
        """

        # Validate the following:
        # 1. Verify that list of services provided by this network are running
        #    a. DNS
        #    b. DHCP
        #    c. Gateway
        #    d. Firewall
        #    e. LB
        #    f. VPN
        #    g. userdata
        # 2. wait for router to start and guest network to be created 
        #    a. listRouters account=user, domainid=1 (router state=Running)
        #    b. listNetworks account=user domainid=1 (network state=Implemented)
        #    c. listVirtualMachines account=user domainid=1 (VM state=Running)
        # 3. listNetwork

        routers = list_routers(
                               self.apiclient,
                               account=self.account.account.name,
                               domainid=self.account.account.domainid,
                               )

        self.assertNotEqual(
                             len(routers),
                             0,
                             "Check list router response"
                             )
        for router in routers:
            self.assertEqual(
                        router.state,
                        'Running',
                        "Check list router response for router state"
                    )
        # Network state associated with account should be 'Implemented'
        networks = list_networks(
                                 self.apiclient,
                                 account=self.account.account.name,
                                 domainid=self.account.account.domainid,
                                 )
        self.assertNotEqual(
                             len(networks),
                             0,
                             "Check list networks response"
                             )
        for network in networks:
            self.assertEqual(
                        network.state,
                        'Implemented',
                        "Check list network response for network state"
                    )
        # VM state associated with account should be 'Running'
        virtual_machines = list_virtual_machines(
                                self.apiclient,
                                account=self.account.account.name,
                                domainid=self.account.account.domainid
                                )

        self.assertNotEqual(
                             len(virtual_machines),
                             0,
                             "Check list virtual machines response"
                             )
        for virtual_machine in virtual_machines:
            self.assertEqual(
                        virtual_machine.state,
                        'Running',
                        "Check list VM response for Running state"
                    )

        hosts = list_hosts(
                           self.apiclient,
                           id=routers[0].hostid
                           )

        # Check status of DNS, DHCP, FIrewall, LB VPN processes
        networks = list_networks(
                                 self.apiclient,
                                 account=self.account.account.name,
                                 domainid=self.account.account.domainid,
                                 )
        self.assertNotEqual(
                             len(networks),
                             0,
                             "Check list networks response"
                             )
        # Load Balancer, Userdata, VPN, Firewall, Gateway, DNS processes should
        # be running
        for network in networks:
            self.assertEqual(
                        'Lb' in str(network.service),
                        True,
                        "Check Load balancing process in list networks"
                    )
            self.assertEqual(
                        'UserData' in str(network.service),
                        True,
                        "Check UserData service in list networks"
                    )
            self.assertEqual(
                        'Vpn' in str(network.service),
                        True,
                        "Check Vpn service in list networks"
                    )
            self.assertEqual(
                        'Firewall' in str(network.service),
                        True,
                        "Check Firewall service in list networks"
                    )
            self.assertEqual(
                        'Gateway' in str(network.service),
                        True,
                        "Check Gateway service in list networks"
                    )
            self.assertEqual(
                        'Dns' in str(network.service),
                        True,
                        "Check Dns service in list networks"
                    )
        return

    def test_02_NetworkGarbageCollection(self):
        """Test network garbage collection
        """

        # Validate the following
        # 1. wait for router to start and guest network to be created 
        #    a.listRouters account=user, domainid=1 (router state=Running)
        #    b.listNetworks account=user domainid=1 (network state=Implemented)
        #    c.listVirtualMachines account=user domainid=1 (VM states=Running)
        # 4. stopVirtualMachines (stop all VMs in this account)
        # 5. wait for VMs to stop-listVirtualMachines account=user, domainid=1
        #    (Both VM states = Stopped)
        # 6. wait for network.gc.interval*2 seconds (600s)
        # 7. listRouters account=user, domainid=1

        routers = list_routers(
                               self.apiclient,
                               account=self.account.account.name,
                               domainid=self.account.account.domainid,
                               )

        self.assertNotEqual(
                             len(routers),
                             0,
                             "Check list router response"
                             )
        # Router associated with account should be in running state
        for router in routers:
            self.assertEqual(
                        router.state,
                        'Running',
                        "Check list router response for router state"
                    )
        # Network state associated with account should be 'Implemented'
        networks = list_networks(
                                 self.apiclient,
                                 account=self.account.account.name,
                                 domainid=self.account.account.domainid,
                                 )
        self.assertNotEqual(
                             len(networks),
                             0,
                             "Check list networks response"
                             )
        # Check if network in 'Implemented' state
        for network in networks:
            self.assertEqual(
                        network.state,
                        'Implemented',
                        "Check list network response for network state"
                    )
        # VM state associated with account should be 'Running'
        virtual_machines = list_virtual_machines(
                                self.apiclient,
                                account=self.account.account.name,
                                domainid=self.account.account.domainid,
                                )

        self.assertNotEqual(
                             len(virtual_machines),
                             0,
                             "Check list virtual machines response"
                             )
        for virtual_machine in virtual_machines:
            self.assertEqual(
                        virtual_machine.state,
                        'Running',
                        "Check list VM response for Running state"
                    )
            # Stop virtual machine
            cmd = stopVirtualMachine.stopVirtualMachineCmd()
            cmd.id = virtual_machine.id
            self.apiclient.stopVirtualMachine(cmd)

        interval = list_configurations(
                                    self.apiclient,
                                    name='network.gc.interval'
                                    )
        # Router is stopped after (network.gc.interval *2) time. Wait for
        # (network.gc.interval *4) for moving router to 'Stopped' 
        time.sleep(int(interval[0].value) * 4)

        routers = list_routers(
                               self.apiclient,
                               account=self.account.account.name,
                               domainid=self.account.account.domainid,
                               )

        self.assertNotEqual(
                             len(routers),
                             0,
                             "Check list router response"
                             )
        for router in routers:
            self.assertEqual(
                        router.state,
                        'Stopped',
                        "Check list router response for router state"
                    )
        # Cleanup Vm_2 - Not required for further tests
        self._cleanup.append(self.vm_2)
        return

    def test_03_RouterStartOnVmDeploy(self):
        """Test router start on VM deploy
        """
        # Validate the following
        # 1. deployVirtualMachine in the account
        # 2. listVirtualMachines account=user, domainid=1
        # 3. when listVirtualMachines reports the userVM to be in state=Running
        # 4. listRouters should report router to have come back to "Running" state
        # 5. All other VMs in the account should remain in "Stopped" state

        vm = VirtualMachine.create(
                                    self.apiclient,
                                    self.services["virtual_machine"],
                                    templateid=self.template.id,
                                    accountid=self.account.account.name,
                                    serviceofferingid=self.service_offering.id
                                    )

        virtual_machines = list_virtual_machines(
                                self.apiclient,
                                id=vm.id,
                                account=self.account.account.name,
                                domainid=self.account.account.domainid,
                                )

        self.assertNotEqual(
                             len(virtual_machines),
                             0,
                             "Check list virtual machines response"
                             )
        # VM state should be 'Running'
        for virtual_machine in virtual_machines:
            self.assertEqual(
                        virtual_machine.state,
                        'Running',
                        "Check list VM response for Running state"
                    )

        routers = list_routers(
                               self.apiclient,
                               account=self.account.account.name,
                               domainid=self.account.account.domainid,
                               )

        self.assertNotEqual(
                             len(routers),
                             0,
                             "Check list router response"
                             )
        # Routers associated with account should be 'Running' after deployment
        # of VM
        for router in routers:
            self.assertEqual(
                        router.state,
                        'Running',
                        "Check list router response for router state"
                    )

        # All other VMs (VM_1) should be in 'Stopped'
        virtual_machines = list_virtual_machines(
                                self.apiclient,
                                id=self.vm_1.id,
                                account=self.account.account.name,
                                domainid=self.account.account.domainid,
                                )

        self.assertNotEqual(
                             len(virtual_machines),
                             0,
                             "Check list virtual machines response"
                             )
        for virtual_machine in virtual_machines:
            self.assertEqual(
                        virtual_machine.state,
                        'Stopped',
                        "Check list VM response for Stopped state"
                    )
        return


class TestRouterStopAssociateIp(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):

        cls.api_client = fetch_api_client()
        cls.services = Services().services
        # Get Zone, Domain and templates
        cls.zone = get_zone(cls.api_client, cls.services)
        template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostypeid"]
                            )
        cls.services["virtual_machine"]["zoneid"] = cls.zone.id

        #Create an account, network, VM and IP addresses
        cls.account = Account.create(
                                     cls.api_client,
                                     cls.services["account"]
                                     )
        cls.service_offering = ServiceOffering.create(
                                            cls.api_client,
                                            cls.services["service_offering"]
                                            )
        cls.vm_1 = VirtualMachine.create(
                                    cls.api_client,
                                    cls.services["virtual_machine"],
                                    templateid=template.id,
                                    accountid=cls.account.account.name,
                                    serviceofferingid=cls.service_offering.id
                                    )
        cls.cleanup = [
                       cls.account,
                       cls.service_offering
                       ]
        return

    @classmethod
    def tearDownClass(cls):
        try:
            cls.api_client = fetch_api_client()
            # Clean up resources
            cleanup_resources(cls.api_client, cls.cleanup)

        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def tearDown(self):
        try:
            # Clean up resources
            cleanup_resources(self.apiclient, self._cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def setUp(self):
        self.apiclient = self.testClient.getApiClient()
        self._cleanup = []
        return

    def test_01_RouterStopAssociateIp(self):
        """Test router stop associate IP
        """

        # validate the following
        # 1. wait for router to start, guest network to be implemented and
        #    VM to report Running
        # 2. stopRouter for this account
        # 3. wait for listRouters to report Router as 'Stopped'
        # 4. associateIpAddress account=user, zoneid=<z>, domainid=1,
        #    networkid=<from listNetworks>
        # 5. startRouter stopped in step 3.
        # 6. wait for listRouters to show router as Running
        # 7. listPublicIpAddress with id as given when associateIpAddress was
        #    called state of IP should be 'Allocated'
        # 8. listRouter account=user, get the link-local-ip and the hostid
        # 9. listHosts with hostid from step 3.
        # 10. double-hop into Router (ssh) through the host it is resident on
        # 11. "ip addr show" should give you the associateIpAddress on eth2

        # Get router details associated with account
        routers = list_routers(
                               self.apiclient,
                               account=self.account.account.name,
                               domainid=self.account.account.domainid,
                               )

        self.assertNotEqual(
                             len(routers),
                             0,
                             "Check list router response"
                             )

        router = routers[0]

        #Stop the router
        cmd = stopRouter.stopRouterCmd()
        cmd.id = router.id
        self.apiclient.stopRouter(cmd)

        routers = list_routers(
                               self.apiclient,
                               account=self.account.account.name,
                               domainid=self.account.account.domainid,
                               )
        router = routers[0]

        self.assertEqual(
                    router.state,
                    'Stopped',
                    "Check list router response for router state"
                    )

        networks = list_networks(
                                 self.apiclient,
                                 account=self.account.account.name,
                                 domainid=self.account.account.domainid,
                                 )
        self.assertNotEqual(
                             len(networks),
                             0,
                             "Check list networks response"
                             )
        network = networks[0]
        # Associate IP address with account
        public_ip = PublicIPAddress.create(
                                self.apiclient,
                                accountid=self.account.account.name,
                                zoneid=self.zone.id,
                                domainid=self.account.account.domainid,
                                networkid=network.id
                                )
        #Start the router
        cmd = startRouter.startRouterCmd()
        cmd.id = router.id
        self.apiclient.startRouter(cmd)

        routers = list_routers(
                               self.apiclient,
                               account=self.account.account.name,
                               domainid=self.account.account.domainid,
                               )
        router = routers[0]
        # Check if router is in Running state
        self.assertEqual(
                    router.state,
                    'Running',
                    "Check list router response for router state"
                    )
    # Check if Public IP is in Allocated state
        public_ips = list_publicIP(
                                   self.apiclient,
                                   id=public_ip.ipaddress.id
                                   )
        self.assertEqual(
                    public_ips[0].state,
                    'Allocated',
                    "Check list public IP response"
                    )

        hosts = list_hosts(
                           self.apiclient,
                           id=router.hostid,
                           )
        host = hosts[0]
        # For DNS and DHCP check 'dnsmasq' process status
        result = get_process_status(
                                host.ipaddress,
                                self.services['virtual_machine']["publicport"],
                                self.vm_1.username,
                                self.vm_1.password,
                                router.linklocalip,
                                'ip addr show'
                                )
        self.assertEqual(
                            result.count(str(public_ip.ipaddress.ipaddress)),
                            1,
                            "Check public IP address"
                        )
        return


class TestRouterStopCreatePF(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):

        cls.api_client = fetch_api_client()
        cls.services = Services().services
        # Get Zone, Domain and templates
        cls.zone = get_zone(cls.api_client, cls.services)
        template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostypeid"]
                            )
        cls.services["virtual_machine"]["zoneid"] = cls.zone.id

        #Create an account, network, VM and IP addresses
        cls.account = Account.create(
                                     cls.api_client,
                                     cls.services["account"],
                                     admin=True
                                     )
        cls.service_offering = ServiceOffering.create(
                                            cls.api_client,
                                            cls.services["service_offering"]
                                            )
        cls.vm_1 = VirtualMachine.create(
                                    cls.api_client,
                                    cls.services["virtual_machine"],
                                    templateid=template.id,
                                    accountid=cls.account.account.name,
                                    serviceofferingid=cls.service_offering.id
                                    )
        cls.cleanup = [
                       cls.account,
                       cls.service_offering
                       ]
        return

    @classmethod
    def tearDownClass(cls):
        try:
            cls.api_client = fetch_api_client()
            # Clean up, terminate the created resources
            cleanup_resources(cls.api_client, cls.cleanup)

        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def tearDown(self):
        try:
            # Clean up, terminate the created resources
            cleanup_resources(self.apiclient, self._cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def setUp(self):
        self.apiclient = self.testClient.getApiClient()
        self._cleanup = []
        return

    def test_01_RouterStopCreatePF(self):
        """Test router stop create port forwarding
        """

        # validate the following
        # 1. wait for router to start, guest network to be implemented and
        #    VM to report Running
        # 2. stopRouter for this account
        # 3. wait for listRouters to report Router as 'Stopped'
        # 4. listPublicIpAddresses account=user, domainid=1 - pick ipaddressid
        # 5. createPortForwardingRule (ipaddressid from step 5.) 
        #    a. for port 22 (ssh) for user VM deployed in step 1.
        #    b. public port 222 , private port 22
        # 6. startRouter stopped for this account 
        # 7. wait for listRouters to show router as Running

        # Get router details associated for that account
        routers = list_routers(
                               self.apiclient,
                               account=self.account.account.name,
                               domainid=self.account.account.domainid,
                               )

        self.assertNotEqual(
                             len(routers),
                             0,
                             "Check list router response"
                             )
        router = routers[0]

        #Stop the router
        cmd = stopRouter.stopRouterCmd()
        cmd.id = router.id
        self.apiclient.stopRouter(cmd)

        routers = list_routers(
                               self.apiclient,
                               account=self.account.account.name,
                               domainid=self.account.account.domainid,
                               )
        router = routers[0]

        self.assertEqual(
                    router.state,
                    'Stopped',
                    "Check list router response for router state"
                    )

        public_ips = list_publicIP(
                                   self.apiclient,
                                   account=self.account.account.name,
                                   domainid=self.account.account.domainid,
                                   zoneid=self.zone.id
                                   )
        public_ip = public_ips[0]

        #Create NAT rule
        nat_rule = NATRule.create(
                        self.apiclient,
                        self.vm_1,
                        self.services["natrule"],
                        public_ip.id
                        )

        #Start the router
        cmd = startRouter.startRouterCmd()
        cmd.id = router.id
        self.apiclient.startRouter(cmd)

        routers = list_routers(
                               self.apiclient,
                               account=self.account.account.name,
                               domainid=self.account.account.domainid,
                               zoneid=self.zone.id
                               )
        router = routers[0]

        self.assertEqual(
                    router.state,
                    'Running',
                    "Check list router response for router state"
                    )
        # NAT Rule should be in Active state after router start
        nat_rules = list_nat_rules(
                                   self.apiclient,
                                   id=nat_rule.id
                                   )
        self.assertEqual(
                    nat_rules[0].state,
                    'Active',
                    "Check list port forwarding rules"
                    )
        try:
            remoteSSHClient.remoteSSHClient(
                                            nat_rule.ipaddress,
                                            nat_rule.publicport,
                                            self.vm_1.username,
                                            self.vm_1.password
                                            )
        except Exception as e:
            self.fail(
                      "SSH Access failed for %s: %s" % \
                      (self.vm_1.ipaddress, e)
                      )
        return

class TestRouterStopCreateLB(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):

        cls.api_client = fetch_api_client()
        cls.services = Services().services
        # Get Zone, Domain and templates
        cls.zone = get_zone(cls.api_client)
        template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostypeid"]
                            )
        cls.services["virtual_machine"]["zoneid"] = cls.zone.id

        #Create an account, network, VM and IP addresses
        cls.account = Account.create(
                                     cls.api_client,
                                     cls.services["account"],
                                     admin=True
                                     )
        cls.service_offering = ServiceOffering.create(
                                            cls.api_client,
                                            cls.services["service_offering"]
                                            )
        cls.vm_1 = VirtualMachine.create(
                                    cls.api_client,
                                    cls.services["virtual_machine"],
                                    templateid=template.id,
                                    accountid=cls.account.account.name,
                                    serviceofferingid=cls.service_offering.id
                                    )
        cls.cleanup = [
                       cls.account,
                       cls.service_offering
                       ]
        return

    @classmethod
    def tearDownClass(cls):
        try:
            cls.api_client = fetch_api_client()
            #Clean up, terminate the created resources
            cleanup_resources(cls.api_client, cls.cleanup)

        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def tearDown(self):
        try:
            cleanup_resources(self.apiclient, self._cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def setUp(self):
        self.apiclient = self.testClient.getApiClient()
        self._cleanup = []
        return

    def test_01_RouterStopCreateLB(self):
        """Test router stop create Load balancing
        """

        # validate the following
        # 1. listLoadBalancerRules (publicipid=ipaddressid of source NAT)
        # 2. rule should be for port 2222 as applied and
        #    should be in state=Active
        # 3. ssh access should be allowed to the userVMs over the source NAT IP
        #    and port 2222

        # Get router details associated for that account
        routers = list_routers(
                               self.apiclient,
                               account=self.account.account.name,
                               domainid=self.account.account.domainid,
                               )

        self.assertNotEqual(
                             len(routers),
                             0,
                             "Check list router response"
                             )

        router = routers[0]

        #Stop the router
        cmd = stopRouter.stopRouterCmd()
        cmd.id = router.id
        self.apiclient.stopRouter(cmd)

        routers = list_routers(
                               self.apiclient,
                               account=self.account.account.name,
                               domainid=self.account.account.domainid,
                               )
        router = routers[0]

        self.assertEqual(
                    router.state,
                    'Stopped',
                    "Check list router response for router state"
                    )

        public_ips = list_publicIP(
                                   self.apiclient,
                                   account=self.account.account.name,
                                   domainid=self.account.account.domainid
                                   )
        public_ip = public_ips[0]

        #Create Load Balancer rule and assign VMs to rule
        lb_rule = LoadBalancerRule.create(
                                          self.apiclient,
                                          self.services["lbrule"],
                                          public_ip.id,
                                          accountid=self.account.account.name
                                          )
        lb_rule.assign(self.apiclient, [self.vm_1])

        #Start the router
        cmd = startRouter.startRouterCmd()
        cmd.id = router.id
        self.apiclient.startRouter(cmd)

        routers = list_routers(
                               self.apiclient,
                               account=self.account.account.name,
                               domainid=self.account.account.domainid,
                               )
        router = routers[0]

        self.assertEqual(
                    router.state,
                    'Running',
                    "Check list router response for router state"
                    )
        # After router start, LB RUle should be in Active state
        lb_rules = list_lb_rules(
                                   self.apiclient,
                                   id=lb_rule.id
                                   )
        self.assertEqual(
                    lb_rules[0].state,
                    'Active',
                    "Check list load balancing rules"
                    )
        self.assertEqual(
                    lb_rules[0].publicport,
                    str(self.services["lbrule"]["publicport"]),
                    "Check list load balancing rules"
                    )

        try:
            remoteSSHClient.remoteSSHClient(
                                    public_ip.ipaddress,
                                    self.services["lb_rule"]["publicport"],
                                    self.vm_1.username,
                                    self.vm_1.password
                                    )
        except Exception as e:
            self.fail(
                      "SSH Access failed for %s: %s" % \
                      (self.vm_1.ipaddress, e)
                      )
        return

class TestRouterStopCreateFW(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):

        cls.api_client = fetch_api_client()
        cls.services = Services().services
        # Get Zone, Domain and templates
        cls.zone = get_zone(cls.api_client, cls.services)
        template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostypeid"]
                            )
        cls.services["virtual_machine"]["zoneid"] = cls.zone.id

        #Create an account, network, VM and IP addresses
        cls.account = Account.create(
                                     cls.api_client,
                                     cls.services["account"]
                                     )
        cls.service_offering = ServiceOffering.create(
                                            cls.api_client,
                                            cls.services["service_offering"]
                                            )
        cls.vm_1 = VirtualMachine.create(
                                    cls.api_client,
                                    cls.services["virtual_machine"],
                                    templateid=template.id,
                                    accountid=cls.account.account.name,
                                    serviceofferingid=cls.service_offering.id
                                    )
        cls.cleanup = [
                       cls.account,
                       cls.service_offering
                       ]
        return

    @classmethod
    def tearDownClass(cls):
        try:
            cls.api_client = fetch_api_client()
            #Clean up, terminate the created templates
            cleanup_resources(cls.api_client, cls.cleanup)

        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def tearDown(self):
        try:
            cleanup_resources(self.apiclient, self._cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def setUp(self):
        self.apiclient = self.testClient.getApiClient()
        self._cleanup = []
        return

    def test_01_RouterStopCreateFW(self):
        """Test router stop create Firewall rule
        """

        # validate the following
        # 1. 1. listFirewallRules (filter by ipaddressid of sourcenat)
        # 2. rule should be for ports 1-600 and in state=Active
        #    (optional backend)
        # 3. verify on router using iptables -t nat -nvx if rules are applied

        # Get the router details associated with account 
        routers = list_routers(
                               self.apiclient,
                               account=self.account.account.name,
                               domainid=self.account.account.domainid,
                               )

        self.assertNotEqual(
                             len(routers),
                             0,
                             "Check list router response"
                             )

        router = routers[0]

        #Stop the router
        cmd = stopRouter.stopRouterCmd()
        cmd.id = router.id
        self.apiclient.stopRouter(cmd)

        routers = list_routers(
                               self.apiclient,
                               account=self.account.account.name,
                               domainid=self.account.account.domainid,
                               )
        router = routers[0]

        self.assertEqual(
                    router.state,
                    'Stopped',
                    "Check list router response for router state"
                    )

        public_ips = list_publicIP(
                                   self.apiclient,
                                   account=self.account.account.name,
                                   domainid=self.account.account.domainid
                                   )
        public_ip = public_ips[0]

        #Create Firewall rule with configurations from settings file
        fw_rule = FireWallRule.create(
                            self.apiclient,
                            ipaddressid=public_ip.id,
                            protocol='TCP',
                            cidrlist=[self.services["fw_rule"]["cidr"]],
                            startport=self.services["fw_rule"]["startport"],
                            endport=self.services["fw_rule"]["endport"]
                            )
        # Cleanup after tests
        self._cleanup.append(fw_rule)

        #Start the router
        cmd = startRouter.startRouterCmd()
        cmd.id = router.id
        self.apiclient.startRouter(cmd)

        routers = list_routers(
                               self.apiclient,
                               account=self.account.account.name,
                               domainid=self.account.account.domainid,
                               )
        router = routers[0]

        self.assertEqual(
                    router.state,
                    'Running',
                    "Check list router response for router state"
                    )
        # After Router start, FW rule should be in Active state
        fw_rules = list_firewall_rules(
                                   self.apiclient,
                                   ipaddressid=public_ip.id
                                   )
        self.assertEqual(
                    fw_rules[0].state,
                    'Active',
                    "Check list load balancing rules"
                    )
        self.assertEqual(
                    fw_rules[0].startport,
                    str(self.services["fw_rule"]["startport"]),
                    "Check start port of firewall rule"
                    )

        self.assertEqual(
                    fw_rules[0].endport,
                    str(self.services["fw_rule"]["endport"]),
                    "Check end port of firewall rule"
                    )
        hosts = list_hosts(
                           self.apiclient,
                           id=router.hostid,
                           )
        host = hosts[0]
        # For DNS and DHCP check 'dnsmasq' process status
        result = get_process_status(
                                host.ipaddress,
                                self.services['virtual_machine']["publicport"],
                                self.vm_1.username,
                                self.vm_1.password,
                                router.linklocalip,
                                'iptables -t nat -nvx'
                                )
        # TODO : Find assertion condition                        )
        self.assertEqual(
                            result.count(str(public_ip.ipaddress.ipaddress)),
                            1,
                            "Check public IP address"
                        )
        return

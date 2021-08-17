
# NSO Developers

This section describes how to develop a service application. 

A service application maps input parameters to create, modify, and delete a
service instance into the resulting commands to devices in the network. 

The input parameters are given from a northbound interface to NSO or 
a network engineer using any of the NSO User Interfaces such as the NSO CLI.

![Cisco-NSO-Logical-Architecture](images/NSO_Package_Structure.png)

Who writes the NBI and SBI models?

- Developing the service model is part of developing the service
  application and is covered later in this chapter.

- Every device NED comes with a corresponding device YANG model. This
  model has been designed by the NED developer to capture the
  configuration data that is supported by the device. This means that a
  service application has two primary.



>### NED (Network Element Driver) 
>
>Is the adaptation layer between the XML representation of the network configuration contained inside NSO and the wire protocol between NSO and managed devices. 
>
>**SNPM**: Devices can be managed automatically, by supplying NSO with the MIBs for the device, with some additional declarative annotations. 
>
>**CLI**: Devices can be managed by writing YANG models describing the data in the CLI, and a relatively thin layer of Java code to handle the communication to the devices. **The key point though, is that the Cisco CLI NED Java programmer doesn't have to understand and parse the structure of the CLI, this is entirely done by the NSO CLI engine.**
>
>**Generic**: Devices can be managed by writing a required Java program to translate operations on the NSO XML tree into configuration operations towards the device. (this may be more complicated)
>
>![cisco-ned-architecture](images/cisco-ned-architecture.png)
>
>
>
>



## Creating an NSO Service Application

1. Create a service package: 
`````python 
cd ncs-run/packages
ncs-make-package --service-skeleton python <package-name> 
`````

2. Edit the skeleton YANG service model in the generated package. Move
the YANG source file should be stored in 

````less 
PACKAGE-NAME/src/yang
````

The two lines of uses ncs:service-data and ncs:servicepoint "attribute"
tells NSO that this is a service.

````python 
list vpn-node { key "vpn-node-id ne-id";

    uses ncs:service-data; 
    ncs:servicepoint l3vpn-ntw-vpn-node-servicepoint;
}
````

3. Now build the service model. 
````
pyhton cd <package-name>/src make
````

A nice property of NSO is that already at this point you can load the
service model into NSO and try if it works well in the CLI etc. Nothing
will happen to the devices since the mapping is not defined yet. This
is normally the way to iterate a model; load it into NSO, test the CLI
towards the network engineers, make changes, reload it into NSO etc.

4. Try the service model in the NSO CLI. In order to have NSO to load
the new package including the service model do: 

````pyhton 
admin@ncs#
packages reload 
````

5. Create the XML templates and move it to the template folder of the
package: 
````
pyhton cd <package-name>/tamplate 
````

6. Make sure the service-point name in the YANG service model has a 
corresponding service-point in the XML file or in the main python file. 

````pyhton 
from ncs.application import Service
from ncs.dp import Action


class Main(ncs.application.Application):
    def setup(self):
        # The application class sets up logging for us. It is accessible
        # through 'self.log' and is a ncs.log.Log instance.
        self.log.info('Main RUNNING')

        # Service callbacks require a registration for a 'service point',
        # as specified in the corresponding data model.
        #
        self.register_service('l3vpn-ntw-site-network-access-servicepoint', 
        L3VPNSiteNetworkAccess)
        self.register_service('l3vpn-ntw-vpn-node-servicepoint', L3VPN_VPNNode)

````
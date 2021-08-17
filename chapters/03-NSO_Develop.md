# NSO Developers

## Architecture

![NSO-DEV-Architecture](images/NSO-DEV-Architecture.png)

Next two main layers are described:

**Device Manager**: Supports functions like device templates, device groups, configuration changes, configuration view and audit. The Device Manager does all this in a generic way and sits north of the Network Element Drivers.

>### NED (Network Element Driver) 
>
>Is the adaptation layer between the XML representation of the network configuration (YANG data-model for the supported device) contained inside NSO and the wire protocol between NSO and managed devices. NEDs are separate packages. Every individual NED packages is for a specific device OS.
>
>**SNPM**: Devices can be managed automatically, by supplying NSO with the MIBs for the device, with some additional declarative annotations. 
>
>**CLI**: Devices can be managed by writing YANG models describing the data in the CLI, and a relatively thin layer of Java code to handle the communication to the devices. **The key point though, is that the Cisco CLI NED Java programmer doesn't have to understand and parse the structure of the CLI, this is entirely done by the NSO CLI engine.**
>
>**Generic**: Devices can be managed by writing a required Java program to translate operations on the NSO XML tree into configuration operations towards the device. (this may be more complicated), usually devices that have other proprietary CLIs, devices that can only be configured over other protocols such as REST, Corba, XML-RPC, SOAP, other proprietary XML solutions.
>
>![cisco-ned-architecture](images/cisco-ned-architecture.png)

**Service Manager**: Configure devices using service-aware applications, each service type is a package that is defined exactly according to the specific requirements. It can be modified and re-loaded into a running system, giving flexibility in the service portfolio. 

The main parts of a service package is a YANG Service Model and a mapping definition towards the desired configurations. **The Service Manager supports the full life-cycle for a service.**

A dedicated built-in storage (Configuration DataBase CDB) has the next advantages compared with external storage:

- A solid model on how to handle configuration data in network devices, including a good update subscription mechanism.
- A TCP based API whereby it is possible to read and subscribe to changes to the network remotely.
- Fast lightweight database access. CDB by default keeps the entire configuration in RAM as well as on disk.
- Ease of use. CDB is already integrated into NSO, the database is lightweight and has no maintenance needs. Writing instrumentation functions to access data is easy.
- Automatic support for upgrade and downgrade of configuration data. 

## Python VM

## Troubleshooting

## NBI: Yang Model

## SBI: NED Component

## Subscriptions

## APIs (Java & Py)

## Service Packages

## Service Application Development



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

## Creating an NSO Service Application

1. Create a service package: 
`````python 
cd ncs-run/packages
ncs-make-package --service-skeleton python <package-name> 
`````

2. Edit the skeleton YANG service model in the generated package. Move the YANG source file that should be stored in:

````less 
PACKAGE-NAME/src/yang
````

The two ***"uses"*** lines ncs:service-data and ncs:servicepoint "attribute" tells NSO that this is a service.

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

A nice property of NSO is that already at this point you can load the service model into NSO and try if it works well in the CLI etc. Nothing will happen to the devices since the mapping is not defined yet. This is normally the way to iterate a model; load it into NSO, test the CLI towards the network engineers, make changes, reload it into NSO etc.

4. Try the service model in the NSO CLI. In order to have NSO to load the new package including the service model, do: 

````pyhton 
admin@ncs#
packages reload 
````

5. Create the XML templates and move it to the template folder of the package: 
````
pyhton cd <package-name>/template 
````

6. Make sure the service-point name in the YANG service model has a corresponding service-point in the XML file or in the main python file. 

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
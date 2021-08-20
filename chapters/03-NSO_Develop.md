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

## Python VM

The Python VM does not run on a hypervisor and does not contain a guest operating system. It is a tool that allows programs written in the Python programming language to run on a variety of CPUs.

Similar to Java, Python translates its programs into an intermediate format called bytecode, storing it in a file ready for execution. When the program is executed, the Python VM converts the bytecode into machine code for fast execution.

![Python_VM](images/Python_VM.png)

NSO is able to start one or more Python VMs where Python code in user-supplied packages can be executed.

By default, a Python VM will be started for each Python package that has a python class name defined in its package-meta-data.xml file. In this Python VM the environment variable PYTHONPATH will point to the python directory of the package.

The tailf-ncs-python-vm.yang defines the *python-vm* container which, along with ncs.conf, is the entry point for controlling the NSO Python VM functionality:

`````xml
+--rw python-vm
	+--rw logging
	|...
	|# More data 
	|...
	+--rw status
	|	+--ro start* [node-id]
	|	|...
	|	|# More data
	|	|...
	|	+--ro current* [node-id
	|
	+---x stop
	|		|..
	|		|# More data
	|		|..
	+---x start
			|..
			|# More data
			|..
`````

- The *status/start* and *status/current* contains operational data.
- The *status/start* command will show information about what Python classes, as declared in the package-meta-data.xml file, that where started and whether the outcome was successful or not. 
- The *status/current* command will show which Python classes that are currently running in a separate thread.
- The *start* and *stop* actions makes it possible to start and stop a particular Python VM.

#### Structure of the User provided code

The package-meta-data.xml file must contain a *component* of type *application* with a *python-class- name* specified, where the component name (Service Name in the example) is a human readable name of this application component. 

`````xml
<component>
<name>Service Name</name> <application>
<python-class-name>Name.service.Service</python-class-name> </application>
</component>
`````

The *python-class-name* should specify the Python class that implements the application entry point. 

**Note**: the application entry point MUST to be specified using Python's dot-notation and should be fully qualified (given the fact that *PYTHONPATH* is pointing to the package python directory).

#### Python package directory structure

Note that directly above the main directory is another directory named as the package (Name) that contains the user code.

`````xml
packages/ 
+-- {{Name}}/
	+-- package-meta-data.xml
	+-- python/
	| 	+-- {{Name}}/
	|				+-- __init__.py
	|				+-- service.py
	|				+-- _namespaces/
	|						+-- __init__.py 
	|						+-- {{Name}}_ns.py
	+-- src
			+-- Makefile 
			+-- yang/
					+-- {{Name}}.yang
`````

- The **service.py** is located according to the description above. There is also a **__init__.py** (which is empty) there to make the {{Name}} directory considered a *module* from Python's perspective.
- The **_namespaces/{{Name}}_ns.py** file. It is generated from the **{{Name}}.yang** model using the **ncsc --emit-python** command and contains constants representing the namespace and the various components of the YANG model, which the User code can import and make use of.
- The **service.py** file should include a class definition named *Service* which acts as the component's entry point.
- A Python class specified in the **package-meta-data.xml** file will be started in a Python thread which we call a *component thread*. 
- The Python class should inherit ***ncs.application.Application*** and should implement the methods ***setup()*** and ***teardown()***.

Example of component class skeleton:

`````python
import ncs

class Service(ncs.application.Application): 
	def setup(self):
	# The application class sets up logging for us. It is accessible 
	# through 'self.log' and is a ncs.log.Log instance. 
	self.log.info('Service RUNNING')

	# Service callbacks require a registration for a 'service point', 
	# as specified in the corresponding data model.
	self.register_service('{{Name}}-servicepoint', ServiceCallbacks)

	# If we registered any callback(s) above, the Application class
	# took care of creating a daemon (related to the service/action point).

	# When this setup method is finished, all registrations are 
	# considered done and the application is 'started'.
	def teardown(self):
	# When the application is finished (which would happen if NCS went 
	# down, packages were reloaded or some error occurred) this teardown 
	# method will be called.
	self.log.info('Service FINISHED')
`````

- The *Service* class will be instantiated by NSO when started or whenever packages are reloaded. 
- Custom initialization such as registering service- and action callbacks should be done in the *setup()* method. 
- If any cleanup is needed when NSO finishes or when packages are reloaded it should be placed in the *teardown()* method.
- The existing log functions are named after the standard Python log levels, thus in the example above the *self.log* object contains the functions *debug,info,warning,error,critical*.

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

````
ncs-make-package --service-skeleton python iFusion-slice
````

The yang file can be complied inside the NSO using pyang. Some error can appear, so the sentences 'yang-version' and 'reference' in imported files should be removed from Yang.

-   ietf-network-slice@2021-07-20.yang:2: error: bad value "1.1" (should be version)
-   ietf-network-slice@2021-07-20.yang:9: error: unexpected keyword "reference"
-   ietf-network-slice@2021-07-20.yang:14: error: unexpected keyword "reference"
-   ietf-network-slice@2021-07-20.yang:19: error: unexpected keyword "reference"


chmod 777 ietf-network-slice@2021-07-20.yang 


2. Edit the skeleton YANG service model in the generated package. Move the YANG source file that should be stored in:

````less 
PACKAGE-NAME/src/yang
````

The two ***"uses"*** lines ncs:service-data and ncs:servicepoint "attribute" tells NSO that this is a service.

Two additional models should be added in the main yang file: 
````python 
  import tailf-common {
    prefix tailf;
  }
  
  import tailf-ncs {
    prefix ncs;
  }
````

Once those models were imported, the service points can be added:

````python
list vpn-node { key "vpn-node-id ne-id";
    uses ncs:service-data; 
    ncs:servicepoint l3vpn-ntw-vpn-node-servicepoint;
}
````

3. Now build the service model. 
````pyhton 
cd <package-name>/src make
````

If additional models are required, the following lines must be change in the 'Makefile':

````pyhton
## Uncomment and patch the line below if you have a dependency to a NED
## or to other YANG files
YANGPATH += ../../<package-name>/src/yang
YANGPATH += ../../<package-name>/src/yang/import
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
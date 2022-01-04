# NSO Developers

## Architecture

![NSO-DEV-Architecture](images/NSO-DEV-Architecture.png){ width=100% }

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
>![cisco-ned-architecture](images/cisco-ned-architecture.png){ width=40% }

**Service Manager**: Configure devices using service-aware applications, each service type is a package that is defined exactly according to the specific requirements. It can be modified and re-loaded into a running system, giving flexibility in the service portfolio. 

The main parts of a service package is a YANG Service Model and a mapping definition towards the desired configurations. **The Service Manager supports the full life-cycle for a service.**

## Python VM

The Python VM does not run on a hypervisor and does not contain a guest operating system. It is a tool that allows programs written in the Python programming language to run on a variety of CPUs.

Similar to Java, Python translates its programs into an intermediate format called bytecode, storing it in a file ready for execution. When the program is executed, the Python VM converts the bytecode into machine code for fast execution.

![Python VM](images/Python_VM.png){ width=20% }

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

## The Service Algorithm - FastMap

As a Service Developer you need to express the mapping from a YANG service model to the corresponding device
YANG model. This is a declarative mapping in the sense that no sequencing is defined.

Observe that irrespective of the underlying device type and corresponding native device interface, the
mapping is towards a YANG device model, not the native CLI for example. This means that as you write
the service mapping, you do not have to worry about the syntax of different devices' CLI commands or in
which order these commands are sent to the devices. This is all taken care of by the NSO device manager.

NSO reduces this problem to a single data-mapping definition for the "create" scenario. At run-time
NSO will render the minimum change for any possible change like all the ones mentioned below. This is
managed by the FASTMAP algorithm.

FASTMAP covers the complete service life-cycle: creating, changing and deleting the service. The
solution requires a minimum amount of code for mapping from a service model to a device model.

FASTMAP is based on generating changes from an initial create. When the service instance is created
the reverse of the resulting device configuration is stored together with the service instance. If an NSO
user later changes the service instance, NSO first applies (in a transaction) the reverse diff of the service,
effectively undoing the previous results of the service creation code. Then it runs the logic to create the
service again, and finally executes a diff to current configuration. This diff is then sent to the devices.

![Python VM](images/fastmap.png){ width=20% }

## Troubleshooting

## Subscriptions

he CDB subscription mechanism allows an external program to be notified when some part of the configuration changes. When receiving a notification it is also possible to iterate through the changes written to CDB. Subscriptions are always towards the running data-store (it is not possible to subscribe to changes to the startup data-store). Subscriptions towards operational data (see the section called “Operational Data in CDB”) kept in CDB are also possible, but the mechanism is slightly different.

The first thing to do is to inform CDB which paths we want to subscribe to. Registering a path returns a subscription point identifier. This is done by acquiring an subscriber instance by calling CdbSubscription Cdb.newSubscription() method. For the subscriber (or CdbSubscription instance) the paths are registered with the dbSubscription.subscribe() that that returns the actual subscription point identifier. A subscriber can have multiple subscription points, and there can be many different subscribers. Every point is defined through a path - similar to the paths we use for read operations, with the exception that instead of fully instantiated paths to list instances we can selectively use tagpaths.

When a client is done defining subscriptions it should inform NSO that it is ready to receive notifications by calling CdbSubscription.subscribeDone(), after which the subscription socket is ready to be polled.

We can subscribe either to specific leaves, or entire subtrees. Explaining this by example we get:

**/ncs:devices/global-settings/trace**: Subscription to a leaf. Only changes to this leaf will generate a notification.

**/ncs:devices**:  Subscription to the subtree rooted at /ncs:devices. Any changes to this subtree will generate a notification. This includes additions or removals of device instances, as well as changes to already existing device instances.

**/ncs:devices/device{"ex0"}/address**: Subscription to a specific element in a list. A notification will be generated when the device “ex0” changes its ip address.

**/ncs:devices/device/address**:  Subscription to a leaf in a list. A notification will be generated leaf address is changed in *any* device instance.

When adding a subscription point the client must also provide a priority, which is an integer (a smaller number means higher priority). When data in CDB is changed, this change is part of a transaction. A transaction can be initiated by a **commit** operation from the CLI or a **edit-config** operation in NETCONF resulting in the running database being modified. As the last part of the transaction CDB will generate notifications in lock-step priority order. First all subscribers at the lowest numbered priority are handled, once they all have replied and synchronized by calling CdbSubscription.sync() the next set - at the next priority level - is handled by CDB. Not until all subscription points have been acknowledged is the transaction complete. This implies that if the initiator of the transaction was for example a **commit** command in the CLI, the command will hang until notifications have been acknowledged.

Note that even though the notifications are delivered within the transaction it is not possible for a subscriber to reject the changes (since this would break the two-phase commit protocol used by the NSO backplane towards all data-providers).

As a subscriber has read its subscription notifications using CdbSubscription.read() it can iterate through the changes that caused the particular subscription notification using the CdbSubscription.diffIterate() method. It is also possible to start a new read-session to the CdbDBType.CDB_PRE_COMMIT_RUNNING database to read the running database as it was before the pending transaction.

To view registered subscribers use the **ncs --status** command.

## NSO Python API

NCS Python high level module.

The high-level APIs provided by this module are an abstraction on top of the low-level APIs. This makes them easier to use, improves code readability and development rate for common use cases, such as service and action callbacks.

As an example, the maagic module greatly simplifies the way of accessing data. First it helps in navigating the data model, using standard Python object dot notation, giving very clear and readable code. The context handlers remove the need to close sockets, user sessions and transactions. Finally, by removing the need to know the data types of the leafs, allows you to focus on the program logic.

This top module imports the following modules:

- application – module for implementing packages and services
- cdb – placeholder for low-level _ncs.cdb items
- dp – data provider, actions
- error – placeholder for low-level _ncs.error items
- events – placeholder for low-level _ncs.events items
- ha – placeholder for low-level _ncs.ha items
- log – logging utilities
- maagic – data access module
- maapi – MAAPI interface
- template – module for working with templates
- service_log – module for doing service logging
- upgrade – module for writing upgrade components

### Sub-modules

- `ncs.application:`Module for building NCS applications.
- `ncs.cdb:`CDB high level module.
- `ncs.childlist:`Internally used classes and functions.
- `ncs.dp:`Callback module for connecting data providers to ConfD/NCS.
- `ncs.error`
- `ncs.events`
- `ncs.experimental:`Experimental stuff …
- `ncs.fsm:`Internally used classes and functions …
- `ncs.ha`
- `ncs.keypath:`Internally used classes and functions.
- `ncs.log:`This module provides some logging utilities.
- `ncs.maagic:`Confd/NCS data access module …
- `ncs.maapi:`MAAPI high level module …
- `ncs.ns`
- `ncs.pool:`Resource Pool
- `ncs.service_log:`This module provides service logging
- `ncs.template:`This module implements classes to simplify template processing.
- `ncs.tm:`Internally used classes and functions.
- `ncs.upgrade:`Module for NSO upgrade components.
- `ncs.util:`Utility module, low level abstrations

## Service Packages

A package is basically a directory of files with a fixed file structure. A package consists of code, YANG modules, custom Web UI widgets etc., that are needed in order to add an application or function to NSO. Packages is a controlled way to manage loading and versions of custom applications.

A package is a directory where the package name is the same as the directory name. 

At the toplevel of this directory a file called package-meta-data.xml must exist. 

The structure of that file is defined by the YANG model$NCS_DIR/src/ncs/yang/tailf-ncs-packages.yang. 

A package may also be a tar archive with the same directory layout. The tar archive can be either uncompressed with suffix .tar, or gzip-compressed with suffix .tar.gz or .tgz.

![Package-Model](images/Package_model_UML.png){ width=100% }

Packages are composed of components. The following types of components are defined: NED, Application, and Callback.

The file layout of a package is:

```markdown
<package-name>/package-meta-data.xml 
							 load-dir/
							 shared-jar/ 
							 private-jar/ 
							 webui/ 
							 templates/ 
							 src/
							 doc/
							 netsim/
```

Local-dir is the directory where all .fxs (compiled YANG files) and .ccl (compiled CLI spec files) are located.

Shared-jar is the directory where all jars are located and are reach using the LOAD_SHARED_JARS request for each deployed NSO package (the classes and resources in these jars are globally accessible for all deployed NSO packages).

Private-jar is the directory where all jars are located and are reach using the LOAD_PACKAGE request for each deployed NSO package (these classes and resources will be private to respective NSO package. In addition, classes that are referenced in a component tag in respective NSO package package-meta-data.xml file will be instantiated).

**Note**: By putting code for a specific service in a private jar, NSO can dynamically upgrade the service without affecting any other service.

The optional webui directory contains webui customization files.

The package-meta-data.xml file defines the name of the package as well as one *component*. Let's go through the different parts of the meta data file:

- name - the name of the package. All packages in the system must have unique names.

- package-version - The version of the package. This is for administrative purposes only, NSO

  cannot simultaneously handle two versions of the same package.

- ncs-min-version - which is the oldest known NSO version where this package works.

- required-package - a list of names of other packages that are required for this package to work.

- component - Each package defines zero or more components.

Each component in a package has a name. The names of all the components must be unique within the package. 

The YANG model for packages contain:

![Component-structure](images/component-structure.png){ width=100% }

The mandatory choice that defines a component must be one of ***ned***, ***callback***, ***application*** or ***upgrade***.

###### NED Component

A Network Element Driver component is used southbound of NSO to communicate with managed devices. The easiest NED to understand is the NETCONF NED which is built in into NSO.

There are 4 different types of NEDs:

• *netconf* - used for NETCONF enabled devices such as Juniper routers, ConfD powered devices or any device that speaks proper NETCONF and also has YANG models. Plenty of packages in the NSO example collection have NETCONF NED components, for example $NCS_DIR/examples.ncs/getting-started/ developing-with-ncs/0-router-network/packages/router.

• *snmp* - used for SNMP devices.
 The example $NCS_DIR/examples.ncs/snmp-ned/basic has a

package which has an SNMP NED component.
 • *cli* - used for CLI devices. The package $NCS_DIR/packages/neds/

cisco-ios is an example of a package that has a CLI NED component. • *generic* - used for generic NED devices. The example $NCS_DIR/

examples.ncs/generic-ned/xmlrpc-device has a package called xml-rpc which defines a NED component of type *generic*

**Note**: A CLI NED and a generic NED component must also come with additional user written Java code, whereas a NETCONF NED and an SNMP NED have no Java code.

###### Callback Component

The *callback* type of component is used for a wide range of callback type Java applications, where one of the most important are the Service Callbacks. 

A package that has a *callback* component usually has some YANG code and then also some Java code that relates to that YANG code. By convention the YANG and the Java code resides in a src directory in the component. When the source of the package is built, any resulting fxs files (compiled YANG files) must reside in the *load-dir* of the package and any resulting Java compilation results must reside in the *shared-jar* and *private-jar* directories.

###### Application Component

Used to cover Java applications that do not fit into the *callback* type. Typically this is functionality that should be running in separate threads and work autonomously.

The example $NCS_DIR/examples.ncs/getting-started/ developing-with-ncs/1-cdb contains three components that are of type *application*. These components must also contain a *java-class-name* element. For application components, that Java class must implement the *ApplicationComponent* Java interface.

###### Upgrade Component

Used to migrate data for packages where the yang model has changed and the automatic cdb upgrade is not sufficient. The upgrade component consists of a java class with a main method that is expected to run one time only.

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

## Python examples of executing common tasks using the NSO Maagic API

### Example of how to create a session into NSO. 

A sessions allows for reading data from NSO and executing Actions. It does not create a transaction into NSO.

```python
def create_session():
   with ncs.maapi.Maapi() as m:
      with ncs.maapi.Session(m, 'admin', 'python', groups=['ncsadmin']):
          root = ncs.maagic.get_root(m)
```

### Example of how to create a transaction into NSO.

It create the transaction with the ncs.maapi.single_write_trans against the ncs module, and commit the transaction with the apply() method inside the transaction object we created above.

```python
def create_transaction():
   with ncs.maapi.single_write_trans('admin', 'python', groups=['ncsadmin']) as t:
       root = ncs.maagic.get_root(t)
       t.apply()
```

### Example of how to understand and navigate a devices config in the python API. 
This example will show by printing the directory of differnet levels of the config.

```python
def navigate_config(device_name):
    with ncs.maapi.Maapi() as m:
       with ncs.maapi.Session(m, 'admin', 'python', groups=['ncsadmin']):
           root = ncs.maagic.get_root(m)
           device_config = root.devices.device[device_name].config
           print(dir(device_config))
           print(dir(device_config.ip))
           print(dir(device_config.ip.dhcp))
           print(dir(device_config.ip.dhcp.snooping))
```

### Function to change the hostname of a provided device. 

This is to give an example of making config changes in NSO
It can be made doing this by:

1. create a transaction
2. create a device pointer by passing the device name into the NSO list of devices. The list (root.devices.device) acts much like a Python L ist, it has key value pairs with key beign the device name and value being the object for that device.
3. Set the value of the device's config hostname by assigning the device objects config.hostname atrribute to the new value.
4. Finish by applying the transaction created.


```python
def change_config_hostname(device_name):
    with ncs.maapi.single_write_trans('admin', 'python', groups=['ncsadmin']) as t:
        root = ncs.maagic.get_root(t)
        device = root.devices.device[device_name]
        device.config.hostname = "new_host_name"
        t.apply()
```

### Example of how to delete data (config or NSO) via python.

uses python **del** operator
**Note**: If you **del** a pointer to a NCS object this will only delete the pointer!

```python
def delete_data(device_name):
    with ncs.maapi.single_write_trans('admin', 'python', groups=['ncsadmin']) as t:
        root = ncs.maagic.get_root(t)
        del root.devices.device[device_name].config.hostname
        t.apply()
```

### Example of how to add a new item into a list resource.

In the IOS YANG model there are many instances of Lists.
For example, adding a new VLAN would be adding a new item to a list.
This can be made invoking the .create() method of the ncs list objects

```python
def create_list_item():
    with ncs.maapi.single_write_trans('admin', 'python', groups=['ncsadmin']) as t:
        root = ncs.maagic.get_root(t)
        root.devices.device.config.interface.vlan.create("200")
        t.apply()
```

### This function takes a device hostname as an input and adds that device into NSO.

Then does an nslookup on the hostname
This function uses 3 separate transactions do to sequencing and default admin-state in NSO of locked.
First Transaction: Adds the device and IP to add the device into the cDB
Second Transaction: adds the port and creates the device-type/ NED info and unlocks the device.
Third Transaction: Gets ssh keys, syncs-from and southbound-locks the device.

```python
def add_device(device_name):
    ip_addr = socket.getaddrinfo(device_name,0,0,0,0)
    with ncs.maapi.single_write_trans('admin', 'python', groups=['ncsadmin']) as t:
        root = ncs.maagic.get_root(t)
        root.devices.device.create(device_name)
        root.devices.device[device_name].address = ip_addr[0][4][0]
        t.apply()
    with ncs.maapi.single_write_trans('admin', 'python', groups=['ncsadmin']) as t2:
        root = ncs.maagic.get_root(t2)
        root.devices.device[device_name].port = 22
        root.devices.device[device_name].device_type.cli.create()
        root.devices.device[device_name].device_type.cli.ned_id = "ios-id:cisco-ios"
        root.devices.device[device_name].device_type.cli.protocol = "ssh"
        root.devices.device[device_name].authgroup = "branblac"
        root.devices.device[device_name].state.admin_state = "unlocked"
        t2.apply()
    with ncs.maapi.single_write_trans('admin', 'python', groups=['ncsadmin']) as t3:
        root = ncs.maagic.get_root(t3)
        root.devices.device[device_name].ssh.fetch_host_keys()
        root.devices.device[device_name].sync_from()
        root.devices.device[device_name].state.admin_state = "southbound-locked"
        t3.apply()
```

### Example of how to loop  over devices in NSO and execute actions or changes per each device.

Within this example we will iterate over devices and print the device name and the HW platform.
Then per device print what extended ACL are present on the device.
    Notice how the configuration for the device is navigated via a python object
    In this case config -> ip -> access-list -> extended -> ext_named_acl
    If you think about it, this object structure is very similiar to the IOS syntax and navigation
It can be made doing this by:

1. Creating a transaction
2. Using a for loop over the the root.devices.device list
3. Printing the info, print info per box

In this example, we should have used a session! but if we desire changes we per box we would want a transaction.
In this case, even if we changed config info, nothing would be done! Since we never apply/commit the transaction changes.

```python
def iterate_devices():
    with ncs.maapi.single_write_trans('admin', 'python', groups=['ncsadmin']) as t:
        root = ncs.maagic.get_root(t)
        for box in root.devices.device:
            print(box.name,": ", box.platform.model)
            for acl in root.devices.device[box.name].config.ip.access_list.extended.ext_named_acl:
                print(acl.name)
```

### Use a MAAPI session via maagic api to get the results of a passed show command.

Uses the devices name in NSO as an input parameter and the commnd ie: CDP Neighbors, ip int br.
prints the raw text results of the command.
It can be made doing this by:

1. Creating a NSO session
2. Create a pointer to our device
3. Create an input object but calling the device.live_status.ios_stats__exec.show.get_input() emthod
4. Pass the command function input into the input objects args variable
5. Invoke the command by passign the input object into the device.live_status.ios_stats__exec.show() method
6. set the output variable to the result attributw of our invoked command object above
7. Print the output.

```python
def show_commands(command, device_name):
    with ncs.maapi.Maapi() as m:
       with ncs.maapi.Session(m, 'admin', 'python'):
           root = ncs.maagic.get_root(m)
           device = root.devices.device[device_name]
           input1 = device.live_status.ios_stats__exec.show.get_input()
           input1.args = [command]
           output = device.live_status.ios_stats__exec.show(input1).result
           print(output)
```

Same as above but for clearing

```python
def clear_commands(command, device_name):
    with ncs.maapi.Maapi() as m:
       with ncs.maapi.Session(m, 'admin', 'python'):
           root = ncs.maagic.get_root(m)
           device = root.devices.device[device_name]
           input1 = device.live_status.ios_stats__exec.clear.get_input()
           input1.args = [command]
           output = device.live_status.ios_stats__exec.clear(input1).result
           print(output)
```

### Example that shows one scenario where you will use a leaflist YANG type.
This example iterates over the devices in a provided group the passes
the string value from the list into root.devices.device[] to get the ip address of the device.

```python
def using_leaflists_data(device_group):
    with ncs.maapi.single_write_trans('ncsadmin', 'python', groups=['ncsadmin'], db=ncs.RUNNING, ip='127.0.0.1', port=ncs.NCS_PORT, proto=ncs.PROTO_TCP) as trans:
        root = ncs.maagic.get_root(trans)
        group = root.devices.device_group[device_group].device_name
        for box in group:
            print type(box)
            print(root.devices.device[box].address)
```

### Single search to see if a provided IP address is present inside any of a devices extended ACLs.
```python
def check_in_string(ip):
    with ncs.maapi.single_write_trans('admin', 'python', groups=['ncsadmin']) as t:
        root = ncs.maagic.get_root(t)
        for box in root.devices.device:
            for acl in root.devices.device[box.name].config.ip.access_list.extended.ext_named_acl:
                for rule in root.devices.device[box.name].config.ip.access_list.extended.ext_named_acl[acl.name].ext_access_list_rule:
                    if ip in rule.rule:
                        print(ip + "Is in acl " + str(acl))
```

### Function example that shows values that are of data type boolean.
These can be set to be True or False.
Also showing object assignment for fun.

```python
def work_with_boolean(device_name):
    with ncs.maapi.single_write_trans('admin', 'python', groups=['ncsadmin']) as t:
        root = ncs.maagic.get_root(t)
        dot_one_q_config = root.devices.device[device_name].config.interface.GigabitEthernet["0/1"].dot1Q
        dot_one_q_config.vlan_id = 10
        dot_one_q_config.native = True
```

### Example function to show how to check if a certain interface is on a device.
We do this by using by if in operators and the maagic API dictionary methods.

```python
def check_if_interface_exists(device_name, interface_type, interface_number):
    with ncs.maapi.single_write_trans('admin', 'python', groups=['ncsadmin']) as t:
        root = ncs.maagic.get_root(t)
        device = root.devices.device[device_name]
        print type(device.interface[interface_type])
        if interface_number in device.interface[interface_type]:
            print("Interface is on the device!")
        else:
            print("Interface is not on the device!")
```

### Prints each interface number on the device of the given type

```python
def print_interfaces(device_name, interface_type):
    with ncs.maapi.single_write_trans('admin', 'python', groups=['ncsadmin']) as t:
        root = ncs.maagic.get_root(t)
        device = root.devices.device[device_name]
        for interface in device.interface[interface_type]:
            print interface.name
```

## Writing a Python background worker for Cisco NSO

In the YANG model servicepoints are used to attach a create callback to a particular subtree in the YANG model. In addition to create servicepoint it also have actionpoints which allows attach python code to YANG actions. Both servicepoint and actionpoint attach to the YANG model and lets code be executed upon external stimuli, either the request to run an action or the change of configuration.

The purpose of the background worker, as an example, will be to increment a counter at a periodic interval. It's simple and not useful on its own but around setting up a worker and so, this will serve as a simple example.

1. Start making a new package of python service skeleton.

`````python 
ncs-make-package --service-skeleton python
`````

2. Edit or replace the YANG model to the following. A simple leaf called counter, that is config false (i.e. operational state data).

`````xml
module bgworker {

  namespace "http://example.com/bgworker";
  prefix bgworker;

  container bgworker {
    leaf counter {
      config false;
      type uint32;
      default 0;
    }
  }
}
`````

**Note**: Set the default value to 0 which means the counter will be 0 each time NCS starts up. Unlike configuration data, state data in NCS is not persisted per default which is why our leaf will go back to a value of 0 each time NCS starts. We could add `tailf:persistent "true"` to the leaf to make it persisted in CDB.

And move the YANG source file that should be stored in:

````less 
PACKAGE-NAME/src/yang
````

3. Make package, the normal example skeleton code produced by `ncs-make-package` shows the use of the `setup()`and `teardown()` methods to hook into the start and stop of the Application.

The comment indicates that this is a component thread and runs as a thread in the Python VM.

```python
# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    def setup(self):
        ...
```

The modified Python code, to deploy a background worker MUST start another thread from `setup()` method:

```python
import threading
import time
import ncs
from ncs.application import Service

class BgWorker(threading.Thread):
    def run(self):
        while True:
            print("Hello from background worker")
            time.sleep(1)

class Main(ncs.application.Application):
    def setup(self):
        self.log.info('Main RUNNING')
        self.bgw = BgWorker()
        self.bgw.start()

    def teardown(self):
        self.log.info('Main FINISHED')
        self.bgw.stop()
```

**Note**: `ServiceCallbacks` class with its `cb_create()` was deleted since it doesn't need anymore and instead a new thread definition called `BgWorker` was created which is instantiated and started from the `setup()` method of the Application.

4. loading the package by running `request packages reload`

```
admin@ncs> request packages reload force

>>> System upgrade is starting.
>>> Sessions in configure mode must exit to operational mode.
>>> No configuration changes can be performed until upgrade has completed.
>>> System upgrade has completed successfully.
reload-result {
    package bgworker
    result true
}
[ok][2019-07-01 13:43:04]
admin@ncs>
```

Running `tail -f ncs-python-vm.log ` will show the printed messages made by the **background worker**

```
<INFO> 1-Jul-2019::13:43:04.534 nuc ncs[11832]: Started PyVM: <<"bgworker">> , Port=#Port<0.26560> , OSpid="26111"
<INFO> 1-Jul-2019::13:43:04.535 nuc ncs[11832]: bgworker :: Starting /home/kll/ncs-4.7.4.2/src/ncs/pyapi/ncs_pyvm/startup.py -l info -f ./logs/ncs-python-vm -i bgworker
<INFO> 1-Jul-2019::13:43:04.595 nuc ncs[11832]: bgworker :: Hello from background worker
<INFO> 1-Jul-2019::13:43:05.597 nuc ncs[11832]: bgworker :: Hello from background worker
<INFO> 1-Jul-2019::13:43:06.598 nuc ncs[11832]: bgworker :: Hello from background worker
<INFO> 1-Jul-2019::13:43:07.599 nuc ncs[11832]: bgworker :: Hello from background worker
<INFO> 1-Jul-2019::13:43:08.599 nuc ncs[11832]: bgworker :: Hello from background worker
```

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
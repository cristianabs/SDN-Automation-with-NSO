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
# NSO Users

## NSO CLI

The NSO CLI (command line interface) provides a unified CLI towards the complete network. The NSO CLI is a northbound interface to the NSO representation of the network devices and network services. Do not confuse this with a cut-through CLI that reaches the devices directly. Although the network might be a mix of vendors and device interfaces with different CLI flavors, NSO provides *one* northbound CLI.

NSO provides a network CLI in two different style (selectable by the user): J-style and C-style. The CLI is automatically rendered using the data models described by the YANG files. There are three distinctly different types of YANG files, the built-in NSO models describing the device manager and the service manager, models imported from the managed devices and finally service models. Regardless of model type, the NSO CLI seamlessly handles all models as a whole.

This creates a auto-generated CLI, without any extra effort, except the design of our YANG files. The auto-generated CLI supports the following features:

- Unified CLI across complete network, devices and network services.
- Command line history and command line editor.
- Tab completion for content of the configuration database.
- Monitoring and inspecting log files.
- Inspecting the system configuration and system state.
- Copying and comparing different configurations, for example, between two interfaces or two devices.
- Configuring common setting across a range of devices.

The CLI contains commands for manipulating the network configuration.

A alias provides a shortcut for a complex command.

Alias expansion is performed when a command line is entered. Aliases are part of the configuration and are manipulated accordingly. This is done by manipulating the nodes in the alias configuration tree.

Actions in the YANG files are mapped into actual commands. In J-style CLI actions are mapped to the **request** commands.

Even though the auto-generated CLI is fully functional it can be customized and extended in numerous ways:

- Built-in commands can be moved, hidden, deleted, reordered and extended.
- Confirmation prompts can be added to built-in commands.
- New commands can be implemented using the Java API, ordinary executables and shell scripts.
- New commands can be mounted freely in the existing command hierarchy.
- The built-in tab completion mechanism can be overridden using user defined callbacks.
- New command hierarchies can be created.
- A command timeout can be added, both a global timeout for all commands, and command specific timeouts.
- Actions and parts of the configuration tree can be hidden and can later be made visible when the user enters a password.

The NSO CLI provides various commands for configuring and monitoring software, hardware, and network connectivity of managed devices. The CLI supports two modes: *operational mode*, for monitoring the state of the NSO node; and *configure mode*, for changing the state of the network.

### Operational mode

Operational mode is the initial mode after successful login to the CLI. It is primarily used for viewing the system status, controlling the CLI environment, monitoring and troubleshooting network connectivity, and initiating the configure mode.

The list of base commands available in operational mode is listed below in the "Operational mode commands" section. Additional commands are rendered from the loaded YANG files.

### Configure mode

Configure mode can be initiated by entering the **configure** command in operational mode. All changes to the network configuration are done to a copy of the active configuration. These changes do not take effect until a successful **commit** or **commit confirm** command is entered.

The list of base commands available in configure mode is listed below in the "Configure mode commands" section. Additional commands are rendered from the loaded YANG files.

**Note:** Please reach **`Chapter 2 in NSO User Guide document `**to learn about Basics as: Starting the CLI, Modifying the configuration, Command output processing, Displaying the configuration, etc..

## Device Manager

The NSO device manager is the centre of NSO. The device manager maintains a flat list of all managed devices. NSO keeps the master copy of the configuration for each managed device in CDB. Whenever a configuration change is done to the list of device configuration master copies, the device manager will partition this "network configuration change" into the corresponding changes for the actual managed devices. The device manager passes on the required changes to the NEDs, Network Element Drivers. A NED needs to be installed for every type of device OS, like Cisco IOS NED, Cisco XR NED, Juniper JUNOS NED etc. The NEDs communicate through the native device protocol southbound. The NEDs falls into the following categories:

- **NETCONF capable device:** The Device Manager will produce NETCONF `edit-config` RPC operations for each participating device.
- **SNMP device:** The Device Manager translates the changes made to the configuration into the corresponding SNMP SET PDUs
- **Device with Cisco CLI:** The device has a CLI with the same structure as Cisco IOS or XR routers. The Device Manager and a CLI NED is used to produce the correct sequence of CLI commands which reflects the changes made to the configuration.
- *Other devices* Devices which do not fit into any of the above mentioned categories a corresponding Generic NED is invoked. Generic NEDs are used for proprietary protocols like REST and for CLI flavours that are not resembling IOS or XR. The Device Manager will inform the Generic NED about the made changes and the NED will translate these to the appropriate operations toward the device.

NSO orchestrates an atomic transaction that has the very desirable characteristic of either the transaction as a whole ends up on all participating devices *and* in the NSO master copy, or alternatively the whole transaction is aborted and all changes are automatically rolled-back.

The architecture of the NETCONF protocol is the enabling technology making it possible to push out configuration changes to managed devices and then in the case of other errors, roll back changes. Devices that do not support NETCONF, i.e., devices that do not have transactional capabilities can also participate, however depending on the device, error recovery may not be as good as it is for a proper NETCONF enabled device.

In order to understand the main idea behind the NSO device manager it is necessary to understand the NSO data model and how NSO incorporates the YANG data models from the different managed devices.

The NEDs will publish YANG data models even for non-NETCONF devices. In case of SNMP the YANG models are generated from the MIBs. For JunOS devices the JunOS NED generates a YANG from the JunOS XML Schema. For Schema-less devices like CLI devices the NED developer writes YANG models corresponding to the CLI structure. The result of this is the device manager and NSO CDB has YANG data models for all devices independent of underlying protocol.

## SSH Key Management

The SSH protocol uses public key technology for two distinct purposes:

### Server authentication

* This use is a mandatory part of the protocol. It allows an SSH client to authenticate the server, i.e. verify that it is really talking to the intended server and not some man-in-the-middle intruder. This requires that the client has a priori knowledge of the server's public keys, and the server proves its possession of one of the corresponding private keys by using it to sign some data. These keys are normally called "host keys", and the authentication procedure is typically referred to as "host key verification" or "host key checking".

### Client authentication

* This use is one of several possible client authentication methods, i.e. it is an alternative to the commonly used password authentication. The server is configured with one or more public keys which are authorized for authentication of a user. The client proves possession of one of the corresponding private keys by using it to sign some data - i.e. the exact reverse of the server authentication provided by host keys. The method is called "publickey" authentication in SSH terminology.

These two usages are fundamentally independent, i.e. host key verification is done regardless of whether the client authentication is via publickey, password, or some other method. However host key verification is of particular importance when client authentication is done via password, since failure to detect a man-in-the-middle attack in this case will result in the cleartext password being divulged to the attacker.

## Managing Network Services

NSO can also manage the life-cycle for services like VPNs, BGP peers, ACLs. It is important to understand what is meant by service in this context.

1. NSO abstracts the device specific details. The user only needs to enter attributes relevant to the service.
2. The service instance has configuration data itself that can be represented and manipulated.
3. A service instance configuration change is applied to all affected devices.

These are the features NSO uses to support service configuration.

1. *Service Modeling*: network engineers can model the service attributes and the mapping to device configurations. For example, this means that a network engineer can specify at data-model for VPNs with router interfaces, VLAN id, VRF and route distinguisher.
2. *Service life-cycle*: while less sophisticated configuration management systems can only create an initial service instance in the network they do not support changing or deleting a service instance. With NSO you can at any point in time modify service elements like the VLAN id of a VPN and NSO can generate the corresponding changes to the network devices.
3. The NSO *service instance* has configuration data that can be represented and manipulated. The service model run-time updates all NSO northbound interfaces so a network engineer can view and manipulate the service instance over CLI, WebUI, REST etc.
4. NSO maintains *references between service instances and device configuration*. This means that a VPN instance knows exactly which device configurations it created/modified. Every configuration stored in the CDB is mapped to the service instance that created it.

## Alarm Manager

NSO embeds a generic alarm manager. It is used for managing NSO native alarms and can easily be extended with application specific alarms. Alarm sources can be notifications from devices, undesired states on services detected or anything provided via the Java API.

The Alarm Manager has three main components:

- **Alarm List:** a list of alarms in NSO. Each list entry represents an alarm state for a specific device, object within the device and an alarm type
- **Alarm Model:** for each alarm type, you can configure the mapping to for example X.733 alarm standard parameters that are sent as notifications northbound
- **Operator Actions:** actions to set operator states on alarms such as acknowledgement, and also actions to administratively manage the alarm list such as deleting alarms

The alarm manager is accessible over all northbound interfaces. A read-only view including an SNMP alarm table and alarm notifications is available in an SNMP Alarm MIB. This MIB is suitable for integration to SNMP based alarm systems.

![NSO-DEV-Architecture](images/alarm_manager.png){ width=100% }

In order to populate the alarm list there is a dedicated Java API. This API lets a developer add alarms, change states on alarms etc. A common usage pattern is to use the SNMP notification receiver to map a subset of the device traps into alarms.

## Web User Interface

The NSO Web UI consists of a suit of web based applications. Each application has it's own distinct concern, for instance handle configuration, transaction handling, manage devices, manage services or monitor the system. The different applications can be accessed from the application hub, which is shown directly after authentication.

The Web UI is a mix of custom built applications and auto-rendering from the underlying device and service models. The latter gives the benefit that a Web UI is immediately updated when new devices or services are added to the system. So, say you add support for a new device vendor. Without any programming is the NCS Web UI capable of configuring those devices.

All modern web browsers are supported and no plug-ins are required. The interface is a pure JavaScript Client.

The Web UI is available on port 8080 on the NSO server. The port can be changed in the `ncs.conf` file. A NSO user must exist.

More help how to use the Web UI is present in the Web UI applications. The help is located in the user menu, which can be found to the right in the application header.

Take special notice to the Commit Manager application, whenever a transaction has started, the active changes can be inspected and evaluated before they are commited and pushed to the network. The data is saved to NSO datastore and pushed to the network when a user presses "Commit".

Any network-wide change can be picked up as a rollback-file. That rollback can then be applied to undo whatever happened to the network.


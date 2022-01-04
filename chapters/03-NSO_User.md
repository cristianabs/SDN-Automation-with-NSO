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

## SSH Key Management

## Network Services

## Alarm Manager

## Web User Interface

## Network Simulator
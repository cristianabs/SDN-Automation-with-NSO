# NSO Overview

Creating and configuring network services is a complex task that often requires multiple configuration changes to all devices participating in the service. Additionally changes generally need to be made concurrently across all devices with the changes being either completely successful or rolled back to the starting configuration. And configuration need to be kept in sync across the system and the network devices. NSO approaches these challenges by acting as interface between people or software that want to configure the network, and the devices in the network.

The key features of NSO that comes into play includes:

1. Multi-vendor device configuration management using the native protocols of the network devices.
2. A Configuration Database (CDB) managing synchronized configurations for all devices and services in the network domain.
3. A set of northbound interfaces including human interfaces like web UI and a CLI; programmable interfaces including RESTCONF, NETCONF, JSON-RPC; and language bindings including Java, Python and Erlang.

# NSO System Admin

## NSO Architecture

<p align="center"><img src="images/Cisco-NSO-Logical-Architecture.jpg" alt="NSO Architecture" width="600"/></p>

**NSO** has two main layers that serve different purposes but are tightly integrated with a transactional engine and database.

**Device Manager** manage device configurations in a transactional manner. It supports features like fine-grained configuration commands, bidirectional device configuration synchronization, device groups and templates, and compliance reporting. Following Device Manager overall features are described:

- Deploy configuration changes to multiple devices in a fail-safe way using distributed transactions.
- Validate the integrity of configurations before deploying to the network.
- Apply configuration changes to named device groups.
- Apply templates (with variables) to named device groups.
- Easily roll back changes, if needed.
- Configuration audits: Check if device configurations are in synch with the NSO database. If they are not, what is the diff?
- Synchronize the NSO database and the configurations on devices, in case they are not in synch. This can be done in either direction (import the diff to the NSO database or deploy the diff on devices).

**Service Manager** makes it possible for an operator to manage high-level aspects of the network that are not supported by the devices directly, or is supported in a cumbersome way. Following Service Manager challenges are described:

- Transaction-safe activation of services across different multi-vendor devices.
- What-if scenarios, (dry-run), showing the effects on the network for a service creation/change.
- Maintaining relationships between services and corresponding device configurations and vice versa. • Modeling of services
- Short development and turn-around time for new services.
- Mapping the service model to device models.

**Network Element Drivers (NEDs)** are used to communicate with devices and are modeled in a data-model using the YANG data modelling language.

NSO uses a dedicated built-in storage Configuration Database (CDB) for all configuration data keeping the CDB in sync with the real network device configurations.

## NSO System Operations

#### 1. How Start (Installation)

To start with, it is necessary to note that NSO requires the following for proper installation and operation:

1. Ensure that root permissions are enabled.
2. Choose the correct operating system (Linux). Currently only the Linux operating system is supported.
3. Make sure Java JDK-7.0 or higher is installed.

The installation process consists of 6 steps, which were summarised in this document. For more information please see Chapter 3, NSO System Install in NSO Installation Guide.

1. Use --system-install option to perform system installation. This option creates a system install of NSO, suitable for deployment.
2. Change to Super User priviliges.
3.  The installation program creates a shell script file in each NSO installation which sets environment variables needed to run NSO. 
4. Start NSO.
5. NSO uses Cisco Smart Licensing, as described in Chapter 3, *Cisco Smart Licensing* in *NSO 5.2 Administration Guide* , to make it easy to deploy and manage NSO license entitlements. 

#### 2. How Monitor

This section describes how to monitor NSO via Shell and CLI.

Checking the overall status of NSO can be done using the shell:

$ **ncs --status

** or in the CLI
 ncs# **show ncs-state**

For details on the output see $NCS_DIR/src/yang/tailf-common-monitoring.yang and Below follows an overview of the output:

• **daemon-status** Shows NSO daemon mode, starting, phase0, phase1, started, stopping. 

**NOTE**: The phase0 and phase1 modes are schema upgrade modes and will appear if you have upgraded any data- models.

- **version**: The NSO version.

- **smp**: Number of threads used by the daemon.

- **ha**: The High-Availability mode of the ncs daemon will show up here: slave, master, relay-slave.

- **internal/callpoints**: All your deployed service models should have a corresponding service-point.

  (The ncs-rfs-service-hook is an obsolete call-point, ignore this one).
   • *UNKNOWN* code tries to register a call-point that does not exist in a data-model.
   • *NOT-REGISTERED* a loaded data-model has a call-point but no code has registered.

  For example:

  servicepoints:
   id=l3vpn-servicepoint daemonId=10 daemonName=ncs-dp-6-l3vpn:L3VPN

- **internal/cdb**: Look for any locks. This might be a sign that a developer has taken a CDB lock without releasing it.

- **loaded-data-models**: Shows all namespaces and YANG modules that are loaded.

- **cli, netconf, rest, snmp, webui**: All northbound agents like CLI, REST, NETCONF, SNMP etc are listed with their IP and port.

- **patches**: Lists any installed patches.

- **upgrade-mode**: If the node is in upgrade mode, it is not possible to get any information from the

  system over NETCONF.

It is also important to look at the packages that are loaded. This can be done in the CLI with "**show packages**" command.

#### 3. How Config

NSO can be configured in two ways:

1. Configuration file "ncs.conf".
2. Configuration data at run-time over northbound.

There is a large number of configuration items in ncs.conf, most of them have sane default values. The ncs.conf file is an XML file that must adhere to the **tailf-ncs- config.yang** model. 

The **tailf-ncs- config.yang** is the most important YANG module that is used to control and configure NSO. Everything in that module is available through the northbound APIs. The YANG module has descriptions for everything that can be configured.

**Note**: The **ncs.conf** file is described by the the section called **“CONFIGURATION PARAMETERS”** in ***NSO 5.2 Manual Pages***.

It is possible to edit the ncs.conf file, and then tell NSO to reload the edited file without restarting the daemon and also close and reopen all log files with: **ncs --reload**

Dynamic config can be made through the NSO northbound interfaces manipulating YANG modules its structure is stored in CDB, any change under, /devices/device will change the CDB. Most relevant settings that can be manipulated are:

| Setting name               | Description                                                  |
| :------------------------- | :----------------------------------------------------------- |
| aaa                        | AAA management, users and groups                             |
| cluster                    | Cluster configuration                                        |
| devices                    | Device communication settings                                |
| java-vm                    | Control of the NCS Java VM                                   |
| nacm                       | Access control                                               |
| packages                   | Installed packages                                           |
| python-vm                  | Control of the NCS Python VM                                 |
| services                   | Global settings for services, (the services themselves might be augmented) |
| session                    | Global default CLI session parameters                        |
| snmp                       | Top-level container for SNMP related configuration and status objects |
| snmp-notification-receiver | Configure reception of SNMP notifications                    |
| software                   | Software management                                          |
| ssh                        | Global SSH connection configuration                          |

#### 4. How Backup and Restore (File system)

All elements of the NSO, can be **Backed Up** and **Restored** with standard file system backup procedures.

In a "system install" of NSO, the most convenient way to do backup and restore is to use the **ncs-backup** command. This backs up the database (CDB) files, state files, config files and rollback files from the installation directory. 

To switch back to a previous good state or restore a backup, it's necessary to perform the next three steps:

1. Stop NSO: \# **/etc/init.d/ncs stop**
2. Restore the backup: \# **ncs-backup --restore** --> Select the backup to be restored from the available list of backups; **The configuration and database with run-time statefiles are restored in /etc/ncs and /var/opt/ncs.**
3. Start NSO: \# **/etc/init.d/ncs start**

## NSO Package Overview

A package is basically a directory of files with a fixed file structure, or a tar archive with the same directory layout. A package consists of code, YANG modules, etc., that are needed in order to add an application or function to NSO. 

**Note**: All user code must be part of a package to run in NSO.

At start NSO searches and copies the packages to a private directory tree in the directory defined by the **/ncs-config/state-dir** parameter in **ncs.conf**, and loads and starts all the packages found.

#### Loading Packages

To add or update (If the package changes include modified, added, or deleted) **Packages**,  can be made via the reload action - from the NSO CLI: **packages reload**

This action makes that NSO copy all packages found in the load path to a temporary version of its private directory, and load the packages from this directory. 

- When loading is successful, this temporary directory will be made permanent, otherwise the temporary directory is removed and NSO continues to use the previous version of the packages. 

**Note**: Always update the version in the load path, and request that NSO does the reload via **packages reload** command.

Its recommended to run the command adding the **max-wait-time** and **timeout-action** parameters, to prevent fail reload operation or upgrade canceling action. 

Example: **packages reload max-wait-time 30 timeout-action kill** --> to wait for up tp 30 seconds, by default these parameters are 10 and fail.

Some warnings will be triggered when reload NSO Packages, if a warning has been triggered it is a strong recommendation to fix the root cause. If all of the warnings are intended, it is possible to proceed with "packages reload force" command.

For more information about warnings triggered please read Chapter 5, *L*oading Packages in *NSO 5.2 Administration Guide*.

#### Managing Packages

NSO has the possibility to configure remote software repositories from which packages can be retrieved. 

The **/software/repository** list allows for configuration of one or more remote repositories.

**Example 3** shows how to configure the Tail-f delivery server:

```

admin@ncs(config)# software repository tail-f
Value for 'url' (<string>): https://support.tail-f.com/delivery 
admin@ncs(config-repository-tail-f)# user name 
admin@ncs(config-repository-tail-f)# password
(<AES encrypted string>): ******* 
admin@ncs(config-repository-tail-f)# commit
Commit complete.

```

The following are the **Actions** provided to list, fetch, install or deinstall packages:

• **software packages list [...]**: List local packages, categorized into *loaded*, *installed*, and *installable*.

• **software packages fetch package-from-file** **file**: Fetch a package by copying it from the file system, making it *installable*.

• **software packages install package** **package-name** **[...]**: Install a package, making it available for loading via the **packages reload** action, or via a system restart with package reload.

• **software packages deinstall package** **package-name**: Deinstall a package, i.e. remove it from the set of packages available for loading.

• **software repository** **name** **packages list [...]**: List packages available in the repository identified by name. The list can be filtered via the name-pattern option.

• **software repository** **name** **packages fetch package** **package-name**: Fetch a package from the repository identified by name, making it *installable*.

There is also an **upload** action that can be used via NETCONF or REST to upload a package from the local host to the NSO host, making it *installable* there.

**Important Note**: It is not feasible to use in the CLI or Web UI, since the actual package file contents is a parameter for the action. It is also not suitable for very large (more than a few megabytes) packages, since the processing of action parameters is not designed to deal with very large values, and there is a significant memory overhead in the processing of such values.

## Troubleshooting

##### Installation Problems

During installation the program gives error messages as:

```
tar: Skipping to next header
gzip: stdin: invalid compressed data--format violated
```

This happens if the installation program has been damaged, most likely because it has been downloaded in **'ascii'** mode.

To resolve this problem, remove the installation directory. Download a new copy of NSO from servers. And make sure use binary transfer mode every step of the way.

##### Running Problems 

Sending NETCONF commands and queries with 'netconf-console' fails. The error message is below:

**You must install the python ssh implementation paramiko in order to use ssh.**

This occours because Netconf-console command is implemented using the Python and depends on the python SSH implementation Paramiko.

To resolve this Install Paramiko (and pycrypto, if necessary) using the standard installation of the OS used.

**Note**: A workaround is to use 'netconf-console-tcp'. It uses TCP instead of SSH and doesn't require Paramiko or Pycrypto. Consider that TCP traffic is not encrypted.

##### General Troubleshooting Strategies

In case of problems during starting or running, take note these troubleshooting tips:

1. Transcript all commands, responses and shell scripts used.
2. Save log files: 'devel.log', 'ncs.log', 'audit.log' and 'ncserr.log'. If you are working with your own system, make sure the log files are enabled in ncs.conf.
3. Run **ncs --status**, to save status information available.
4. Run **ncs --check-callbacks**, to verify if **"Data Provider"** works for all possible data items.
5. Run **ncs --debug-dump mydump1**, to create a **"debug dump"**. It contains a lot of status information (including a full ncs --status report) and some internal state information.
6. To catch certain types of problems, especially relating to system start and configuration, the operating system's **"system call trace"** can be invaluable. This tool is called strace/ktrace/truss depending of the OS.
   - linux: **strace -f -o mylog1.strace -s 1024 ncs ...**
   - BSD: **ktrace -ad -f mylog1.ktrace ncs** and **kdump -f mylog1.ktrace > mylog1.kdump**
   - Solaris: **truss -f -o mylog1.truss ncs ...**

## Disaster Management

There are different disaster scenarios described below:

1. **NSO fails to start**

   When NSO starts and fails to initialize, the following exit codes can occur:

   - Exit codes *1* and *19* mean that an internal error has occurred. A text message should be in the logs, or if the error occurred at startup before logging had been activated, on standard error (standard output if NSO was started with --foreground --verbose). 

   - Exit codes *2* and *3* are only used for the ncs "control commands", and mean that the command failed due to timeout. Code *2* is used when the initial connect to NSO didn't succeed within 5 seconds (or the TryTime if given), while code *3* means that the NSO daemon did not complete the command within the time given by the --timeout option.

   - Exit code *10* means that one of the init files in the CDB directory was faulty in some way. Further information in the log.

   - Exit code *11* means that the CDB configuration was changed in an unsupported way. This will only happen when an existing database is detected, which was created with another configuration than the current in ncs.conf.

   - Exit code *13* means that the schema change caused an upgrade, but for some reason the upgrade failed. Details are in the log. The way to recover from this situation is either to correct the problem or to re-install the old schema (fxs) files.

   - Exit code *14* means that the schema change caused an upgrade, but for some reason the upgrade failed, corrupting the database in the process. This is rare and usually caused by a bug. To recover, either start from an empty database with the new schema, or re-install the old schema files and apply a backup.

   - Exit code *15* means that A.cdb or C.cdb is corrupt in a non-recoverable way. Remove the files and re-start using a backup or init files.

   - Exit code *20* means that NSO failed to bind a socket.

   - Exit code *21* means that some NSO configuration file is faulty. More information in the logs.

   - Exit code *22* indicates a NSO installation related problem, e.g. that the user does not have read access

     to some library files, or that some file is missing.

   If NSO is stopped, files A.cdb, C.cdb, O.cdb and S can simply be copied, and the copy is then a full backup of CDB.

2. **NSO failure after startup**
   - Out of memory: If NSO is unable to allocate memory, it will exit by calling *abort(3)*. This will generate an exit code as for reception of the SIGABRT signal - e.g. if NSO is started from a shell script, it will see 134 as exit code (128 + the signal number).
   - Out of file descriptors for *accept(2)*: If NSO fails to accept a TCP connection due to lack of file descriptors, it will log this and then exit with code 25. To avoid this problem, make sure that the process and system-wide file descriptor limits are set high enough, and if needed configure session limits in ncs.conf.

3. **Transaction commit failure**

   When NSO considers the configuration to be in a inconsistent state, operations will continue. It is still possible to use NETCONF, the CLI and all other northbound management agents.

   The MAAPI API has two interface functions which can be used to set and retrieve the consistency status. This API can thus be used to manually reset the consistency state. Apart from this, the only way to reset the state to a consistent state is by reloading the entire configuration.
# Introduction
Mesa script is a script designed to update the switchport configuration on a Juniper EX switch when a Mist Access Point is connected to it.

It is composed of lightweight python web server ([Flask](https://github.com/pallets/flask)) and python code to process the webhook information and change the switchport configuration.

The switchport configuration can be done through
* Juniper CSO
* directly on the switch by using PyEZ.

This script is available as is and can be run on any server with Python3. 
The script is also available as a Docker image. It is designed to simplify the deployment, and a script is available to automate the required images deployment.

## How it works
<img src="__readme_img/cso_process.png" width="40%">

The following steps are explaining the communication when using CSO integration.
1. When an admin connects an AP on any switchport (1) , the switch is using MAC authentication, and the RADIUS server is returning a VLAN id allowing the AP to contact the Mist Cloud (1’)
2. Once the AP connects the Mist Cloud, it will report the switch LLDP information (hostname, switchport desc, …) (2)
3. At the same time, Mist Cloud is sending a webhook message to the MESA server indicating this AP just connects (3)
4. MESA server will use Mist APIs to get more information, especially the switch hostname and the switchport (4)
5. MESA server will contact CSO to get the information required to generate the “AP_mode” configuration. (5)
6. Once the new configuration is generated, MESA will use CSO APIs to apply it to the switchport and ask CSO to deploy the changes to the switch (6)
7. CSO will deploy the new configuration, which will change the switchport from access mode to trunk mode and configure the required VLANs (7)
8. When an admin disconnects an AP from any switchport, the process will be the same, except that the configuration will be generated to revert the switchport back to the “secured_mode”

### Docker Image
You can easily deploy this application with [Docker](https://www.docker.com/). The image is publicly available on Docker Hub at https://hub.docker.com/r/tmunzer/get-a-key/.
In this case, you can choose to manually deploy the image and create the container, or you can use the automation script (for Linux).

#### Automation Script
The Automation script will allow you to easily 
* Configure your application (ACS parameters)
* Manage HTTPS certificates with self-signed certificates 
* Download, Deploy, Update the application container
To use this script, just download it [here](mesa.sh), and run it in a terminal.

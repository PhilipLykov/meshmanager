This repo houses "MeshManager".  This is a management and oversight application that works with MeshMonitor
for deeper inspection and analysis of data collected from multiple MeshMonitor nodes and Meshtastic MQTT servers.

Tech Stack:
* Web interactive frontend with responsible realtime behaviors
* Python backend for data collection and analysis
* PostGres server for data storage
* MQTT server (mosquitto?) for receiving MQTT messages

Features:
* Supports a read-only viewing mode without authentication.
* Supports a basic "admin" login that allows for saving.
* Interactive UI for adding MeshMonitor instances: Provide a name, URL, API Token, and set various parameters (TBD)
* Interactive UI for adding MQTT servers for collecting (not sending) data
* Catppuchin interface design

Once MeshMonitor and MQTT instances are configured, begin a regular data collection.
* MQTT we should simply subscribe to a configured topic for collection.
* MeshMonitor instances we should poll every 5 minutes and collect all data.  API endpoints are available in the documentation at https://meshmonitor.yeraze.com/api/v1/docs/
* Make sure we save everything (messages, nodes, traceroutes, telemetry, etc) in tables in our postgres instance, along with data of which system originated the data. Refer to the source code of the MeshMonitor project if you need help.

Front page shows a list of configured nodes on the left.  On the right show an interactive LEaflet map with pins for each node we know of across all meshmonitor and mqtt instances very similar to what we did in MeshMonitor.

Deployment:
Provide a docker-compose.yml as an example, and build a docker-compose.dev.yml that we use here for testing.  The compose file should launch all the services and configure exposed network ports for the http interface.



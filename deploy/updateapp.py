#################################################
#
# Written by:  Destre Adair
# Modified by: Rishi Jaiswal
# Modified by: Anjani Dubey
# Installation script 
#
# NOTE: This is for a cluster installation
#       Only.
#
#################################################

import sys
import time
from ConfigParser import ConfigParser

#################################################
#
#  Make sure there are enough ARGS send into 
#  the script
#
#  lob - Line of Business
#  env - Environment being released to
#  earName - Name of the EAR File
#
#################################################

if (len(sys.argv) != 4):
   print "\nFormat: updateapp.py BUSINESSNAME ENVIRONMENT EARFILELOCATION PATH-TO-INI_FILE"
   print "\nExample: updateapp.py cdmesb Dev-F CDMESB_EAR.ear cdm.ini\n"
   sys.exit(1)

lob     = sys.argv[0]
env     = sys.argv[1]
earName = sys.argv[2]
proj    = sys.argv[3]

lobenv = lob + "_" + env
project = proj + "/ear_configs.ini"


#################################################
#
# Open the config file and make sure
# the section exists
#
#################################################

config = ConfigParser()

config.readfp(open(project))

if (config.has_section(lobenv)):
   nodeName       = config.get(lobenv, "nodeName")
   cellName       = config.get(lobenv, "cellName")
   clusterName    = config.get(lobenv, "clusterName")
   servers        = config.get(lobenv, "servers")
   appName        = config.get(lobenv, "appName")
   contextrt      = config.get(lobenv, "contextrt")
   mapMod2Servers = config.get(lobenv, "mapMod2Servers")
   timeOut        = config.get(lobenv, "timeOut")

else:
   print "** ERROR - Section " + lobenv + " could not be located\n\n."
   sys.exit(1)

#################################################
#
# Setup up the Ear File Directory Location
#
#################################################

#earFile="/u01/deployments/" + lob + "/uploads/" + earName
earFile=earName
#earFile="D:/Rishi/app_0904_build_0129/vobs/sgapp/app/chordiant/projects/implementation/_Citi_BD_EarBuilder/" + earName
#earFile="D:/data/views/app_build_0409/vobs/sgapp/app/chordiant/projects/implementation/_Citi_BD_EarBuilder/chordiant.ear"
#################################################
#
# Check to see if the server is running, if it 
# is, then stop it for the duration of the 
# installation.
#
#  If the Cluster Name is blank or not defined
#  then assume that only individual servers
#  on nodes will be stopped.
#
#################################################
# 
# Not stopping the CDM Appserver since Rules deployment may be going on in Parallel
#
#################################################
if (clusterName.isspace() or len(clusterName) == 0 ):

   individualNodes=servers.split(",")
   for nodes in individualNodes:
       server=nodes.split(":")
       runningServer = AdminControl.completeObjectName("type=Server,node=" + server[0] + ",process=" + server[1] + ",*")

       if len(runningServer) > 0:
          print "Step 1. Server " + server[1] + " on " + server[0] + " is running. Preparing to shutdown..."
          AdminControl.stopServer(server[1], server[0])
       else:
          print "Step 1. Server " + server[1] + " on " + server[0] + " is not running. Proceeding with App Install"

else:

    cluster=AdminControl.completeObjectName("cell=" + cellName + ",type=Cluster,name=" + clusterName + ",*")

    stateOfCluster=AdminControl.getAttribute(cluster, 'state')

    print "State of Cluster is " + stateOfCluster

    if stateOfCluster != "websphere.cluster.stopped":
        print "Step 1. Cluster is running. Preparing to shutdown..."
        AdminControl.invoke(cluster, 'stopImmediate') 
    else:
        print "Step 1. Cluster is not running. Proceeding with App Install"


#################################################
#
# Update the EAR file
#
#################################################

print "Step 2. Starting the Installation of EAR File.\n"


AdminApp.update(appName, 'app', '[  -operation update -contents ' + earFile + ' -nopreCompileJSPs -installed.ear.destination $(APP_INSTALL_ROOT)/' + cellName+ ' -distributeApp -nouseMetaDataFromBinary -nodeployejb -createMBeansForResources -noreloadEnabled -nodeployws -validateinstall warn -noprocessEmbeddedConfig -filepermission .*\.dll=755#.*\.so=755#.*\.a=755#.*\.sl=755 -noallowDispatchRemoteInclude -noallowServiceRemoteInclude -contextroot [ ' + contextrt + ' ] -MapModulesToServers [ ' + mapMod2Servers + ' ]]]' )

#################################################
#
# Save the updated app
#
#################################################

print "\nStep 3. Save the Configuration."

AdminConfig.save()

print "\nStep 4. Installation of " + earFile + " EAR File is completed for " + lob + " for " + env + " environment.\n"

#################################################
#
# Sync up the Nodes in the cluster 
#
#################################################

print "\nStep 5. Synchronizing all the Nodes. "

if (clusterName.isspace() or len(clusterName) == 0 ):

   individualNodes=servers.split(",")
   for nodes in individualNodes:
       server=nodes.split(":")
       SyncTheNode=AdminControl.completeObjectName('type=NodeSync,node=' + server[0] + ',*')
       AdminControl.invoke(SyncTheNode, 'sync')
       time.sleep(30)

else:

   updateApp="[-ApplicationNames %s -timeout %s]" % (appName,timeOut)
   AdminTask.updateAppOnCluster(updateApp)
   time.sleep(30)

#################################################
#
# Startup the Nodes in the cluster or
# individual servers.
#
# The logic is if the clustername and server
# list is specified, then the individual
# servers on the nodes will be started. 
#
# Otherwise, if the clustername is specified
# but not the servers, then the entire
# cluster is started.
#
# The reason for this is that you might
# have servers in a cluster that you may
# not want started. If you just did a cluster
# start, then all of the nodes in the cluster
# would be started and this might not be 
# what you want.
#
#################################################


####Commenting it out as per Tim's request #####

print "\nStep 6. Starting up of cluster or individual appservers"

if (servers.isspace() or len(servers) == 0 ):

   AdminControl.invoke(cluster, 'start')

else:

   individualNodes=servers.split(",")
   for nodes in individualNodes:
       server=nodes.split(":")
       AdminControl.startServer(server[1], server[0])

print "\nStep 7. The process is completed. Please wait several minutes as it takes awhile to restart all the clusters or servers"
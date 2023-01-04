#!/bin/zsh
#
# Start rM whiteboard application 'pipes-and-paper-enhanced'
# 
# Will look for rM device on two different hostnames
# (e.g. Wifi and USB)
# 

## (assignments must not have spaces around = sign...)
#TODO change the SSH hostnames if need be
# The script will try the rMhostname first, then rMhostname2
rMhostname="rm2"
rMhostname2="rm2usb"

## Do not enclose a path with ~ in "", otherwise the ~ is not expanded 
#TODO put the path on the machine to the repository here
runCommandPath=~/Develop/pipes-and-paper-enhanced

# is the rM online?
# (will timeout with exit code 2 if not)
echo "** searching for reMarkable..."
# e.g. wifi
ping -c 1 -t 5 $rMhostname
# not found
if (( ? != 0 )) then
  # try e.g. usb
  rMhostname=$rMhostname2
  echo "trying $rMhostname..."
  ping -c 1 -t 5 $rMhostname
fi

# evaluate exit code
if [ $? -eq 0 ]
then
  echo "** reMarkable was found"
  echo "** connecting whiteboard to $rMhostname"

  # open browser window after server had time to start up
  (sleep 2 && open http://localhost:8001) &

  # start server
  cd $runCommandPath
  #TODO customize the CLI parameters here
  $runCommandPath/run.sh --ssh-hostname $rMhostname

  exit $?
else
  echo "** reMarkable NOT FOUND in the local network" >&2
  exit 1
fi

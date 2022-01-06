#!/bin/sh
# installer.sh will install the necessary packages to get the Brown Capability up and running
UID=$(id -u)
if [ $UID -ne 0 ]
  then echo "Please execute as root"
  exit
fi

# Install packages
PACKAGES="python3 libavahi-compat-libdnssd-dev"
apt-get update
apt-get install $PACKAGES -y
pip install picamera gpiozero HAP-python[QRCode]

## Enable Camera Interface
CONFIG="/boot/config.txt"

# If a line containing "start_x" exists
if grep -Fq "start_x" $CONFIG
then
	# Replace the line
	echo "Modifying start_x"
	sed -i "s/start_x=0/start_x=1/g" $CONFIG
else
	# Create the definition
	echo "start_x not defined. Creating definition"
	echo "start_x=1" >> $CONFIG
fi

# If a line containing "gpu_mem" exists
if grep -Fq "gpu_mem" $CONFIG
then
	# Replace the line
	echo "Modifying gpu_mem"
	sed -i "/gpu_mem/c\gpu_mem=128" $CONFIG
else
	# Create the definition
	echo "gpu_mem not defined. Creating definition"
	echo "gpu_mem=128" >> $CONFIG
fi

# Install brown
mkdir /usr/local/bin/brown
cp ./capability.py /usr/local/bin/brown/capability.py

# Install brown service
cp ./unit/brown.service /lib/systemd/system/brown.service

chmod 644 /lib/systemd/sytem/brown.service
systemctl enable brown.service
systemctl start brown.service

echo "Install complete, rebooting."
#reboot
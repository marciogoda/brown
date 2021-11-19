# Brow Capability


## Automated plant watering based on Raspbery Pi Zero W

This project born from a necessity of watering my wifes plants during long trips and be able to monitor their development.
To correct follow my wife's watering routine for the existing plants, the script will water only in a specifc day of the week, but the schedulle can be configured as you need.

This project is composed of 2 parts:
- Deamon to monitor soil moisture and visual of the plants and water on a specific schedule.
- Web app capable of live feed and water the plants on demmand.

### Daemon
It will check every 10 min the soil moisture and take a pricture of the plant

### Web app
This is a web page hosted on the Rapbery Pi Zero ex. http://[host_name]/
- Allows you to stream a live video from the Pi Camera 
- Allow you to trigger the GPIO to start/stop watering


## Components
- Raspbery Pi Zero W
- RPi Relay Board [https://www.waveshare.com/wiki/RPi_Relay_Board](https://www.waveshare.com/wiki/RPi_Relay_Board)
- Raspbery Pi Camera V2
- Peristaltic Liquid Pump - 5V DC Power
- Soil Moisture Sensor
- Flexible silicone tubbing 2.5mm internal diameter

## Instalation

```
   curl -L https://github.com/marciogoda/brown/latest/install.sh | bash
```

## Security information
As the web app contains live feed from the camera it is advised to deploy in a secure network environment or without internet access.
If you prefer during the instalation dont install the web app.
We don't take any responsability for your the use any part of this project.

#!/bin/sh

cd /home/pi/sentakuki/

#python3 6_sentakuki_beep_detect.py
#python3 7_sentakuki_beep_detect.py
nohup python3 sentakuki_beep_detect.py
#sudo nice -n -20 python3 7_sentakuki_beep_detect.py
#python3 old_sentakuki_beep_detect.py

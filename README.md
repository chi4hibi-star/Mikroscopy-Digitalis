## Fair Use
This Software is for LAB3.org and Voxelcast ExplorAM as well as the 
creator Andreas Anastassiadis. For usage outside these Organisations
and people please ask any of them for a copy and not any other person.

## Setup Raspberry Pi for the first time
'''bash
sudo apt update
sudo apt install python3-pip python3-venv -y
git clone https://github.com/chi4hibi-star/Mikroscopy-Digitalis
cd project_root
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
python src/main.py

## Useage
The Software is for Raspberry Pi that controlls a Mikroskope.
The Controll is via a Raspberry Pi Camera and 3 Stepper Motors controlled
by the GPIO's. Here is the GPIO connection to the Driver:
PINS = {
        'EN': {'X': 15, 'Y': 31, 'Z': 37},
        'STEP': {'X': 11, 'Y': 22, 'Z': 35},
        'DIR': {'X': 13, 'Y': 29, 'Z': 36},
        'ENDSTOP_NEG': {'X': 16, 'Y': 32, 'Z': 38},
        'ENDSTOP_POS': {'X': 18, 'Y': 33, 'Z': 40}
    }
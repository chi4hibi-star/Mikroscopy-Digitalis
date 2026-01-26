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
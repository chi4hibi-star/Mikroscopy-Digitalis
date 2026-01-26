## Setup Raspberry Pi for the first time

sudo apt update
sudo apt install python3-pip python3-venv -y
git clone 
cd project_root
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/main.py
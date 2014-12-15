set -e

sudo apt-get install -y python-pip python-dev
sudo pip install --upgrade pip

(
    cd /vagrant
    sudo pip install -r dev-requirements.txt
)

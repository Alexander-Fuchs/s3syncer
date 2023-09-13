#!/bin/bash

# define colors
BOLD=$(tput bold)
NORMAL=$(tput sgr0)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)

echo "${BOLD}${YELLOW}Checking if Python 3 is installed...${NORMAL}"
# check if python is installed
if command -v python3 &>/dev/null
then
    echo "${BOLD}${GREEN}Python 3 is installed${NORMAL}"
else
    echo "${BOLD}${YELLOW}Python 3 is not installed. Please install Python 3.${NORMAL}"
    exit 1
fi

echo "${BOLD}${YELLOW}Creating virtual environment...${NORMAL}"
# create virtual environment
python3 -m venv $(pwd)/venv

echo "${BOLD}${YELLOW}Activating virtual environment...${NORMAL}"
# activate virtual environment
source $(pwd)/venv/bin/activate

echo "${BOLD}${YELLOW}Installing required packages...${NORMAL}"
# install required packages
pip install -r $(pwd)/requirements.txt

echo "${BOLD}${YELLOW}Copying s3_syncer.conf to the supervisor config directory...${NORMAL}"
# copy s3_syncer.conf to the supervisor config directory
cp $(pwd)/s3_syncer.conf /etc/supervisor/conf.d/

echo "${BOLD}${YELLOW}Updating supervisor...${NORMAL}"
# update supervisor
sudo supervisorctl reread
sudo supervisorctl update

echo "${BOLD}${GREEN}Setup completed.${NORMAL}"

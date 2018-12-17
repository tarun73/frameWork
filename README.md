# frameWork

HOW TO RUN ON LOCAL

install mongodb - 
https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/

install rabbitmq server - 
https://www.vultr.com/docs/how-to-install-rabbitmq-on-ubuntu-16-04-47

create virtual python environment -
install dependecies using the requirements.txt file
pip install -i requirements.txt

make changes in the config.json file according to the credentials.
change the default training images, testing images, datasets directories to your needs.
change mongo database names accordingly


activate the virtual environment and run
python app.py 
python worker.py


For api details check the API Description.txt file

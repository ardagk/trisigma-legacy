## Required
* python 3.10
* memcached >1.6.21
* rabbitmq >3.12.2
* mongod >6.0.6

## Build
1. Clone the project, cd into it
2. `pip install -r requirements.txt`
3. `pip install .`
4. `touch /var/log/trisigma.log`
5. `sudo chmod 666 /var/log/trisigma.log`

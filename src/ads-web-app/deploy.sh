yum update -y
yum install epel-release
yum install "mod_wsgi" -y
yum install python-pip
python setup.py install
rsync -avz --progress /root/ovpl/src/ads-web-app /var/www/html/
service httpd restart



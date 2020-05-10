# big_basket_automation
Automating grocery shopping from https://www.bigbasket.com/

installation : 

- Create and activate virtual env
~~~
$ virtualenv bb
$ source bb/bin/activate 
~~~

- Clone repo :
~~~
$ git clone https://github.com/shatadru/big_basket_automation.git
$ cd big_basket_automation
~~~

- Install requirements 
~~~
$ pip install -r requirements.txt
~~~

- Copy sample file in /etc/
~~~
$ sudo mkdir /etc/bb
$ sudo cp bb.conf.sample /etc/bb.conf
$ sudo cp contacts.sample /etc/bb/contacts
~~~

- Edit config file /etc/bb.conf and /etc/bb/contacts

- Get curl command after logging in to www.bigbasket.com and save it in a file.
~~~
$ vi raw_curl_command
~~~

Convert the file :
~~~
$ sudo bash convert_curl_to_header raw_curl_command > /etc/bb/header
~~~

After this you can run the script in background or as systemd service.
~~~
$ python3 big_basket.py
~~~

big_basket.py : Provides slot email/whatsapp/sms notification when a slot is available in your area 

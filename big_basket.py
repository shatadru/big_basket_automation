import configparser
import datetime
import json
import logging
import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from twilio.rest import Client

# default config file location
ConfigFilePath='/etc/bb.conf'


# Parser for config file
def parse_config(ConfigFilePath):
    ConfigParser = configparser.RawConfigParser()
    FilePath = ConfigFilePath
    # Check if file exists
    check_file(FilePath)
    ConfigParser.read(FilePath)
    config_dict_default = dict(ConfigParser.items('default'))
    config_dict_twilio = dict(ConfigParser.items('twilio'))
    config_dict_email = dict(ConfigParser.items('email'))
    global sleep, header, account_sid, auth_token, smtp_server, smtp_port, email, password, admin_email, contacts
    # default config
    sleep = int(config_dict_default['interval'])
    log_file = config_dict_default['log_file']
    admin_email = config_dict_default['admin_email']

    # Forward log to log file
    logging.basicConfig(filename=log_file, filemode='w',
                        format='%(asctime)s : %(process)s - %(levelname)s - %(message)s')
    logging.root.setLevel(logging.NOTSET)
    logging.info('----------------------------------------')
    logging.info('Big basket slot notifier starting.......')
    logging.info('----------------------------------------')
    print("Logs are printed on " + log_file)
    notification_repeat_delay = int(config_dict_default['notification_repeat_delay'])
    contact_file = config_dict_default['contact_file']
    check_file(contact_file)
    header_file = config_dict_default['header_file']
    check_file(header_file)
    contacts = {}
    with open(contact_file, 'r') as con:
        for lines in con.readlines():
            columns = lines.split()
            id = int(columns.pop(0))
            contacts[id] = columns
    header = {}
    with open(header_file, 'r') as head:
        for lines in head.readlines():
            columns = lines.split(": ")
            header[columns[0]] = columns[1].split("\n")[0].strip()
    # Parse Email config
    smtp_server = config_dict_email['smtp_server']
    smtp_port = config_dict_email['smtp_port']
    email = config_dict_email['email']
    password = config_dict_email['password']

    # Parse Twilio config
    account_sid = config_dict_twilio['account_sid']
    auth_token = config_dict_twilio['auth_token']
    logging.info('Config file parsed successfully....')


def send_email(receiver_emails, sub, body):
    global smtp_server, smtp_port, sender_email, password
    smtp_server = smtp_server
    smtp_port = smtp_port  # For starttls
    sender_email = email
    receiver_emails = receiver_emails
    login = sender_email
    password = password
    subject = sub
    email_body = body
    context = ssl.create_default_context()
    # send your email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.ehlo()
        server.starttls(context=context)  # Secure the connection
        server.ehlo()
        server.login(login, password)
        for receiver_email in receiver_emails:
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = receiver_email
            message["Subject"] = subject
            # Add body to email
            body = email_body
            message.attach(MIMEText(body, "plain"))
            text = message.as_string()
            try:
                server.sendmail(sender_email, receiver_email, text)
            except Exception as err:
                logging.error("Email send failure : " + str(err))


def check_file(filepath):
    try:
        f = open(filepath)
        f.close()
    except FileNotFoundError:
        handle_error('File' + filepath + ' does not exist, ensure Config file is in place')
    except IOError as err:
        handle_error('File' + filepath + ' is not a accessible, ensure user has read access to the file : ' + str(err))


def handle_error(error, email='shatadru01@gmail.com'):
    # This function is for generic error handling
    # This will send crash report to developer/admin
    subject = "Big Basket Slot Notifier crash report"
    body = "\nEmail generated at :   " + datetime.datetime.now().strftime("%a %d-%h-%Y    %I:%M %p") + "\n"
    body += "\nError is : " + str(error)
    print(error)
    logging.error(error)
    # send_email(email, subject, body)
    exit(255)


def slot_email(available, email, admin_email, fullname, slot_type, status):
    if available == 1:
        subject = 'Big basket Slot Available'
    else:
        subject = 'This is a test email from Big Basket slot notifier\n'

    email_body = 'This email is generated automatically, please report error/issue at ' + admin_email + '\n'
    email_body += 'Email generated at : ' + datetime.datetime.now().strftime("%a %d-%h-%Y    %I:%M %p") + '\n'
    if available == 1:
        email_body += 'Slot is available for ' + fullname + '\n'
        email_body += 'Slot type = ' + slot_type +'\n'
        email_body += "Status = " + status + '\n'
        logging.info('Sending email...')
        send_email(email, subject, email_body)
    else:
        email_body += 'Slot is not currently available for ' + fullname + '\n'
        logging.info('Not sending email...')
    logging.info(email)
    logging.info(email_body)

    # sub = 'Big basket Slot Available'
    # text2='\nThis email is generated automatically, please report error/issue at shatadru01@gmail.com'
    # text2+="\n email generated at :   "+datetime.datetime.now().strftime("%a %d-%h-%Y    %I:%M %p")+"\n"
    # text2+= '\n\nSlot is available for ' + str(address['first_name'])+" "+str(address['last_name']) + "\n Slot type = " +slot_type +"\n Status = " + item['darkstore_next_slot']
    # text2+='\n\n Your Address details in BB database: '
    # text2+='\n Please verify if location is nearby : https://latlong.net/c/?lat='+str(address['address_lat'])+'&long='+str(address['address_lng'])+"\n"
    # text2+=json.dumps(address,indent=2)
    # text2+="\n Please contact script owner for any correction in address, note address does not need to be exact for checking slots"
    # text2+="\n However verify area, location url, pin"
    # text2+="\n\n Also this will spam you for now when slot is available, I will change this tomorrow to ensure this sends only 1-2 email once slot is opened rather than every 2 mins"


def send_whatsapp(receiver_number,body):
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        from_='whatsapp:+14155238886',
        body=body,
        to='whatsapp:'+str(receiver_number)
    )
    print(message.sid)

def send_sms(receiver_number,body):
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        from_='+15017122661',
        body=body,
        to=str(receiver_number)
    )
    print(message.sid)


def login_and_fetch_address():
    logging.info('Fetching address list....')
    session = requests.Session()
    # Fetch address details
    try:
        get_all_addrs=session.get('https://www.bigbasket.com/mapi/v3.5.1/address/list/?send_partial=0',headers=header)
    except ConnectionError as conerr:
        handle_error("Connection failed, error is : " + str(conerr))
    except Exception as err:
        handle_error("Unable to reach to bigbasket, error is : " + str(err))

    # Process address
    #print(get_all_addrs.text )
    address_json_string = json.loads(get_all_addrs.text)
    addresses = address_json_string['response']
    return addresses['addresses']

def login_and_fetch_slot_availability():
    logging.info('Fetching slot availability....')
    session = requests.Session()
    # Add all entries in contacts dict to construct the data to send to API
    data=''
    for everyone in contacts:
        data+='address_id[]='+str(everyone)+'&'
    data+='all=true'
    #data='address_id[]=153097968&address_id[]=155452388&address_id[]=155452368&address_id[]=155452356&address_id[]=155452335&address_id[]=155516832&address_id[]=155729665&all=true'
    # Fetch slot details
    try:
        get_slots = session.post('https://www.bigbasket.com/auth/member/get-address-slots/', data=data, headers=header)
    except ConnectionError as conerr:
        handle_error("Connection failed, error is : " + str(conerr))
    except Exception as err:
        handle_error("Unable to reach to bigbasket,, error is : " + str(err))

    # Process Slots
    # Convert slot data from API response to nested list
    slot_json_string = json.loads(get_slots.text)
    #rint(slot_json_string)
    slot_success = slot_json_string['success']
    if slot_success == False:
        handle_error("BB slot availability API returned failure")
    slot_addresses=slot_json_string['adresses']
    return slot_addresses

def check_availabilty_for_address_and_email(slot_details,address_details):
    logging.info('Checking slot availability for each address   ....')
    global  admin_email
    email_sent = []
    global contacts
    for address in address_details:
        if  address['id'] in contacts:
            email=contacts[address['id']]
            for item in slot_details:
                if address['id']  == item['id']:
                    fullname = str(address['first_name']) + " " + str(address['last_name'])
                    if item['show_express'] == False:
                        slot_type = "Standard"
                    else:
                        slot_type = "Express"
                    slot_status = item['darkstore_next_slot']
                    if item ['darkstore_next_slot'] != 'All Slots Full. Please Try Again Later':
                        logging.info('Slot Present')
                        slot_email(1, email,admin_email, fullname, slot_type, slot_status)
                        phone_no='+91'+str(address['contact_no'])
                        #send_whatsapp(phone_no,text2)
                    else:
                        slot_email(0, email, admin_email, fullname, slot_type, slot_status)
                        #send_email(email, sub, text2)
            logging.info ('-----------------------------------------------------------')


parse_config(ConfigFilePath)
while 1:
    # Get all address in the account
    address_details=login_and_fetch_address()

    # Get all slot availability from account
    slot_details=login_and_fetch_slot_availability()

    # Descision making logic, combine both dict, for each contact Check for availability, if available email contact
    check_availabilty_for_address_and_email(slot_details,address_details)

    logging.info("sleeping for "+str(sleep)+" seconds ...")
    time.sleep(sleep)

from os import access
import traceback
import requests
import json
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from mimetypes import guess_type as guess_mime_type
import db


with open ('gmail_creds.json','r') as file :
    data = json.load(file)
client_id=data['web']['client_id']
client_secret=data['web']['client_secret']



# Adds the attachment with the given filename to the given message
def add_attachment(message, attachment):

    content_type, encoding = guess_mime_type(attachment['_filename_'])
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    if main_type == 'text':
        
        msg = MIMEText(urlsafe_b64decode(attachment['data']), _subtype=sub_type)
        
    elif main_type == 'image':
        
        msg = MIMEImage(urlsafe_b64decode(attachment['data']), _subtype=sub_type)
        
    elif main_type == 'audio':
        
        msg = MIMEAudio(urlsafe_b64decode(attachment['data']), _subtype=sub_type)
        
    else:
        
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(urlsafe_b64decode(attachment['data']))
    
    msg.add_header('Content-Disposition', 'attachment', filename=attachment['_filename_'])
    message.attach(msg)


def build_message(sender,destination, subject, body, attachments):
    if not attachments: # no attachments given
        message = MIMEText(body)
        message['to'] = destination
        message['from'] = sender
        message['subject'] = subject
    else:
        message = MIMEMultipart()
        message['to'] = destination
        message['from'] = sender
        message['subject'] = subject
        message.attach(MIMEText(body))
        for attachment in attachments:
            add_attachment(message, attachments[attachment])
    raw_message = urlsafe_b64encode(message.as_string().encode("utf-8"))
    return {'raw': raw_message.decode("utf-8")}


def revoke__user(token):

    revoke_response=requests.post('https://oauth2.googleapis.com/revoke',
    params={'token': token},
    headers = {'content-type': 'application/x-www-form-urlencoded'})
    return {"result":revoke_response.json()}



def save_gmail_user(user_id,access_token,refresh_token,expiry):
    try:
        conn=db.create_db_connection("localhost", "root", "My3QlP@ssword", "Credentials")
        db.execute_query(conn,db.save_creds_query("Gmail",user_id,client_id,client_secret,access_token,refresh_token,expiry))
        return "saved successfuly"
    
    except Exception as e:
        traceback.print_exc(e)






def get_gmail_creds():
    try:
        
        conn=db.create_db_connection("localhost", "root", "My3QlP@ssword", "Credentials")
        db_creds=db.read_query(conn,db.get_creds_query("gmail"))
        return (db.creds_row_mapper(db_creds[0]))
        
    except Exception as e:
        print(e)
        


def delet_gmail_creds():
    try:
        
        conn=db.create_db_connection("localhost", "root", "My3QlP@ssword", "Credentials")
        db.execute_query(conn,db.delete_creds_query("gmail"))

        return ({"results":"your gmail account has been disconnected",
                                "success":True,
                                "status":200}),200
    except Exception as e:
        traceback.print_exc(e)

    return ({"results":"Error deleting credentials",
                                "success":False,
                                "status":500}),500

def update_gmail_creds(cred_type, access_token, refresh_token, expiry):

    try:

        conn=db.create_db_connection("localhost", "root", "My3QlP@ssword", "Credentials")
        db.execute_query(conn,db.update_creds_query(access_token,refresh_token,expiry,cred_type))
        
        return ({"results":"Attributes updated successfuly",
                                "success":True,
                                "status":200}),200
    except Exception as e:
        traceback.print_exc(e)

    return ({"results":"Error updating credentials",
                                "success":False,
                                "status":500}),500
   
import traceback
from flask import Flask, Blueprint, request, redirect 
import json
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from oauth2client.client import flow_from_clientsecrets
#SERVICES
from gmail_service import save_gmail_user , get_gmail_creds , update_gmail_creds , revoke__user , delet_gmail_creds ,build_message
# import gmail_service

with open ('gmail_creds.json','r') as file :
    data = json.load(file)

app = Flask(__name__)
app.debug = True


SCOPES=["https://mail.google.com/", "https://www.googleapis.com/auth/userinfo.email"]
client_id=data['web']['client_id']
client_secret=data['web']['client_secret']
host_url="http://127.0.0.1:5000"
redirect_uri = host_url+"/gmail/permission_granted"






@app.route("/gmail/authorize",methods=["GET","POST"])

def gmail_auth():
    
    url="https://accounts.google.com/o/oauth2/v2/auth?scope=https://mail.google.com/ https://www.googleapis.com/auth/userinfo.email&access_type=offline&include_granted_scopes=true&response_type=code&redirect_uri="+redirect_uri+"&client_id="+client_id
    return redirect(url)
    


@app.route("/gmail/permission_granted",methods = ["GET","POST"])
def exchange_code():
    authorization_code=request.args.get("code")
    flow = flow_from_clientsecrets("gmail_creds.json", ' '.join(SCOPES))
    flow.redirect_uri = redirect_uri
    credentials = flow.step2_exchange(str(authorization_code))
    creds_string='{}'.format(credentials.to_json())
    creds=json.loads(creds_string)
    #print("@@@@@@@@@@@@@@@@@@@@@@@@ GMAIL FIRST TIME CREDS")
    #print(creds)

    #TO SAVE IN THE DATABASE##########################################
    user_id = creds['id_token']['email']
    access_token=creds['access_token']
    refresh_token=creds['refresh_token']
    expiry=creds['token_expiry']
    #we will save our data into DB
    saving_response=save_gmail_user(user_id,access_token,refresh_token,expiry)
    #print("################ gmail saving_response #########",saving_response)
    
    return "user authenticated"


@app.route("/gmail/get_labels",methods=["GET","POST"])
def labels():
    
    Token={"token": "", "refresh_token": "", "token_uri": "https://oauth2.googleapis.com/token", "client_id": "", "client_secret": "", "scopes": ["https://mail.google.com/", "https://www.googleapis.com/auth/userinfo.email"], "expiry": ""}
    ####### in here i must retreive the info from database
   
    db_creds= get_gmail_creds()
    
    Token["token"]=db_creds["access_token"]
    Token["refresh_token"]=db_creds["refresh_token"]
    Token["expiry"] = db_creds["expiry"]
    Token["client_id"] = db_creds["client_id"]
    Token["client_secret"] = db_creds["client_secret"]
    user_id = db_creds["user_id"]

    print("####################### access_token, refresh token, expiry, user_id : ", Token["token"],Token["refresh_token"], Token["expiry"], user_id)

    #this section is only to refresh creds if there isn't already valid creds
    creds = None
    creds = Credentials.from_authorized_user_info(Token, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            #send to the database to update ##################################
            access_token=creds.token
            refresh_token=creds.refresh_token
            expiry=creds.expiry 
            date = str(expiry).split(" ")
            join=date[0]+"T"+date[1]

            account_update_response=update_gmail_creds("gmail", access_token, refresh_token,join)
            
            print("AFTERRRRR UPDATINGGGGGGGG RESPONSEEEEEEEEEEEEEEE: ", account_update_response)
    ######################################## END OF REFRESHING SECTION
    service = build('gmail', 'v1',cache_discovery=False, credentials=creds)
    
    # Call the Gmail API
    results = service.users().labels().list(userId=user_id).execute()
    labels = results.get('labels', [])
    labelslist=list()
    if not labels:
        return'No labels found.'
    else:
        
        for label in labels:
            labelslist.append(label['name'])
    jsonString = json.dumps(labelslist)
    return jsonString
        



@app.route("/gmail/get_threads_list",methods=["GET","POST"])

def get_threads_list():
    #allowed lables : [  "CHAT", "SENT", "INBOX", "IMPORTANT", "TRASH", "DRAFT", "SPAM", "CATEGORY_FORUMS", "CATEGORY_UPDATES", "CATEGORY_PERSONAL", "CATEGORY_PROMOTIONS", "CATEGORY_SOCIAL", "STARRED", "UNREAD" ]
    lable=request.args.get("lable")
    next_page=request.args.get("next_page")
    Token={"token": "", "refresh_token": "", "token_uri": "https://oauth2.googleapis.com/token", "client_id": "", "client_secret": "", "scopes": ["https://mail.google.com/", "https://www.googleapis.com/auth/userinfo.email"], "expiry": ""}
    ####### in here i must retreive the info from database
   
    db_creds= get_gmail_creds()
    
    Token["token"]=db_creds["access_token"]
    Token["refresh_token"]=db_creds["refresh_token"]
    Token["expiry"] = db_creds["expiry"]
    Token["client_id"] = db_creds["client_id"]
    Token["client_secret"] = db_creds["client_secret"]
    user_id = db_creds["user_id"]
    print("####################### access_token, refresh token, expiry, user_id : ", Token["token"],Token["refresh_token"], Token["expiry"], user_id)

    #this section is only to refresh creds if there isn't already valid creds
    creds = None
    creds = Credentials.from_authorized_user_info(Token, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            #send to the database to update ##################################
            access_token=creds.token
            refresh_token=creds.refresh_token
            expiry=creds.expiry 
            date = str(expiry).split(" ")
            join=date[0]+"T"+date[1]

            account_update_response=update_gmail_creds("gmail", access_token, refresh_token,join)
            
            print("AFTERRRRR UPDATINGGGGGGGG RESPONSEEEEEEEEEEEEEEE: ", account_update_response)
    ######################################## END OF REFRESHING SECTION
    
    service = build('gmail', 'v1',cache_discovery=False, credentials=creds,)

    # Call the Gmail API
    if next_page =="":
        threads_list = service.users().threads().list(userId=user_id,maxResults=50,labelIds=lable,includeSpamTrash=False).execute()
    else:
        threads_list = service.users().threads().list(userId=user_id,maxResults=50,pageToken=next_page,labelIds=lable,includeSpamTrash=False).execute()
    return threads_list



@app.route("/gmail/get_thread",methods=["GET","POST"])

def get_thread():
    
    thread_id=request.args.get("thread_id")
    Token={"token": "", "refresh_token": "", "token_uri": "https://oauth2.googleapis.com/token", "client_id": "", "client_secret": "", "scopes": ["https://mail.google.com/", "https://www.googleapis.com/auth/userinfo.email"], "expiry": ""}
    ####### in here i must retreive the info from database
   
    db_creds= get_gmail_creds()

    Token["token"]=db_creds["access_token"]
    Token["refresh_token"]=db_creds["refresh_token"]
    Token["expiry"] = db_creds["expiry"]
    Token["client_id"] = db_creds["client_id"]
    Token["client_secret"] = db_creds["client_secret"]
    user_id = db_creds["user_id"]

    print("####################### access_token, refresh token, expiry, user_id : ", Token["token"],Token["refresh_token"], Token["expiry"], user_id)

    #this section is only to refresh creds if there isn't already valid creds
    creds = None
    creds = Credentials.from_authorized_user_info(Token, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            #send to the database to update ##################################
            access_token=creds.token
            refresh_token=creds.refresh_token
            expiry=creds.expiry 
            date = str(expiry).split(" ")
            join=date[0]+"T"+date[1]
            account_update_response=update_gmail_creds("gmail", access_token, refresh_token,join)
            print("AFTERRRRR UPDATINGGGGGGGG RESPONSEEEEEEEEEEEEEEE: ", account_update_response)
    ######################################## END OF REFRESHING SECTION
    
    service = build('gmail', 'v1',cache_discovery=False, credentials=creds,)

    # Call the Gmail API
    thread = service.users().threads().get(userId=user_id,id=thread_id,format='full').execute()

    return thread

    



@app.route("/gmail/get_message",methods=["GET","POST"])

def get_message():
    #this section is only to refresh creds if there isn't already valid creds
    msg_id=request.args.get("msg_id")
    ##########################################################################
    Token={"token": "", "refresh_token": "", "token_uri": "https://oauth2.googleapis.com/token", "client_id": "", "client_secret": "", "scopes": ["https://mail.google.com/", "https://www.googleapis.com/auth/userinfo.email"], "expiry": ""}
    ####### in here i must retreive the info from database
   
    db_creds= get_gmail_creds()
    
    Token["token"]=db_creds["access_token"]
    Token["refresh_token"]=db_creds["refresh_token"]
    Token["expiry"] = db_creds["expiry"]
    Token["client_id"] = db_creds["client_id"]
    Token["client_secret"] = db_creds["client_secret"]
    user_id = db_creds["user_id"]

    print("####################### access_token, refresh token, expiry, user_id : ", Token["token"],Token["refresh_token"], Token["expiry"], user_id)

    #this section is only to refresh creds if there isn't already valid creds
    creds = None
    creds = Credentials.from_authorized_user_info(Token, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            #send to the database to update ##################################
            access_token=creds.token
            refresh_token=creds.refresh_token
            expiry=creds.expiry 
            date = str(expiry).split(" ")
            join=date[0]+"T"+date[1]

            account_update_response=update_gmail_creds("gmail", access_token, refresh_token,join)

            print("AFTERRRRR UPDATINGGGGGGGG RESPONSEEEEEEEEEEEEEEE: ", account_update_response)

    ######################################## END OF REFRESHING SECTION
    
    service = build('gmail', 'v1',cache_discovery=False, credentials=creds,)

    # Call the Gmail API
    msg = service.users().messages().get(userId=user_id,id=msg_id,format='full').execute()
    # g="SEVMFSVCBJUyBPTE8gQU5JUyAsIFRISVMgUETkxZIFRPIFRFU1QgSUYgVEhFIEVNQUlMIFJFQURJTkcgSVMgV09SS0lORyBXRUxMDQosDQpJIE5FRUQgVE8gV1JJVEUgTE9UUyBPRiBXT1JEUyAsIEkgVEhJTksgSSdMTCBKVVNUIENPUFkgQSAgUEFSQUdSQVBIIEZST00NCkdPT0dMRSAsDQpBIHBhcmFncmFwaCBpcyBhIHNlcmllcyBvZiByZWxhdGVkIHNlbnRlbmNlcyBkZXZlbG9waW5nIGEgY2VudHJhbCBpZGVhLA0KY2FsbGVkIHRoZSB0b3BpYy4gVHJ5IHRvIHRoaW5rIGFib3V0IHBhcmFncmFwaHMgaW4gdGVybXMgb2YgdGhlbWF0aWMgdW5pdHk6DQphIHBhcmFncmFwaCBpcyBhIHNlbnRlbmNlIG9yIGEgZ3JvdXAgb2Ygc2VudGVuY2VzIHRoYXQgc3VwcG9ydHMgb25lDQpjZW50cmFsLCB1bmlmaWVkIGlkZWEuIFBhcmFncmFwaHMgYWRkIG9uZSBpZGVhIGF0IGEgdGltZSB0byB5b3VyIGJyb2FkZXINCmFyZ3VtZW50Lg0K"
    #message = ('Message snippet: %s \n\n' % msg['snippet'])
    #msg_str = base64.urlsafe_b64decode(g.encode("utf-8")).decode("utf-8")
    #mime_msg = E.message_from_string(msg_str)
    ########################################################################################
    # getting attachments
    attachments={}
    attachments_counter=1
    for part in msg['payload']['parts']:
      
      if(part['filename'] and part['body'] and part['body']['attachmentId']):
          attachment = service.users().messages().attachments().get(id=part['body']['attachmentId'], userId=user_id, messageId=msg_id).execute()
          att={
              "_filename_": part['filename'],
              "data":attachment['data']
              }
          attachments['attachment{}'.format(attachments_counter)]=att
          attachments_counter+=1
    msg["attachments"]=attachments
    return msg



@app.route("/gmail/send_email",methods=["GET","POST"])

def send_email():
    #variables to get from the frontend

    json_data = request.json


##THIS HOW DATA SHOULD BE SENT FROM THE FRONTEND
    # json_data = {
    #     "attachments" : {
    #         "attachment1": {
    #             "_filename_": "test1.csv",
    #             "data": "SEVMFSVCBJUyBPTE8gQU5JUyAsIFRISVMgUETkxZIFRPIFRFU1QgSUYgVEhFIEVNQUlMIFJFQURJTkcgSVMgV09SS0lORyBXRUxMDQosDQpJIE5FRUQgVE8gV1JJVEUgTE9UUyBPRiBXT1JEUyAsIEkgVEhJTksgSSdMTCBKVVNUIENPUFkgQSAgUEFSQUdSQVBIIEZST00NCkdPT0dMRSAsDQpBIHBhcmFncmFwaCBpcyBhIHNlcmllcyBvZiByZWxhdGVkIHNlbnRlbmNlcyBkZXZlbG9waW5nIGEgY2VudHJhbCBpZGVhLA0KY2FsbGVkIHRoZSB0b3BpYy4gVHJ5IHRvIHRoaW5rIGFib3V0IHBhcmFncmFwaHMgaW4gdGVybXMgb2YgdGhlbWF0aWMgdW5pdHk6DQphIHBhcmFncmFwaCBpcyBhIHNlbnRlbmNlIG9yIGEgZ3JvdXAgb2Ygc2VudGVuY2VzIHRoYXQgc3VwcG9ydHMgb25lDQpjZW50cmFsLCB1bmlmaWVkIGlkZWEuIFBhcmFncmFwaHMgYWRkIG9uZSBpZGVhIGF0IGEgdGltZSB0byB5b3VyIGJyb2FkZXINCmFyZ3VtZW50Lg0K"
    #         },

    #         "attachment2": {
    #             "_filename_": "test2.pdf",
    #             "data": "SEVMFSVCBJUyBPTE8gQU5JUyAsIFRISVMgUETkxZIFRPIFRFU1QgSUYgVEhFIEVNQUlMIFJFQURJTkcgSVMgV09SS0lORyBXRUxMDQosDQpJIE5FRUQgVE8gV1JJVEUgTE9UUyBPRiBXT1JEUyAsIEkgVEhJTksgSSdMTCBKVVNUIENPUFkgQSAgUEFSQUdSQVBIIEZST00NCkdPT0dMRSAsDQpBIHBhcmFncmFwaCBpcyBhIHNlcmllcyBvZiByZWxhdGVkIHNlbnRlbmNlcyBkZXZlbG9waW5nIGEgY2VudHJhbCBpZGVhLA0KY2FsbGVkIHRoZSB0b3BpYy4gVHJ5IHRvIHRoaW5rIGFib3V0IHBhcmFncmFwaHMgaW4gdGVybXMgb2YgdGhlbWF0aWMgdW5pdHk6DQphIHBhcmFncmFwaCBpcyBhIHNlbnRlbmNlIG9yIGEgZ3JvdXAgb2Ygc2VudGVuY2VzIHRoYXQgc3VwcG9ydHMgb25lDQpjZW50cmFsLCB1bmlmaWVkIGlkZWEuIFBhcmFncmFwaHMgYWRkIG9uZSBpZGVhIGF0IGEgdGltZSB0byB5b3VyIGJyb2FkZXINCmFyZ3VtZW50Lg0K"
    #         }
    #     },

    #     "message_text": "hey im a message",
    #     "subject": "im subject",
    #     "destination": "touatidjamel5@gmail.com"


    # }

    attachments = json_data["attachments"]
    message_text = json_data["message_text"]
    subject = json_data["subject"]
    destination = json_data["destination"]
    
    Token={"token": "", "refresh_token": "", "token_uri": "https://oauth2.googleapis.com/token", "client_id": "", "client_secret": "", "scopes": ["https://mail.google.com/", "https://www.googleapis.com/auth/userinfo.email"], "expiry": ""}
    ####### in here i must retreive the info from database
   
    db_creds= get_gmail_creds()
    


    Token["token"]=db_creds["access_token"]
    Token["refresh_token"]=db_creds["refresh_token"]
    Token["expiry"] = db_creds["expiry"]
    Token["client_id"] = db_creds["client_id"]
    Token["client_secret"] = db_creds["client_secret"]
    user_id = db_creds["user_id"]

    

    print("####################### access_token, refresh token, expiry, user_id : ", Token["token"],Token["refresh_token"], Token["expiry"], user_id)


    #this section is only to refresh creds if there isn't already valid creds
    creds = None
    creds = Credentials.from_authorized_user_info(Token, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            #send to the database to update ##################################
            access_token=creds.token
            refresh_token=creds.refresh_token
            expiry=creds.expiry 
            date = str(expiry).split(" ")
            join=date[0]+"T"+date[1]

            account_update_response=update_gmail_creds("gmail", access_token, refresh_token,join)
            

            print("AFTERRRRR UPDATINGGGGGGGG RESPONSEEEEEEEEEEEEEEE: ", account_update_response)
  

    #CREATING  EMAIL####################################################
    message=build_message(user_id,destination,subject,message_text,attachments)
  
    #create the api service
    service = build('gmail', 'v1', credentials=creds)

    #send the email
    service.users().messages().send(userId=user_id, body=message).execute()

    return {"status":200}





@app.route("/gmail/revoke_user",methods=["GET","POST"])

def revoke_user():
    try:
        ###################################################################
        Token={"token": "", "refresh_token": "", "token_uri": "https://oauth2.googleapis.com/token", "client_id": "", "client_secret": "", "scopes": ["https://mail.google.com/", "https://www.googleapis.com/auth/userinfo.email"], "expiry": ""}
        ####### in here i must retreive the info from database
    
        db_creds= get_gmail_creds()
        


        Token["token"]=db_creds["access_token"]
        Token["refresh_token"]=db_creds["refresh_token"]
        Token["expiry"] = db_creds["expiry"]
        Token["client_id"] = db_creds["client_id"]
        Token["client_secret"] = db_creds["client_secret"]
        user_id = db_creds["user_id"]

        access_token = db_creds["access_token"]

        print("####################### access_token, refresh token, expiry, user_id : ", Token["token"],Token["refresh_token"], Token["expiry"], user_id)


        #this section is only to refresh creds if there isn't already valid creds
        creds = None
        creds = Credentials.from_authorized_user_info(Token, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                access_token=creds.token
                
        try:
                revoke_resp=revoke__user(access_token)
                print("++++++++++ revoke resp ++++",revoke_resp)
        except Exception as e:
            traceback.print_exc()
            
        delet_gmail_creds()
        return{"result":"gmail unlinked with success","status":"200"}
    except Exception as e:
        traceback.print_exc(e)
        return(e.args[0])


if __name__ == "__main__":
    
    app.run(host="127.0.0.1", port=5000)
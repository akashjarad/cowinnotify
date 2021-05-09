import datetime
import json
import os
import smtplib
import ssl
import time

import plivo
import pytz
import requests

tz = pytz.timezone("Asia/Calcutta")

# add the distric you want to monitor
districts = ["363"]
SUBJECT = "COVID VACCINE AVAILABILITY"
context = ssl.create_default_context()

# api-endpoint
URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict"

with open('metadata.json') as f:
    meatdata = json.load(f)


def get_all_slot():
    nearest_slot= False
    week_counter = 1
    currdate = datetime.datetime.now(tz)
    timestamp = datetime.datetime.now(tz).strftime("%Y:%m:%d %H:%M:%S")
    day_date = datetime.datetime.now(tz).strftime("%d-%m-%Y")
    while week_counter < 5:
        available_centers = list()
        other_available_centers =list()
        for d in districts:
            url = URL + "?district_id=" + d + "&date=" + day_date
            r = requests.get(url=url, headers={
                "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36"},)
            # extracting data in json format
            data = r.json()
            for center in data["centers"]:
                if (center['pincode'] in meatdata['pincodes'] and len(center['sessions'])):
                    for session in center['sessions']:
                        if(session['available_capacity'] > 4 and session["vaccine"] in meatdata['vaccine']):
                            available_centers.append({"name": center["name"], "available_capacity": session["available_capacity"],  "date": session["date"],
                                                  "fee_type": center["fee_type"], "address": center["address"], "Age": session["min_age_limit"], "vaccine": session["vaccine"]})
                elif (meatdata['partial_pin_code'] in str(center['pincode']) and len(center['sessions'])):
                    nearest_slot= True
                    for session in center['sessions']:
                        if(session['available_capacity'] > 4 and session["vaccine"] in meatdata['vaccine']):
                            other_avail_centers.append({"name": center["name"], "available_capacity": session["available_capacity"],  "date": session["date"],
                                                  "fee_type": center["fee_type"], "address": center["address"], "Age": session["min_age_limit"], "vaccine": session["vaccine"]})
            
            if len(available_centers):
                print("Sending Mail Notification", timestamp)
                send_mail(available_centers)
                send_sms("Vaccine Avilable.please check mail")
            elif(len(other_avail_centers)):
                print("Sending Mail Notification", timestamp)
                send_mail(available_centers)
            else:
                with open("request_logs.log", "a+") as f:
                    f.write("No slots found for date : "+ day_date +" . Checked at : " + timestamp + "\n")
                print("No slots found : ", timestamp)

        day_date = currdate + datetime.timedelta(days=6*week_counter)
        day_date = day_date.strftime("%d-%m-%Y")
        week_counter = week_counter+1

    return


def send_sms(content):
    client = plivo.RestClient(
        meatdata['sms_account_id'], meatdata['sms_auth_token'])
    response = client.messages.create(
        src='+XXXXXXXXXX',
        dst=meatdata['notify_mobile_no'],
        text=content)
    return Response(response.to_string())


def send_mail(available_centers):
    from_address = "xxxxxx@gmail.com"
    TEXT = "Following centers are available. Check the following dates:\n\n"
    for center in available_centers:
        TEXT = TEXT + json.dumps(center) + "\n"
    message = "To: {}\r\n".format(
        meatdata['emails']) + "Subject: {}\n\n{}".format(SUBJECT, TEXT)
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls(context=context)
        try:
            server.login(from_address, meatdata['gmail_app_password'])
        except smtplib.SMTPAuthenticationError as e:
            error_code = e.smtp_code
            error_message = e.smtp_error
            print("\n" + error_message)
            pass

        try:
            server.sendmail(from_address, meatdata['emails'], message)
            server.quit()
        except smtplib.SMTPResponseException as e:
            error_code = e.smtp_code
            error_message = e.smtp_error
            print("\n" + error_message)
            print("Abort!")
            pass


def main():
    sleep = 20
    while True:
        get_all_slot()
        time.sleep(sleep * 60)


if __name__ == "__main__":
    main()

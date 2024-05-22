from tinydb import TinyDB, Query
import hashlib
from bs4 import BeautifulSoup
import requests
import threading
from flask import Flask, request, render_template
import time
from datetime import datetime
import email
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid

# Configure your Email
email_address = "temptestmail19@gmail.com"
email_password = "nshhmetbstuxqije"
email_smtp_server = "smtp.gmail.com"
email_smtp_port = 587
# Configure End

# log_file = 'price_tracker.log'
#
# logging.basicConfig(
#     filename=log_file,
#     level=logging.INFO,
#     format='%(asctime)s [%(levelname)s] - %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S',
# )


def send_email(address, content):
    sender_email = "temptestmail19@gmail.com"
    sender_password = "nshhmetbstuxqije"
    recipient_email = address
    subject = "price drop alert"
    body = content

    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "html"))

    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())


    data = ""
    for i in content:
        for key in i.keys():
            if key == 'URL':
                data += "<a style='background-color:#29b6f6; color:white; font-size:16px; text-align:center; padding: .375rem .75rem; width:100vw; border-radius:10px; text-decoration:none' href='" + i[key] + "'>Click to view product</a>"
            else:
                data += "<p style='font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; margin-bottom: 5px;'>" + key + "</p>"
                data += "<p style='font-family: sans-serif; font-size: 20px; font-weight: 800; margin: 0; margin-bottom: 15px;'>" + i[key] + "</p> "
    html = f"""<html><head><meta name='viewport' content='width=device-width'>
    <meta http-equiv='Content-Type' content='text/html; charset=UTF-8'><title>Simple Transactional Email</title>
    <style> /* your CSS styles here */ </style></head>
    <body style='background-color: #f6f6f6; font-family: sans-serif; -webkit-font-smoothing: antialiased; font-size: 14px; line-height: 1.4; margin: 0; padding: 0; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;'>
    <table border='0' cellpadding='0' cellspacing='0' class='body' style='border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%; background-color: #f6f6f6;'>
    <tbody> <tr> <td style='font-family: sans-serif; font-size: 14px; vertical-align: top;'>&nbsp;</td>
    <td class='container' style='font-family: sans-serif; font-size: 14px; vertical-align: top; display: block; Margin: 0 auto; max-width: 580px; padding: 10px; width: 580px;'>
    <div class='content' style='box-sizing: border-box; display: block; margin: 2rem; max-width: 580px; padding: 20px; background-color: white;'>
    <!-- START CENTERED WHITE CONTAINER --> {data}
    <div class='footer' style='clear: both; Margin-top: 10px; text-align: center; width: 100%;'> <table border='0' cellpadding='0' cellspacing='0' style='border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%;'> </table> </div>
    <!-- END FOOTER --> <!-- END CENTERED WHITE CONTAINER --> </div> </td> <td style='font-family: sans-serif; font-size: 14px; vertical-align: top;'>&nbsp;</td> </tr> </tbody> </table></body></html>"""
    part2 = MIMEText(html, "html")
    message.attach(part2)
    s = smtplib.SMTP(email_smtp_server, email_smtp_port)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(sender_email, sender_password)
    s.sendmail(sender_email, recipient_email, message.as_string())
    s.quit()
    print('Email Sent to ' + address)


def get_product(url):
    headers = {
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36 OPR/69.0.3686.77",
        'Cookie': '',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    product_title = soup.find(id='productTitle').text.strip()

    # Find the price elements
    price_whole = soup.find("span", class_="a-price-whole")
    price_symbol = soup.find("span", class_="a-price-symbol")

    # Extract price and currency
    price = price_whole.text.strip()
    currency = price_symbol.text.strip()

    currency = currency.replace('\n', '').replace('\u00a0', '').replace(',', '')
    id = hashlib.sha256(product_title.encode("utf-8")).hexdigest()

    return {
        'product_price': price,
        'product_title': product_title,
        'previous_price': price,
        'id': id,
        'currency': currency,
        'url': url
    }


def check_amazon():
    while True:
        set_db = TinyDB("json/setting.json")
        set_search = Query()
        result = set_db.search(set_search.title == "sleep_time")
        sleep_time = int(result[0]['content'])

        user_db = TinyDB('json/product.json')
        user_product = user_db.all()
        search = Query()

        for a in user_product:
            while True:
                status = True
                try:
                    result = get_product(a['url'])
                except Exception:
                    status = False
                    pass
                if status:
                    break

            current_price = float(a['product_price'])
            new_price = float(result['product_price'])

            if current_price - new_price > 0:
                price_drop = current_price - new_price
                user_db.update({'product_price': str(new_price), 'previous_price': str(current_price)},
                               search.id == a['id'])
                send = user_db.search(search.id == a['id'])

                send_data = [{
                    "Product Title": send[0]['product_title'],
                    "Price": send[0]['currency'] + " " + send[0]['product_price'],
                    "Last Price": send[0]['currency'] + " " + send[0]['previous_price'],
                    "URL": send[0]['url'],
                }]

                notification_list = TinyDB("json/notification.json")
                notification_list.insert(send_data[0])

                email_list = TinyDB("json/email.json")
                email_users = email_list.all()

                for user in email_users:
                    send_email(user['email'], send_data)

        now = datetime.now()
        current_time = now.strftime("%Y-%m-d %H:%M:%S")
        set_db = TinyDB("json/setting.json")
        set_search = Query()
        set_db.update({'content': str(current_time)}, set_search.title == "time")
        print("Product Checked on - " + str(current_time))

        result = set_db.search(set_search.title == "sleep_time")
        sleep_time = result[0]['content']
        time.sleep(int(sleep_time))

    # except Exception as e:
    #  Log any exceptions that occur
    # logging.error("An error occurred: %s", str(e))

app = Flask("Python Amazon Price Tracker")


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/email', methods=['GET'])
def email():
    return render_template('email.html')


@app.route('/setting', methods=['GET'])
def setting():
    return render_template('setting.html')


@app.route('/search', methods=['GET'])
def search():
    name = request.args.get('name')
    user_db = TinyDB('json/' + name + '.json')
    products = user_db.all()
    notification = TinyDB('json/notification.json')
    notification_list = notification.all()
    noti_search = Query()
    if name == 'product':
        result = {'products': [], 'notification': []}
        for i in products:
            result['products'].append(i)
        for i in notification_list:
            result['notification'].append(i)
            notification.remove(noti_search.URL == i['URL'])
    else:
        result = {'email': []}
        for i in products:
            result['email'].append(i)
    return result


@app.route('/get_setting', methods=['GET'])
def get_setting():
    set_db = TinyDB("json/setting.json")
    set_search = Query()
    name = request.args.get('setting')

    if name != None:
        result = set_db.search(set_search.title == name)
        update_time = result[0]['content']
        return {'data': update_time}
    else:
        return {"all_setting": set_db.all()}


@app.route('/save_setting', methods=['POST'])
def save_setting():
    set_db = TinyDB("json/setting.json")
    set_search = Query()
    data = request.get_json()
    for i in data.keys():
        set_db.update({'content': data[i]}, set_search.title == i)
    return "Saved"


@app.route('/add', methods=['POST'])
def add():
    data = request.get_json()

    if data['type'] == 'url':
        user_product = TinyDB("json/product.json")
        while True:
            status = True
            try:
                product = get_product(data['data'])
            except Exception:
                status = False
                pass
            if status:
                break
        product_search = Query()
        find_product = user_product.search(product_search.id == product['id'])
        if find_product == []:
            user_product.insert(product)
            return "Tracking " + product['product_title']
        else:
            return product['product_title'] + " is already in your tracking list."
    elif data['type'] == 'email':
        user_email = TinyDB("json/email.json")
        email_search = Query()
        find_email = user_email.search(email_search.email == data['data'])
        if find_email == []:
            user_email.insert({"email": data['data']})
            return "Email Saved."
        else:
            return "Email already exists."


@app.route('/remove', methods=['POST'])
def remove():
    data = request.get_json()
    if data['type'] == 'product':
        user_product = TinyDB("json/product.json")
        product_search = Query()
        user_product.remove(product_search.id == data['data'])
        return "Product Deleted."
    elif data['type'] == 'email':
        user_product = TinyDB("json/email.json")
        product_search = Query()
        user_product.remove(product_search.email == data['data'])
        return "Email Deleted."


threading.Thread(target=check_amazon).start()
app.run(host='0.0.0.0', debug=False, port=10086)

import smtplib, json
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from getopt import getopt
import sys

from constants import DELIMETER, FOUNDMAP_MAIL_HEADER, FOUNDMAP_MAIL_SUBJECT, SECRET_FILE_ADDRESS


def secret_password():
    with open(SECRET_FILE_ADDRESS, 'r') as secret:
        password = json.load(secret)['google_app_password']
    return password


def send_files_mail(texts, attachments):

    gmail_user = 'fantastic.farzin@gmail.com'
    gmail_password = secret_password()

    # Create Email 
    mail_from = gmail_user
    mail_to = ['farzinlize@live.com', 'fmohammadi@ce.sharif.edu']

    message = MIMEMultipart()
    message['Subject'] = FOUNDMAP_MAIL_SUBJECT

    message_body = ''
    for text in texts:
        with open(text, 'r') as content:
            message_body += content.read() + '\n###############################\n'
    message.attach(MIMEText(FOUNDMAP_MAIL_HEADER + '\n' + message_body))

    for filename in attachments:
        with open(filename, 'rb') as attachment:
            message.attach(MIMEImage(attachment.read()))

    # Sent Email
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(gmail_user, gmail_password)
    server.sendmail(mail_from, mail_to, message.as_string())
    server.close()


if __name__ == "__main__":
    shortopt = 'i:a:'
    longopts = ['in-body=', 'attachment=']

    # default values
    args_dict = {}

    opts, args = getopt(sys.argv[1:], shortopt, longopts)
    for o, a in opts:
        if o in ['-i', '--in-body']:
            args_dict.update({'in-body':a.split(DELIMETER)})
        elif o in ['-a', '--attachment']:
            args_dict.update({'attachments':a.split(DELIMETER)})

    send_files_mail(args_dict['in-body'], args_dict['attachments'])
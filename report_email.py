import smtplib, json
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from getopt import getopt
import sys

from constants import DELIMETER, EMAIL_ACCOUNT, MAIL_HEADER, MAIL_SUBJECT, MAIL_TO, SECRET_FILE_ADDRESS

TYPES = {'T':MIMEText, 'I':MIMEImage}
READ_MODE = {'T': 'r', 'I': 'rb'}

def secret_password():
    with open(SECRET_FILE_ADDRESS, 'r') as secret:
        password = json.load(secret)['google_app_password']
    return password


def send_files_mail(texts=[], attachments=[], types=[], strings=[], additional_subject=''):

    assert len(attachments) == len(types)

    gmail_user = EMAIL_ACCOUNT
    gmail_password = secret_password()

    # Create Email 
    mail_from = gmail_user
    mail_to = MAIL_TO

    message = MIMEMultipart()
    message['Subject'] = MAIL_SUBJECT + additional_subject

    message_body = '\n'.join(strings) + '\n'
    for text in texts:
        try:
            with open(text, 'r') as content:
                message_body += content.read() + '\n###############################\n'
        except FileNotFoundError:
            print("[MAIL][ERROR] file doesn't exist (%s)"%text)
            message_body += "[ERROR] file doesn't exist (%s)"%text + '\n###############################\n'

    message.attach(MIMEText(MAIL_HEADER + '\n' + message_body))

    for type_of, filename in zip(types, attachments):
        try:
            with open(filename, READ_MODE[type_of]) as attachment:
                message.attach(TYPES[type_of](attachment.read()))
        except FileNotFoundError:
            print("[MAIL][ERROR] file doesn't exist (%s)"%text)
            message_body += "[ERROR] file doesn't exist (%s)"%text + '\n###############################\n'

    # Sent Email
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(gmail_user, gmail_password)
    server.sendmail(mail_from, mail_to, message.as_string())
    server.close()


if __name__ == "__main__":
    shortopt = 'i:a:t:'
    longopts = ['in-body=', 'attachment=', 'types=']

    # default values
    args_dict = {'attachments':[], 'types':[]}

    opts, args = getopt(sys.argv[1:], shortopt, longopts)
    for o, a in opts:
        if o in ['-i', '--in-body']:
            args_dict.update({'in-body':a.split(DELIMETER)})
        elif o in ['-a', '--attachment']:
            args_dict.update({'attachments':a.split(DELIMETER)})
        elif o in ['-t', '--types']:
            args_dict.update({'types':a.split(DELIMETER)})

    send_files_mail(args_dict['in-body'], args_dict['attachments'], args_dict['types'])
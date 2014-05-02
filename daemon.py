"""
  Mailforwarder v1.2

  Forwards unread mail from an IMAP SSL service to any e-mail account.
  When mail is forwarded successfully, it is also marked read at the IMAP server.

  The daemon outputs 'M' for every forwarded mail
  and 'E' for every mail forward error and 'F' for failed connections.

  Author: Rune Friborg <runef@birc.au.dk>
  This file is copyrighted under the Beerware license. Enjoy.
  https://www.google.com/?q=beerware%20license
"""
import sys
import getpass, imaplib
import email
import subprocess
import time
import socket
import re

# CHANGE!
USER        = 'USERNAME' # IMAP Username
DESTINATION = 'email@email.domain' # Forward destination
IMAP_SERVER = 'imap.server.domain'

# OPTIONAL
RETURNPATH  = "unknown-from@address.nodk"
PASS        = getpass.getpass() # Ask for pass at startup
FREQUENCY   = 20 # seconds
SENDMAIL    = "/usr/sbin/sendmail" # full path!

getmail = re.compile(".*<(.+@.+)>|([^<>]+)")

def forward(email_data):
    # create a Message instance from the email data
    message = email.message_from_string(email_data)
    
    # replace headers (could do other processing here)
    # message.replace_header("To", DESTINATION)

    # extract from header
    m = getmail.match(message.get("From", RETURNPATH))
    m1, m2 = m.groups()
    frommail = m1 or m2
 
    # open SMTP connection and send message with
    # specified envelope from and to addresses    
    p = subprocess.Popen([SENDMAIL, "-f", frommail, DESTINATION], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate(input=message.as_string())
    if stdout or stderr:
        sys.stdout.write("\nFailed forwarding message '%s'\nSendmail stdout:%s\nSendmail stderr:%s\n" % (message.get("Subject", "unknown subject"), stdout, stderr))
        sys.stdout.flush()
        return False
    return True

report_ok = False

while True:
    try:
        M = imaplib.IMAP4_SSL(host=IMAP_SERVER)
        try:
            M.login(USER,PASS)
            try:
                M.select()
                typ, data = M.search(None, 'UNSEEN')
                for num in data[0].split():
                    typ, data = M.fetch(num, '(RFC822)')
                    email_data = data[0][1]

                    try:
                        success = forward(email_data)
                        # Set delete flag 
                        # M.store(num, '+FLAGS', '\\Deleted')
                
                        # Set read flag
                        if success:
                            M.store(num, '+FLAGS', '(\\Seen)')
                            sys.stdout.write('M')
                            sys.stdout.flush()
                        else:
                            M.store(num, '-FLAGS', '(\\Seen)')
                            sys.stdout.write('E')
                            sys.stdout.flush()
                    except:
                        M.store(num, '-FLAGS', '(\\Seen)')
                        sys.stdout.write('E')
                        sys.stdout.flush()
                        raise
            finally:
                M.close()
        finally:
            M.logout()
    except:
        if not report_ok:
            sys.stdout.write('Failed connecting to %s' % IMAP_SERVER)
            sys.stdout.flush()
            raise

        sys.stdout.write('F')
        sys.stdout.flush()
        pass

    if not report_ok:
        sys.stdout.write("Daemon started\n")
        report_ok = True
    # sleeping
    time.sleep(FREQUENCY)

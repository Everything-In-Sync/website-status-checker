import requests
from requests.exceptions import RequestException
from smtplib import SMTP
from email.mime.text import MIMEText
import colorama
from colorama import init
from colorama import Fore, Back, Style
import ssl
import socket
from datetime import datetime

sites_to_test = [
    "google.com",
    "yahoo.com"
]


def format_expiry_date(expiry_str):
    # Parse the date
    expiry_date = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y GMT')
    # Format it to just the date
    return expiry_date.strftime('%Y-%m-%d')

def test_websites(websites, max_response_time=2):
    email_report = ""
    terminal_report = ""
    all_ok = True
    for site in websites:
        try:
            response = requests.get("https://" + site, timeout=5)
            response_time = response.elapsed.total_seconds()
            response_status = response.status_code

            # Check if the response time is within the acceptable limit
            if response_time < max_response_time:
                response_time_status = f"Response time: {response_time} seconds"
            else:
                response_time_status = f"WARNING: Slow response time: {response_time} seconds"
                all_ok = False

            # Check the status code and prepare report content
            if response_status == 200:
                ctx = ssl.create_default_context()
                try:
                    with ctx.wrap_socket(socket.socket(), server_hostname=site) as s:
                        s.connect((site, 443))
                        cert = s.getpeercert()
                        expiry_str = cert['notAfter']
                        expiry_date = format_expiry_date(expiry_str)
                except Exception as e:
                    print(f"Error checking SSL certificate for {site}: {e}")
                email_report += f"OK: {site} is up (Status Code 200). {response_time_status} SSL Expire: {expiry_date}\n"
                terminal_report += Fore.GREEN + f"OK: {site} is up (Status Code 200). {response_time_status} SSL Expire: {expiry_date}\n" + Style.RESET_ALL
            else:
                email_report += f"WARNING: {site} returned a non-OK status code {response_status}. {response_time_status}\n"
                terminal_report += Fore.RED + f"WARNING: {site} returned a non-OK status code {response_status}. {response_time_status}\n" + Style.RESET_ALL
                all_ok = False

        except RequestException as e:
            email_report += f"ERROR: Could not connect to {site} ({str(e)}). Response time check skipped.\n"
            terminal_report += Fore.RED + f"ERROR: Could not connect to {site} ({str(e)}). Response time check skipped.\n" + Style.RESET_ALL
            all_ok = False

    print(terminal_report)  # Print the report with color in the terminal
    return all_ok, email_report  # Send the email without color codes


def send_email(
    subject,
    body,
    sender_email,
    receiver_email,
    smtp_server,
    smtp_port,
    smtp_username,
    smtp_password,
):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    with SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())


all_ok, report = test_websites(sites_to_test)

if all_ok:
    subject = "Websites: All Good"
else:
    subject = "Websites: Issue"
sender_email = "email"
receiver_email = "email"
smtp_server = "server"
smtp_port = 587
smtp_username = "username"
smtp_password = "password"
send_email(
    subject,
    report,
    sender_email,
    receiver_email,
    smtp_server,
    smtp_port,
    smtp_username,
    smtp_password,
)







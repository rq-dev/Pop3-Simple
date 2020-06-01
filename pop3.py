import socket
import ssl
import base64
import re


host = 'pop3.mail.ru'
username = '*****'
password = '*****'


def print_help():
    print('Made by Roman Yaschenko MO-202\n'
          'The programme download letters from pop3 server. Fill in host, username and password')


class MailStruct:
    def __init__(self, mail_to, mail_from, mail_subject,
                 mail_date, mail_size, original_headers):
        self.mail_to = mail_to
        self.mail_from = mail_from
        self.mail_subject = mail_subject
        self.mail_date = mail_date
        self.mail_size = mail_size
        self.original_headers = original_headers

    def __repr__(self):
        headers = ('To: {}\n'
                   'From: {}\n'
                   'Subject: {}\n'
                   'Date: {}\n'
                   'Size: {} bytes\n').format(
            self.mail_to,
            self.mail_from,
            self.mail_subject,
            self.mail_date,
            self.mail_size)
        return headers


def save_letters(letters_info):
    for letter_number in range(len(letters_info)):
        try:
            with open('Letter {}.txt'.format(str(letter_number + 1)), 'w') as file:
                file.write(repr(letters_info[letter_number]))
            print('Letter {}'.format(str(letter_number + 1)) + ' has been saved!')
        except IOError:
            print('Error!')


def get_info(channel):
    letters_structs = []
    send(channel, 'LIST')
    for line in recv_lines(channel):
        msg_id, msg_size = map(int, line.split())
        send(channel, 'TOP {} 0'.format(msg_id))
        headers = recv_lines(channel)
        headers = '\n'.join(headers)
        important_headers = ['From', 'To', 'Subject', 'Date']
        important_headers_values = []
        for header in important_headers:
            important_headers_values.append(
                get_header(header, headers) or 'unknown')
        important_headers_values = list(
            map(decode, important_headers_values))
        msg_from, msg_to, msg_subj, msg_date \
            = important_headers_values
        letters_structs.append(MailStruct(
            msg_from, msg_to, msg_subj, msg_date, msg_size, headers))
    return letters_structs


def post_processing(s):
    flags = re.IGNORECASE | re.MULTILINE | re.DOTALL
    return re.sub(r'^\s*', '', s.strip(), flags=flags).replace('\n', '')


def get_header(header, headers):
    f = re.IGNORECASE | re.MULTILINE | re.DOTALL
    m = re.search(r'^{}:(.*?)(?:^\w|\Z|\n\n)'
                      .format(header), headers, f)
    if m:
        return post_processing(m.group(1))


def decode(value):
    def replace(match):
        encoding = match.group(1).lower()
        b64raw = match.group(2)
        raw = base64.b64decode(b64raw.encode())
        try:
            return raw.decode(encoding)
        except Exception as ex:
            print(ex)
            return match.group(0)

    return re.sub(r'=\?(.*?)\?b\?(.*?)\?=', replace, value, flags=re.IGNORECASE)


def send(channel, command):
    channel.write(command)
    channel.write('\n')
    channel.flush()


def recv_line(channel):
    response = channel.readline()[:-2]
    if response.startswith('-ERR'):
        raise POP3Exception(response)


class POP3Exception(Exception):
    def __init__(self, message):
        super().__init__(message)


def recv_lines(channel):
    recv_line(channel)
    lines = []
    while True:
        line = channel.readline()[:-2]
        if line == '.':
            break
        lines.append(line)
    return lines


def authentication(channel, username, password):
    send(channel, 'USER {}'.format(username))
    recv_line(channel)
    channel.write('PASS {}\n'.format(password))
    channel.flush()
    recv_line(channel)


def main():
    try:
        sock = socket.socket()
        sock.settimeout(10)
        sock = ssl.wrap_socket(sock)
        sock.connect((socket.gethostbyname(host), 995))
        channel = sock.makefile('rw', newline='\r\n', encoding='utf-8')
        recv_line(channel)
        authentication(channel, username, password)
        letters_info = get_info(channel)
        save_letters(letters_info)
    except Exception:
        print('Error! FILL IN INFORMATION IN pop3.py')
        print_help()


if __name__ == '__main__':
    main()

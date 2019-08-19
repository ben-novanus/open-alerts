from configparser import ConfigParser
from mail import Email
from models.exchange import Exchange


def main():
    config = ConfigParser(strict=False)
    config.read('config.ini')

    email = Email(config.get('Email', 'Server'), config.get('Email', 'Port'), config.get(
        'Email', 'TLS'), config.get('Email', 'User'), config.get('Email', 'Password'))
    email.processMail()

    # for section_name in config.sections():
    #     print('Section:', section_name)
    #     print('  Options:', config.options(section_name))
    #     for name, value in config.items(section_name):
    #         print(name, value)
    #     print()

    # for x in test_list:
    # if x.value == value:
    #    print "i found it!"
    # break


if __name__ == "__main__":
    main()

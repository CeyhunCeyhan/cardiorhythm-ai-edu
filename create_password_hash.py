"""Run locally; never enter actual passwords into GitHub or chat."""
from getpass import getpass
from security import make_hash

if __name__ == '__main__':
    print(make_hash(getpass('Enter a new password (12+ characters): ')))

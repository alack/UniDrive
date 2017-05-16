from subprocess import call
from sys import exit

returncode = call(["python", "-m", "unittest", "discover", "tests"])

exit(returncode)
from subprocess import call
from sys import exit

return_code = call(["python", "-m", "unittest", "discover", "-v", "tests"])

exit(return_code)
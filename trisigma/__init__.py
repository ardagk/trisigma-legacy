import os

os.environ.setdefault('CONFIG_DIR', os.path.join(os.getcwd(), 'config'))

if not os.getenv('NOENV'):
    from dotenv import load_dotenv
    load_dotenv(override=True, dotenv_path=os.path.join(os.path.join(os.getcwd(), '.env')))
os.system('export PYTHONPYCACHEPREFIX="$HOME/.cache/pycache/"')


from trisigma.api import policy
from trisigma.api import const
from trisigma.api import dtype
from trisigma.api import error
from trisigma.api import lib
from trisigma.api import entity
from trisigma.api import value
from trisigma.api import flag
from trisigma.api import irepo
from trisigma.api import base

from trisigma.api import inbound
from trisigma.api import outbound
from trisigma.api import interactor

from trisigma.api import middleware
from trisigma.api import primary
from trisigma.api import files
from trisigma.api import secondary
from trisigma.api import repo
from trisigma.api import command


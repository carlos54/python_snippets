from mailing import create_app
from mailing.config import UnitTest
import os

app = create_app(UnitTest)
pwd = os.path.dirname(__file__)


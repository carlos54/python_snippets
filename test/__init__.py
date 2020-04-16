from mailing import create_app
from mailing.config import UnitTest
import os

app = create_app(UnitTest)
pwd = os.path.dirname(__file__)
stc_path = os.path.join(pwd, "static/")
tps_path = os.path.join(pwd, "temps/")
app_template_path = app.config.get("TEMPLATE_DIR")


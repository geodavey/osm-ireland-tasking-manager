import base64

from flask_migrate import MigrateCommand
from flask_script import Manager
from dotenv import load_dotenv

from server import create_app, init_counters
from server.services.users.authentication_service import AuthenticationService
from server.services.users.user_service import UserService
from server.services.translation_service import TranslationService
from server.services.stats_service import StatsService

import os
import warnings

# Load configuration from file
load_dotenv(os.path.join(os.path.dirname(__file__), "tasking-manager.env"))

# Temporarily here - to support backwards compatibility with TM_DB key.
if os.getenv("TM_DB", False):
    for key in [
        "TM_APP_BASE_URL",
        "TM_SECRET",
        "TM_CONSUMER_KEY",
        "TM_CONSUMER_SECRET",
    ]:
        if not os.getenv(key):
            warnings.warn("%s environmental variable not set." % (key,))
else:
    # Check that required environmental variables are set
    for key in [
        "TM_APP_BASE_URL",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "TM_SECRET",
        "TM_CONSUMER_KEY",
        "TM_CONSUMER_SECRET",
        "TM_DEFAULT_CHANGESET_COMMENT",
    ]:
        if not os.getenv(key):
            warnings.warn("%s environmental variable not set." % (key,))

# Initialise the flask app object
application = create_app()
try:
    init_counters(application)
except Exception:
    warnings.warn("Homepage counters not initialized.")
manager = Manager(application)


# Enable db migrations to be run via the command line
manager.add_command("db", MigrateCommand)


@manager.option("-u", "--user_id", help="Test User ID")
def gen_token(user_id):
    """ Helper method for generating valid base64 encoded session tokens """
    token = AuthenticationService.generate_session_token_for_user(user_id)
    print(f"Raw token is: {token}")
    b64_token = base64.b64encode(token.encode())
    print(f"Your base64 encoded session token: {b64_token}")


@manager.command
def refresh_levels():
    print("Started updating mapper levels...")
    users_updated = UserService.refresh_mapper_level()
    print(f"Updated {users_updated} user mapper levels")


@manager.command
def refresh_translatables():
    print("Exporting translatable strings")
    TranslationService.refresh_translatables()


@manager.command
def refresh_project_stats():
    print("Started updating project stats...")
    StatsService.update_all_project_stats()
    print("Project stats updated")


if __name__ == "__main__":
    manager.run()

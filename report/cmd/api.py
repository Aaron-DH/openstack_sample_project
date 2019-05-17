from report import service
from report.api import app

import sys


def main():
    service.prepare_service(sys.argv)
    app.build_server()

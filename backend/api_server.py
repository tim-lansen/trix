# -*- coding: utf-8 -*-

from modules.utils.api_trix import ApiTrix, ApiClient, WebsocketServer
from modules.config import TRIX_CONFIG
from modules.utils.log_console import Logger
from modules.utils.mount_paths import mount_paths


if __name__ == "__main__":
    Logger.set_console_level(Logger.LogLevel.TRACE)
    mount_paths({'watch'})
    api_server = WebsocketServer(port=TRIX_CONFIG.apiServer.port, host='0.0.0.0', apiClass=ApiTrix, clientClass=ApiClient)
    api_server.serve_forever()

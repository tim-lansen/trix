# -*- coding: utf-8 -*-

from modules.utils.database import DBInterface
from modules.models.asset import Asset
from modules.utils.log_console import Logger


if __name__ == '__main__':
    # dBase = {
    #     'templates': {},
    #     'tables': {}
    # }
    # modules.utils.database.config_table_using_class(modules.models.job.Job, dBase)
    # modules.utils.database.config_table_using_class(modules.models.asset.Asset, dBase)
    # print(json.dumps(dBase, indent=2))

    DBInterface._drop_all_tables()
    DBInterface.initialize()
    asset: Asset = Asset()
    asset.guid.new()
    asset.name = ''
    asset.mediaFiles = [Asset.MediaFile(0), Asset.MediaFile(0), Asset.MediaFile(0)]
    Logger.debug('{}\n'.format(asset.dumps(indent=2)), Logger.LogLevel.LOG_WARNING)
    DBInterface.Asset.set(asset)
    asset = DBInterface.Asset.get(asset.guid)
    Logger.debug('{}\n'.format(asset.dumps(indent=2)), Logger.LogLevel.LOG_INFO)
    DBInterface.Asset.delete(asset.guid)


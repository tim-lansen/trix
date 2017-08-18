# -*- coding: utf-8 -*-

from modules.utils.database import DBInterface
from modules.models.asset import Asset
from modules.utils.types import Guid


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
    asset = Asset()
    asset.guid.new()
    asset.name = ''
    asset.mediaFiles = [Asset.MediaFile(0), Asset.MediaFile(0), Asset.MediaFile(0)]
    DBInterface.Asset.set(asset)
    asset = DBInterface.Asset.get(asset.guid)
    print(asset.dumps(indent=2))
    DBInterface.Asset.delete(asset.guid)


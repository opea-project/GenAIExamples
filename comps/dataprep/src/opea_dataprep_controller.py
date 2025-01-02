# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import os

from comps import CustomLogger, OpeaComponentController

logger = CustomLogger("opea_dataprep_controller")
logflag = os.getenv("LOGFLAG", False)


class OpeaDataprepController(OpeaComponentController):
    def __init__(self):
        super().__init__()

    def invoke(self, *args, **kwargs):
        pass

    async def ingest_files(self, *args, **kwargs):
        if logflag:
            logger.info("[ dataprep controller ] ingest files")
        return await self.active_component.ingest_files(*args, **kwargs)

    async def get_files(self, *args, **kwargs):
        if logflag:
            logger.info("[ dataprep controller ] get files")
        return await self.active_component.get_files(*args, **kwargs)

    async def delete_files(self, *args, **kwargs):
        if logflag:
            logger.info("[ dataprep controller ] delete files")
        return await self.active_component.delete_files(*args, **kwargs)

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps import CustomLogger, OpeaComponentLoader

logger = CustomLogger("opea_finetuning_loader")


class OpeaFinetuningLoader(OpeaComponentLoader):
    def __init__(self, component_name, **kwargs):
        super().__init__(component_name=component_name, **kwargs)

    def invoke(self, *args, **kwargs):
        pass

    def create_finetuning_jobs(self, *args, **kwargs):
        return self.component.create_finetuning_jobs(*args, **kwargs)

    def cancel_finetuning_job(self, *args, **kwargs):
        return self.component.cancel_finetuning_job(*args, **kwargs)

    def list_finetuning_checkpoints(self, *args, **kwargs):
        return self.component.list_finetuning_checkpoints(*args, **kwargs)

    def list_finetuning_jobs(self, *args, **kwargs):
        return self.component.list_finetuning_jobs(*args, **kwargs)

    def retrieve_finetuning_job(self, *args, **kwargs):
        return self.component.retrieve_finetuning_job(*args, **kwargs)

    async def upload_training_files(self, *args, **kwargs):
        return await self.component.upload_training_files(*args, **kwargs)

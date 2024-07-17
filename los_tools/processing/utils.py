from processing.core.ProcessingConfig import ProcessingConfig

from los_tools.constants.settings import Settings


class LoSToolsSettings:
    @staticmethod
    def sample_Z_using_plugin() -> bool:
        return ProcessingConfig.getSetting(Settings.name_sample_z)

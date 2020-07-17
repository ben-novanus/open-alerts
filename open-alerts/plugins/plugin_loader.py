import logging
from plugins.flags import Flags
from plugins.switch_pt_config import SwitchPtConfig


class PluginLoader:
    @staticmethod
    def processPluginBlock(alert, block):
        logger = logging.getLogger('main')
        logger.info("Processing plugin block: %s", block.plugin)

        if block.plugin == "FLAGS":
            return Flags.processBlock(alert, block)
        elif block.plugin == "SWITCH-PT-CONFIG":
            return SwitchPtConfig.processBlock(alert, block)
        else:
            logger.error("No plugin found for name: %s", block.plugin)
            return False

import logging
from plugins.require_environment import RequireEnvironment
from plugins.switch_pt_config import SwitchPtConfig


class PluginLoader:
    @staticmethod
    def processPluginBlock(alert, block):
        logger = logging.getLogger('main')
        logger.info("Processing plugin block: %s", block.plugin)

        if block.plugin == "require-environment":
            return RequireEnvironment.processBlock(alert, block)
        elif block.plugin == "switch-pt-config":
            return SwitchPtConfig.processBlock(alert, block)
        else:
            logger.error("No plugin found for name: %s", block.plugin)
            return False

import logging
from plugins.require_environment import RequireEnvironment


class PluginLoader:
    @staticmethod
    def processPluginBlock(alert, block):
        logger = logging.getLogger('main')
        logger.info("Processing plugin block: %s", block.plugin)

        if block.plugin == "require-environment":
            return RequireEnvironment.processBlock(alert, block)
        else:
            logger.error("No plugin found for name: %s", block.plugin)
            return False

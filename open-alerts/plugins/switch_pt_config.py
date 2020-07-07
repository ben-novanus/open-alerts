import logging
import requests


class SwitchPtConfig:
    @staticmethod
    def processBlock(alert, block):
        logger = logging.getLogger('main')

        logger.info(
            "Switching the Profit Trailer active config to %s", block.pt_config)

        logger.debug("Using the PT license: %s and url: %s",
                     block.pt_license, block.pt_url)

        if block.pt_license and block.pt_url:
            headers = {"accept": "*/*"}
            data = {
                "configName": block.pt_config,
                "license": block.pt_license
            }

            try:
                r = requests.post(block.pt_url, headers=headers, data=data)
            except requests.exceptions.RequestException as e:
                logger.error(
                    "Unable to complete Profit Trailer Switch Config request: %s", e)

            if r.status_code == 304:
                logger.warning(
                    "Profit Trailer config was not switched from the original, code: %s", r.status_code)
            if r.status_code != 200:
                logger.error(
                    "Error switching Profit Trailer config, code: %s", r.status_code)

        return True

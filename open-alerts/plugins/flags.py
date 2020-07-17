import logging
import json
from datetime import datetime, timedelta
import os
import time


class Flags:
    @staticmethod
    def processBlock(alert, block):
        logger = logging.getLogger('main')
        file_name = "flags.json"
        date_time_format = "%d/%m/%Y %H:%M:%S"
        max_days = 7

        if block.max_days:
            max_days = int(block.max_days)

        logger.debug("Setting max time to %s days", max_days)
        max_time = datetime.now() - timedelta(days=max_days)

        try:
            with open(file_name) as infile:
                data = json.load(infile)
        except IOError:
            logger.debug("File %s does not exist", file_name)
            data = {}
        except ValueError:
            logger.error(
                "File %s does not contain valid json, reseting flags", file_name)
            data = {}

        if block.action == "STORE":
            logger.debug(
                "Storing flag %s with a direction of %s", block.name, block.direction.value)

            directionData = {
                "direction": block.direction.value,
                "timestamp": datetime.now().strftime(date_time_format)
            }

            data[block.name] = directionData

            with open(file_name, 'w') as outfile:
                json.dump(data, outfile)

            return True
        elif block.action == "REQUIRE":
            if data and data[block.name]:
                logger.debug(
                    "Checking for required flag %s with a direction of %s. Found %s direction with timestamp %s",
                    block.name, block.direction.value, data[block.name].get("direction"), data[block.name].get("timestamp"))

                timestamp = datetime.strptime(
                    data[block.name].get("timestamp"), date_time_format)
                if (data[block.name].get("direction") == block.direction.value and
                        timestamp > max_time):
                    return True
                elif timestamp < max_time:
                    logger.error(
                        "Check for required flag %s did not pass, timestamp for stored flag is to old",
                        block.name)
                    return False
                else:
                    logger.warning(
                        "Check for required flag %s did not pass",
                        block.name)
                    return False
            else:
                logger.debug("Flag json for %s contains no data",
                             block.name)

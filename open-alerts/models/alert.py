import re
import logging
from .block import Block


class Alert:
    def __init__(self, body):
        self.logger = logging.getLogger("main")
        self.exchange = ""
        self.account = ""
        self.instrument = ""
        self.currency = ""
        self.blocks = []

        self.parseBody(body)

    def parseBody(self, body):
        # TODO add autoview syntax parsing
        if "account =" in body or "account=" in body:
            self.parseGoatAlert(body)
        elif "a =" in body or "a=" in body:
            self.parseAutoViewAlert(body)

    def parseGoatAlert(self, body):
        lines = body.split('\\n')
        currentBlock = 0

        blockFields = [attr for attr in dir(Block) if not callable(
            getattr(Block, attr)) and not attr.startswith("__")]

        for line in lines:
            # goat syntax
            match = re.match('([a-zA-Z_]+)(?:\s*)=(?:\s*)([^\n]+)', line)
            if not match:
                match_num = re.match('\[(\d)\]', line)

            if match:
                key = match[1].lower()
                val = match[2].upper()

                if key in blockFields and currentBlock > 0:
                    try:
                        block = self.blocks[currentBlock]
                    except IndexError:
                        block = Block()
                        self.blocks.insert(currentBlock, block)

                    setattr(block, key, val)
                elif key == "account":
                    self.account = val.lower()
                elif key == "exchange":
                    self.exchange = val.lower()
                elif key == "instrument":
                    self.instrument = val
                    match = re.match('^([A-Z]{3})-.+', val)
                    if match:
                        self.currency = match[1]
                    else:
                        self.logger.error("Unable to parse currency from \
instrument: %s", val)

            elif match_num:
                currentBlock = int(match_num[1])

    def parseAutoViewAlert(self, body):
        self.error.error("Autoview syntax is not supported yet")
        # lines = body.split('\\n')
        # currentBlock = 0

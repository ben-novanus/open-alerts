import re
from .block import Block


class Alert:
    def __init__(self, body):
        self.exchange = ""
        self.account = []
        self.instrument = ""
        self.blocks = []
        self.currency = ""

        self.parseBody(body)

    def parseBody(self, body):
        # TODO add autoview syntax parsing
        self.parseGoatAlert(body)

    def parseGoatAlert(self, body):
        lines = body.splitlines()
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
                    self.account = val.replace(' ', '').split(',')
                elif key == "exchange":
                    self.exchange = val.lower()
                elif key == "currency":
                    self.currency = val
                elif key == "instrument":
                    self.instrument = val

            elif match_num:
                currentBlock = int(match_num[1])

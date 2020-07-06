import re
import logging
from .block import Block
from .block import Type as BlockType
from .block import OrderType
from .block import Direction
from .block import Trigger


class Alert:
    def __init__(self, body):
        self.logger = logging.getLogger("main")
        self.exchange = ""
        self.account = ""
        self.symbol = ""
        self.currency = ""
        self.blocks = []

        self.parseBody(body)

    def parseBody(self, body):
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
            match = re.match('([a-zA-Z_]+)(?:\s*)=(?:\s*)([^\n]+)', line)
            if not match:
                match_num = re.match('\[(\d)\]', line)

            if match:
                key = match[1].lower()
                val = match[2].upper()

                if ((key in blockFields and currentBlock) > 0 or
                        key == "cancel" or key == "close" or
                        key == "order" or key == "adjust" or
                        key == "plugin" or key == "side"):
                    blockIndex=currentBlock - 1
                    try:
                        block=self.blocks[blockIndex]
                    except IndexError:
                        block=Block()
                        self.blocks.insert(blockIndex, block)

                    if key == "cancel":
                        block.type=BlockType.CANCEL_ORDER
                    elif key == "close":
                        block.type=BlockType.CLOSE_POSITION
                    elif key == "adjust":
                        block.type=BlockType.ADJUST_POSITION
                    elif key == "plugin":
                        block.type=BlockType.PLUGIN
                        block.plugin=val.lower()
                    elif key == "order":
                        if not block.type:
                            block.type=BlockType.STANDARD_ORDER
                        if val == "MARKET":
                            block.orderType=OrderType.MARKET
                        elif val == "LIMIT":
                            block.orderType=OrderType.LIMIT
                        elif val == "STOP_MARKET":
                            block.orderType=OrderType.STOP_MARKET
                        elif val == "STOP_LIMIT":
                            block.orderType=OrderType.STOP_LIMIT
                        elif val == "TRAILING_STOP":
                            block.orderType=OrderType.TRAILING_STOP
                        elif val == "TAKE_PROFIT_MARKET":
                            block.orderType=OrderType.TAKE_PROFIT_MARKET
                        elif val == "TAKE_PROFIT_LIMIT":
                            block.orderType=OrderType.TAKE_PROFIT_LIMIT
                    elif key == "side":
                        if val == "BUY" or val == "LONG":
                            block.direction=Direction.BUY
                        elif val == "SELL" or val == "SHORT":
                            block.direction=Direction.SELL
                    elif key == "trigger":
                        if val == "LAST":
                            block.trigger=Trigger.LAST
                        elif val == "INDEX":
                            block.trigger=Trigger.INDEX
                        elif val == "MARK":
                            block.trigger=Trigger.MARK
                    elif (key == "close_on_trigger" or key == "post_only" or
                          key == "reduce_only" or key == "new_position_only"):
                        if val == "TRUE":
                            setattr(block, key, True)
                    else:
                        setattr(block, key, val)
                elif key == "account":
                    self.account=val.lower()
                elif key == "exchange":
                    self.exchange=val.lower()
                elif key == "symbol":
                    self.symbol=val
                    match=re.match('^([A-Z]{3})-?.+', val)
                    if match:
                        self.currency=match[1]
                    else:
                        self.logger.error(("Unable to parse currency from "
                                           "symbol: %s"), val)

            elif match_num:
                currentBlock=int(match_num[1])

    def parseAutoViewAlert(self, body):
        self.logger.error("Autoview syntax is not yet supported")

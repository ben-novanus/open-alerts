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
        self.accounts = []
        self.symbol = ""
        self.currency = ""
        self.blocks = []

        self.parseBody(body)

    def parseBody(self, body):
        if "account =" in body or "account=" in body:
            self.parseGoatAlert(body)
        elif "a=" in body or "delay=" in body:
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
                key = match.group(1).lower()

                if key.startswith("pt_"):
                    val = match.group(2)
                else:
                    val = match.group(2).upper()

                if ((key in blockFields and currentBlock) > 0 or
                        key == "cancel" or key == "close" or
                        key == "order" or key == "adjust" or
                        key == "plugin" or key == "side"):
                    blockIndex = currentBlock - 1
                    try:
                        block = self.blocks[blockIndex]
                    except IndexError:
                        block = Block()
                        self.blocks.insert(blockIndex, block)

                    if key == "cancel":
                        block.type = BlockType.CANCEL_ORDER
                    elif key == "close":
                        block.type = BlockType.CLOSE_POSITION
                    elif key == "adjust":
                        block.type = BlockType.ADJUST_POSITION
                    elif key == "plugin":
                        block.type = BlockType.PLUGIN
                        block.plugin = val
                    elif key == "order":
                        if not block.type:
                            block.type = BlockType.STANDARD_ORDER
                        if val == "MARKET":
                            block.orderType = OrderType.MARKET
                        elif val == "LIMIT":
                            block.orderType = OrderType.LIMIT
                        elif val == "STOP_MARKET":
                            block.orderType = OrderType.STOP_MARKET
                        elif val == "STOP_LIMIT":
                            block.orderType = OrderType.STOP_LIMIT
                        elif val == "TRAILING_STOP":
                            block.orderType = OrderType.TRAILING_STOP
                        elif val == "TAKE_PROFIT_MARKET":
                            block.orderType = OrderType.TAKE_PROFIT_MARKET
                        elif val == "TAKE_PROFIT_LIMIT":
                            block.orderType = OrderType.TAKE_PROFIT_LIMIT
                    elif key == "side":
                        if val == "BUY" or val == "LONG":
                            block.direction = Direction.BUY
                        elif val == "SELL" or val == "SHORT":
                            block.direction = Direction.SELL
                    elif key == "trigger":
                        if val == "LAST":
                            block.trigger = Trigger.LAST
                        elif val == "INDEX":
                            block.trigger = Trigger.INDEX
                        elif val == "MARK":
                            block.trigger = Trigger.MARK
                    elif (key == "close_on_trigger" or key == "post_only" or
                          key == "reduce_only" or key == "new_position_only"):
                        if val == "TRUE":
                            setattr(block, key, True)
                    else:
                        setattr(block, key, val)
                elif key == "account":
                    if "," in val:
                        self.accounts = val.lower().split(",")
                    else:
                        self.accounts = [val.lower()]
                elif key == "exchange":
                    self.exchange = val.lower()
                elif key == "symbol":
                    self.symbol = val
                    match = re.match('^([A-Z]{3})-?.+', val)
                    if match:
                        self.currency = match.group(1)
                    else:
                        self.logger.error(("Unable to parse currency from "
                                           "symbol: %s"), val)
            elif match_num:
                currentBlock = int(match_num.group(1))

    def parseAutoViewAlert(self, body):
        lines = body.split('\\n')

        blockFields = ["b", "c", "delay", "l", "p", "pxs", "q",
                       "ro", "sl", "t", "tp", "ts"]

        for line in lines:
            commands = line.lower().split()
            block = Block()
            commandDict = {}
            for command in commands:
                match = re.match('([a-zA-Z_]+)=([^\n]+)', command)

                if match:
                    commandDict[match.group(1)] = match.group(2).upper()
                else:
                    self.logger.error(("Unknown command: %s"), command)

            for key, val in commandDict.items():
                if key in blockFields:
                    if key == "delay":
                        block.wait = val
                    elif key == "t":
                        if not block.type:
                            block.type = BlockType.STANDARD_ORDER

                        if not block.orderType:
                            if val == "MARKET":
                                block.orderType = OrderType.MARKET
                            elif val == "LIMIT":
                                block.orderType = OrderType.LIMIT
                            elif val == "FOK":
                                self.logger.error(("Fill or Kill is not currently a "
                                                   "valid order type"))
                            elif val == "IOC":
                                self.logger.error(("Immediate or Cancel is not currently a "
                                                   "valid order type"))
                            elif val == "POST":
                                block.orderType = OrderType.LIMIT
                                block.post_only = True
                    elif key == "c":
                        if val == "ORDER":
                            block.type = BlockType.CANCEL_ORDER
                        elif val == "POSITION":
                            # if line containsts this is an adjust
                            if commandDict.get("ts"):
                                block.type = BlockType.ADJUST_POSITION
                            else:
                                block.type = BlockType.CLOSE_POSITION
                    elif key == "b":
                        if not block.direction:
                            if val == "BUY" or val == "LONG":
                                block.direction = Direction.BUY
                            elif val == "SELL" or val == "SHORT":
                                block.direction = Direction.SELL
                    elif key == "pxs":
                        if val == "LAST":
                            block.trigger = Trigger.LAST
                        elif val == "INDEX":
                            block.trigger = Trigger.INDEX
                        elif val == "MARK":
                            block.trigger = Trigger.MARK
                    elif key == "ro" and val == "1":
                        block.reduce_only = True
                    elif key == "sl":
                        # block.stop_loss = val
                        block.orderType = OrderType.STOP_MARKET
                        if commandDict.get("ps") == "position":
                            block.stop_price = val
                        else:
                            block.stop_price_m = val
                        block.post_only = True
                        block.reduce_only = True
                    elif key == "tp":
                        # block.take_profit = val
                        block.orderType = OrderType.STOP_LIMIT
                        block.limit_price_m = val
                        if commandDict.get("p"):
                            if commandDict.get("ps") and commandDict.get("p").lower() == "position":
                                block.stop_price = commandDict.get("p")
                            else:
                                block.stop_price_m = commandDict.get("p")
                        if not commandDict.get("q"):
                            block.quantity = "100%"
                        # Hack because for AV syntax your take profit direction is backwards
                        if commandDict.get("b"):
                            if commandDict.get("b") == "BUY" or commandDict.get("b") == "LONG":
                                block.direction = Direction.SELL
                            elif commandDict.get("b") == "SELL" or commandDict.get("b") == "SHORT":
                                block.direction = Direction.BUY
                        block.post_only = True
                        block.reduce_only = True
                    elif key == "ts":
                        block.trailing_stop = val
                    elif key == "l":
                        block.leverage = val
                    elif key == "q":
                        block.quantity = val
                    elif key == "p":
                        block.limit_price = val
                elif key == "a":
                    if "," in val:
                        self.accounts = val.lower().split(",")
                    else:
                        self.accounts = [val.lower()]
                elif key == "e":
                    self.exchange = val.lower()
                elif key == "s":
                    self.symbol = val
                    match = re.match('^([A-Z]{3})-?.+', val)
                    if match:
                        self.currency = match.group(1)
                    else:
                        self.logger.error(("Unable to parse currency from "
                                           "symbol: %s"), val)
            self.blocks.append(block)

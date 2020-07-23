from enum import Enum


class Type(Enum):
    CANCEL_ORDER = "Cancel Order"
    CLOSE_POSITION = "Close Position"
    STANDARD_ORDER = "Standard Order"
    ADJUST_POSITION = "Adjust Position"
    PLUGIN = "Plugin"


class OrderType(Enum):
    MARKET = "Market"
    LIMIT = "Limit"
    STOP_MARKET = "Stop Market"
    STOP_LIMIT = "Stop Limit"
    TRAILING_STOP = "Trailing Stop"
    TAKE_PROFIT_MARKET = "Take Profit Market"
    TAKE_PROFIT_LIMIT = "Take Profit Limit"


class Direction(Enum):
    BUY = "Buy"
    SELL = "Sell"


class Trigger(Enum):
    LAST = "Last"
    INDEX = "Index"
    MARK = "Mark"


class Block:
    type = None
    orderType = None
    direction = None

    close_on_trigger = False
    leverage = ""
    limit_price = ""
    limit_price_m = ""
    post_only = False
    quantity = ""
    reduce_only = False
    signal_type = ""
    stop_loss = ""
    stop_price = ""
    stop_price_m = ""
    take_profit = ""
    trail_value = ""
    trigger = None
    wait = ""
    trailing_stop = ""
    in_profit_only = ""
    new_position_only = False
    plugin = ""
    action = ""
    name = ""
    max_days = ""
    pt_config = ""
    pt_license = ""
    pt_url = ""

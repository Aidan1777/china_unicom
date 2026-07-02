"""Constants for the China Unicom integration."""
from homeassistant.const import Platform

DOMAIN = "china_unicom"
NAME = "China Unicom"

PLATFORMS = [Platform.SENSOR]

# Configuration keys
CONF_OPENID = "openid"
CONF_PHONE_NUMBER = "phone_number"
CONF_REFRESH_INTERVAL = "refresh_interval"

# Default values
DEFAULT_REFRESH_INTERVAL = 15  # minutes

# API Endpoints
API_SSPBIGBALL = "https://mina.10010.com/wxapplet/weixinNew/sspbigball"
API_USAGE_DETAIL = (
    "https://mxx.client.10010.com/servicequerybusiness"
    "/operationservice/queryOcsPackageFlowLeftContentRevisedInJune"
)
API_BALANCE_DETAIL = (
    "https://mxx.client.10010.com/servicequerybusiness"
    "/balancenew/accountBalancenew.htm"
)
API_GET_TICKET = "https://mina.10010.com/wxapplet/weixinNew/getTicket"
API_SERVICE_ENTRANCE = "https://mxx.client.10010.com/servicebusiness/wx/serviceEntrance"
API_QUERY_GOODS_LIST = "https://mina.10010.com/wxapplet/weixinNew/queryGoodsList"

# Request headers
HEADERS_JSON = {"Content-Type": "application/json"}
HEADERS_FORM = {"Content-Type": "application/x-www-form-urlencoded"}

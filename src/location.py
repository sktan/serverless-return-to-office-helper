import json
import urllib.request

from aws_lambda_powertools.utilities.parser import BaseModel


class IpApiResponse(BaseModel):
    status: str
    country: str
    countryCode: str
    region: str
    regionName: str
    timezone: str


def get_ip_location(ipaddr: str) -> IpApiResponse:
    """
    Get the location of the specified IP address

    Args:
        ipaddr (str): The IP address
    """

    with urllib.request.urlopen(f"http://ip-api.com/json/{ipaddr}") as response:
        data = json.loads(response.read())

    return IpApiResponse(**data)

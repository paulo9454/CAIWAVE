from enum import Enum


class CampaignCoverageScope(str, Enum):
    NATIONAL = "national"
    COUNTY = "county"
    CONSTITUENCY = "constituency"
    HOTSPOT = "hotspot"

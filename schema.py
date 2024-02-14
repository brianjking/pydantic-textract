from pydantic import BaseModel, validator, ValidationError
from enum import Enum
from typing import List, Optional
from datetime import datetime

class MediaTypeEnum(str, Enum):
    """Data model for the CFM media types."""
    Print = "Print"
    Outdoor = "Outdoor"
    Point_of_Purchase = "Point of Purchase"
    Broadcast = "Broadcast"
    Events = "Events"
    Digital = "Digital"
    Facility_Branding = "Facility Branding"
    Sponsorships = "Sponsorships"
    Signage = "Signage"
    Vehicle_Wraps = "Vehicle Wraps"
    Unknown = "Unknown"

class ActivityTypeEnum(str, Enum):
    """Data model for the CFM activity types."""
    DirectMail = "Direct Mail"
    LocalAd = "Local Ad"
    RegionalAd = "Regional Ad"
    Handouts = "Hand-outs"
    Billboards = "Billboards"
    Signage = "Signage"
    DealerDisplayAdvertising = "Dealer Display Advertising"
    Television = "Television"
    Radio = "Radio"
    Tradeshows = "Tradeshows"
    Exhibition = "Exhibition"
    eBlast = "e-Blast"
    MusicChannel = "Music Channel"
    PaidListing = "Paid Listing"
    OnlineDisplayAd = "Online Display Ad"
    PaidSearch = "Paid Search"
    SocialAd = "Social Ad"
    SearchEngineOptimization = "Search Engine Optimization (SEO)"
    BMISocialProgram = "BMI Social Program"
    BMIPaidMedia = "BMI Paid Media"
    CTV = "CTV"
    Kenect = "Kenect"
    FacilityUpgrades = "Facility Upgrades"
    Sponsorship = "Sponsorship"
    DealerSignage = "Dealer Signage"
    VehicleWrapsDecals = "Vehicle Wraps/Decals"
    Unknown = "Unknown"

class CFM(BaseModel):
    """Data model for the CFM types."""
    vendor_merchant_name: str
    bill_invoice_amount: str
    requested_amount: str = ""
    date_of_invoice: str
    claim_start_date: Optional[str] = None
    claim_end_date: Optional[str] = None
    media_type: MediaTypeEnum
    activity_type: ActivityTypeEnum
    comments: str = ""
    description: str = ""
    account_id_number: str = ""
    invoice: str = ""

    @validator('claim_start_date', 'claim_end_date', pre=True, always=True)
    def default_claim_dates(cls, v, values, field):
        if v is None:
            return values['date_of_invoice']
        return v

    @validator('requested_amount', pre=True, always=True)
    def default_requested_amount(cls, v, values):
        if not v:
            return values['bill_invoice_amount']
        return v

    @validator('activity_type', pre=True, always=True)
    def validate_activity_type(cls, v, values):
        media_type = values.get('media_type', MediaTypeEnum.Unknown)  # Default to Unknown if not provided
        valid_activities = {
            MediaTypeEnum.Print: [ActivityTypeEnum.DirectMail, ActivityTypeEnum.LocalAd, ActivityTypeEnum.RegionalAd, ActivityTypeEnum.Handouts, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Outdoor: [ActivityTypeEnum.Billboards, ActivityTypeEnum.Signage, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Point_of_Purchase: [ActivityTypeEnum.DealerDisplayAdvertising, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Broadcast: [ActivityTypeEnum.Television, ActivityTypeEnum.Radio, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Events: [ActivityTypeEnum.Tradeshows, ActivityTypeEnum.Exhibition, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Digital: [ActivityTypeEnum.eBlast, ActivityTypeEnum.MusicChannel, ActivityTypeEnum.PaidListing, ActivityTypeEnum.OnlineDisplayAd, ActivityTypeEnum.PaidSearch, ActivityTypeEnum.SocialAd, ActivityTypeEnum.SearchEngineOptimization, ActivityTypeEnum.BMISocialProgram, ActivityTypeEnum.BMIPaidMedia, ActivityTypeEnum.CTV, ActivityTypeEnum.Kenect, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Facility_Branding: [ActivityTypeEnum.FacilityUpgrades, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Sponsorships: [ActivityTypeEnum.Sponsorship, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Signage: [ActivityTypeEnum.DealerSignage, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Vehicle_Wraps: [ActivityTypeEnum.VehicleWrapsDecals, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Unknown: [ActivityTypeEnum.Unknown],  # Ensures fallback to Unknown for any unhandled media types
        }
        # Default to Unknown if the activity type is not valid for the given media type
        if not valid_activities[media_type].__contains__(v):
            return ActivityTypeEnum.Unknown
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%m-%d-%Y'),  # Adjust date format as requested
        }

class Cocktail(BaseModel):
    """Data model for the Cocktail Menu items."""
    cocktail_name: str
    brands: List[str]  # Updated to accommodate multiple brands
    products: List[str]  # Updated to accommodate multiple products
    ingredients: List[str]
    price: float
    size: str
    description: str

class Menu(BaseModel):
    """Data model for the Menu."""
    cocktails: List[Cocktail]

from pydantic import BaseModel, validator, ValidationError, constr
from enum import Enum
from typing import List
from datetime import datetime 


class MediaTypeEnum(str, Enum):
    """Data model for the media types on CFM invoices."""
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
    """Data model for processing CFM co-op claim invoices and receipts."""
    vendor_merchant_name: str  # The company providing the service or product, issuing the invoice.
    bill_invoice_amount: str  # The original amount billed on the invoice.
    requested_amount: str = ""  # The amount being claimed, defaults to bill_invoice_amount if not provided.
    date_of_invoice: datetime  # Invoice date, used as default for claim dates if they're not specified.
    claim_start_date: datetime = None  # The start date for the claim period.
    claim_end_date: datetime = None  # The end date for the claim period.
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
        media_type = values.get('media_type')
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
            MediaTypeEnum.Unknown: [ActivityTypeEnum.Unknown],
        }
        if media_type and v not in valid_activities.get(media_type, []):
            raise ValueError(f"Invalid activity type '{v}' for media type '{media_type}'")
        return v

class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d'),
        }

class Cocktail(BaseModel):
    """Data model for individual cocktails on a menu."""
    cocktail_name: constr(strip_whitespace=True, min_length=1)  # Name of the cocktail
    brand: constr(strip_whitespace=True, min_length=1)  # Non-empty string that trims whitespace
    product: constr(strip_whitespace=True, min_length=1)  # Non-empty string that trims whitespace
    ingredients: List[constr(strip_whitespace=True, min_length=1)]  # List of non-empty strings that make up the cocktail
    price: float  # Price of the cocktail
    size: constr(strip_whitespace=True, min_length=1)  # Description of size, e.g., '500ml', '1 pint'
    description: constr(strip_whitespace=True, min_length=1)  # Detailed description of the cocktail

class Menu(BaseModel):
    """Data model for processing a cocktail menu to a schema, containing multiple cocktails."""
    cocktails: List[Cocktail]  # List of cocktails on the menu

from pydantic import BaseModel, validator, ValidationError
from enum import Enum

class ActivityTypeEnum(str, Enum):
    DirectMail = "DirectMail"
    LocalAd = "LocalAd"
    RegionalAd = "RegionalAd"
    Handouts = "Hand-outs"
    Billboard = "Billboard"
    ExternalBrandingSignage = "External Branding Signage"
    DealerDisplayAdvertising = "Dealer Display Advertising"
    RadioAd = "RadioAd"
    TVAd = "TVAd"
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
    BMIEmailProgram = "BMI Email Program"
    BMIPaidMedia = "BMI Paid Media"
    CTV = "CTV"
    Kenect = "Kenect"
    FacilityUpgrades = "Facility Upgrades"
    Sponsorship = "Sponsorship"
    DealerSignage = "Dealer Signage"
    VehicleWrapsDecals = "Vehicle Wraps/Decals"
    Unknown = "Unknown"

class MediaTypeEnum(str, Enum):
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

class InsAds(BaseModel):
    """Data model for a CFM."""
    vendor_merchant_name: str
    bill_invoice_amount: str
    date_of_invoice: str
    media_type: MediaTypeEnum
    activity_type: ActivityTypeEnum
    comments: str = ""
    description: str = ""
    account_id_number: str = ""
    invoice: str = ""

    @validator('activity_type', pre=True, always=True)
    def validate_activity_type(cls, v, values):
        media_type = values.get('media_type')
        valid_activities = {
            MediaTypeEnum.Print: [ActivityTypeEnum.DirectMail, ActivityTypeEnum.LocalAd, ActivityTypeEnum.RegionalAd, ActivityTypeEnum.Handouts, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Outdoor: [ActivityTypeEnum.Billboard, ActivityTypeEnum.ExternalBrandingSignage, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Point_of_Purchase: [ActivityTypeEnum.DealerDisplayAdvertising, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Broadcast: [ActivityTypeEnum.RadioAd, ActivityTypeEnum.TVAd, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Events: [ActivityTypeEnum.Tradeshows, ActivityTypeEnum.Exhibition, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Digital: [ActivityTypeEnum.eBlast, ActivityTypeEnum.MusicChannel, ActivityTypeEnum.PaidListing, ActivityTypeEnum.OnlineDisplayAd, ActivityTypeEnum.PaidSearch, ActivityTypeEnum.SocialAd, ActivityTypeEnum.SearchEngineOptimization, ActivityTypeEnum.BMISocialProgram, ActivityTypeEnum.BMIEmailProgram, ActivityTypeEnum.BMIPaidMedia, ActivityTypeEnum.CTV, ActivityTypeEnum.Kenect, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Facility_Branding: [ActivityTypeEnum.FacilityUpgrades, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Sponsorships: [ActivityTypeEnum.Sponsorship, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Signage: [ActivityTypeEnum.DealerSignage, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Vehicle_Wraps: [ActivityTypeEnum.VehicleWrapsDecals, ActivityTypeEnum.Unknown],
            MediaTypeEnum.Unknown: [ActivityTypeEnum.Unknown],
        }
        if media_type and v not in valid_activities.get(media_type, []):
            return ActivityTypeEnum.Unknown
        return v

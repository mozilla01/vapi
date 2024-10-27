from pydantic import BaseModel, Field, ConfigDict
from pydantic.functional_validators import BeforeValidator
from typing import Optional, List
from typing_extensions import Annotated
from datetime import datetime
from bson import ObjectId

PyObjectId = Annotated[str, BeforeValidator(str)]


class PageModel(BaseModel):
    """
    Container for a single Page record
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    url: str = Field(...)
    title: Optional[str] = Field(...)
    text: List[str] = Field(...)
    anchor_text: Optional[str] = Field(...)
    outgoing: Optional[List[str]] = Field(default=None)
    last_crawled: datetime = Field(..., le=datetime.today())
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class UpdatePageModel(BaseModel):
    """
    A set of optional updates to be made to a document in the database
    """
    url: Optional[str] = None
    text: Optional[List[str]] = None
    title: Optional[str] = None
    anchor_text: Optional[str] = None
    outgoing: Optional[List[str]] = None
    last_crawled: Optional[datetime] = None
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class PageCollectionModel(BaseModel):
    """
    A container holding a list of `PageModel` instances.

    This exists because providing a top-level array in a JSON response can be a [vulnerability](https://haacked.com/archive/2009/06/25/json-hijacking.aspx/)
    """

    pages: List[PageModel]


class QueueModel(BaseModel):
    url: str = Field(...)


class QueueCollectionModel(BaseModel):
    """
    A container holding a list of `QueueModel` instances.

    This exists because providing a top-level array in a JSON response can be a [vulnerability](https://haacked.com/archive/2009/06/25/json-hijacking.aspx/)
    """
    urls: List[QueueModel]

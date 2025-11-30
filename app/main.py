import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router
from app.api.middleware import logging_middleware
from app.core.logger import setup_logging

setup_logging(log_level="INFO", log_file="markone.log")
logger = logging.getLogger(__name__)

app = FastAPI(title="Newsletter Market Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(logging_middleware)

app.include_router(router.router, prefix="/api/v1")

# Things to extract:
# - Newsletter title
# - Author name
# - Number of words
# - Number of sections
# - Subject line (title)
# - Subject line category (e.g: Subscription, Personal Growth)
# - Number of emojis
# - Number of emojis in subject line
# - Number of words in Subject line
# - Does it address reader with a name?
# - CTAs (eg: Read more, Subscribe)
# - Number of links
# - Number of images
# - Reading time
# - Ads
# - Number of times product is mentioned
# - Overall intent
# - Overall tone (e.g: Formal, Informal, Humorous)
# - Overall Comments (Summary and intent of the newsletter)

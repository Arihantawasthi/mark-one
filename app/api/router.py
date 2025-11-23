from fastapi import APIRouter
from app.db import queries
from app.llm.agent import AnalysisResponse, LinkObject
from app.tasks.pipeline import scraping_stage


router = APIRouter(tags=["newsletter"])

search_results = [
    {
      "title": "Soccer Analytics Newsletter | Richard Whittall | Substack",
      "link": "https://socceranalytics.substack.com/",
      "snippet": "A newsletter about soccer analytics (well, about everything really). Click to read Soccer Analytics Newsletter, by Richard Whittall, a Substack publication ...",
      "position": 1
    },
    {
      "title": "Optimum Sports Consulting Newsletter | Substack",
      "link": "https://optimumsportsconsulting.substack.com/",
      "snippet": "Welcome to the NIL Newsletter by Optimum Sports Consulting - providing valuable, actionable NIL resources for athletes, administrators, agencies and...",
      "position": 2
    },
    {
      "title": "Olympics Everywhere Newsletter | Sydney Bauer | Substack",
      "link": "https://olympicseverywhere.substack.com/",
      "snippet": "The Olympics are so big they touch every aspect of a country's society; I'm here to unpack that. Click to read Olympics Everywhere Newsletter, by Sydney ...",
      "position": 3
    }
]

search_results = [
    {
        "position": 3,
        "title": "About - MacGuffin or Meaning: Entertainment Newsletter",
        "link": "https://alisechaffins.substack.com/",
    },
    {
        "position": 4,
        "title": "About - We Have Notes",
        "link": "https://wehavenotes.substack.com/",
    },
    {
        "position": 5,
        "title": "Recommended by Aurelie Chazal - The Inclusive Screen",
        "link": "https://theinclusivescreen.substack.com/",
    },
    {
        "position": 6,
        "title": "TheFUSE — A Wichita Falls Arts & Entertainment newsletter",
        "link": "https://fallstownfuse.substack.com/",
    }
]

@router.get("/")
def health_check():
    return { "status": "ok", "service": "scrapper" }

@router.get("/trigger-analysis")
def trigger_analysis():
    total_newsletters = len(search_results)
    niche = "entertainment"
    search_terms = [ "top 10 newsletters on sports", "best sports newsletters", "popular sports newsletters" ]
    notion_doc_url = "https://www.notion.so/your-notion-doc-url"
    analysis_run_id = queries.insert_analysis_run(
        notion_doc_url,
        niche,
        search_terms,
        total_newsletters,
        0,
        "initiated"
    )

    scraping_stage.delay(analysis_run_id, search_results)

    return { "status": "ok", "message": "Analysis triggered" }

@router.get("/test-analysis-insert")
def test_analysis_insert():
    analysis = AnalysisResponse(
        title="Football and tail risks",
        subtitle="Let's not forget the lessons here",
        author="",
        word_count=1035,
        image_count=1,
        like_count=5,
        comment_count=12,
        section_count=10,
        emoji_count=0,
        title_emoji_count=0,
        subtitle_emoji_count=0,
        title_word_count=4,
        subtitle_word_count=6,
        addressed_user_by_name=False,
        reading_time_minutes=4,
        product_mention_count=0,
        ctas=[
            LinkObject(
                type="reference",
                text="normal distribution",
                url="https://www.investopedia.com/terms/n/normaldistribution.asp"
            ),
            LinkObject(
                type="reference",
                text="Investopedia",
                url="https://www.investopedia.com/terms/t/tailrisk.asp"
            ),
            LinkObject(
                type="reference",
                text="BBC story on the underground caves inhabited during WW2",
                url="https://www.bbc.com/news/magazine-34139311"
            ),
        ],
        ads=[],
        overall_summary=(
            "The newsletter discusses the concept of tail risks in football, emphasizing "
                "the need for better preparedness in the face of unexpected events, drawing "
                "parallels with historical crises and urging clubs to collaborate for solutions."
        ),
        overall_intent="to inform",
        overall_tone="thoughtful"
    )

    queries.insert_issue_analysis(1, analysis)
    return { "status": "ok", "message": "Test analysis inserted" }

@router.get("/get-analysis")
def get_analysis():
    analysis = queries.get_issue_analysis()
    return { "status": "ok", "message": "Analysis exported to analysis_export.csv", "data": analysis }

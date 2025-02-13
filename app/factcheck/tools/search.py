from duckduckgo_search import DDGS

from app import config


async def search_claim_check(claim):
    try:
        request = DDGS().text(keywords=claim, region=config.DDG_REGION, safesearch="off", backend="auto", max_results=1)
        claim_reviews = []
        if request:  #
            for result in request:
                claim_reviews.append({
                    'title': result['title'],
                    'href': result['href'],
                    'body': result['body'],
                    'claim': claim,
                })

        return claim_reviews

    # --------------------------------

    except Exception as e:
        print(f"Oшибка : {e}")

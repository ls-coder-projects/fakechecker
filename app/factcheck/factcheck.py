import asyncio

from app.factcheck.tools.search import search_claim_check


# проверка отдельно одного факта из мультиплай функции
async def verify_single_claim(claim):
    review_of_claim = await search_claim_check(claim)

    return review_of_claim


async def verify_multiple_claims(claims, concurrency_limit: int = 5):
    semaphore = asyncio.Semaphore(concurrency_limit)
    results = []

    async def sem_verify_claim(claim):
        async with semaphore:
            # Добавление claim_reviews в result
            result = await verify_single_claim(claim)
            results.extend(result)

    tasks = [sem_verify_claim(claim) for claim in claims]
    await asyncio.gather(*tasks, return_exceptions=False)

    return results


async def process_fact_check_session(claims):
    verification_results = await verify_multiple_claims(claims)

    return verification_results

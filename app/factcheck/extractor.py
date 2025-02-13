from concurrent.futures import ThreadPoolExecutor

from mistralai import Mistral

from app import config


def split_user_input(text):
    paragraphs = text.split('\n')
    paragraphs = [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]
    return paragraphs


def summarize(text_array):
    def create_chunks(paragraphs):
        chunks = []
        chunk = ''
        for paragraph in paragraphs:
            if len(chunk) + len(paragraph) < config.CHUNK_SIZE:
                chunk += paragraph + ' '
            else:
                chunks.append(chunk.strip())
                chunk = paragraph + ' '
        if chunk:
            chunks.append(chunk.strip())
        return chunks

    try:
        text_chunks = create_chunks(text_array)
        text_chunks = [chunk for chunk in text_chunks if chunk]

        summaries = []

        system_messages = [
            {"role": "system",
             "content": "You are an expert in creating summaries that capture the main points and key details."},
            {"role": "system",
             "content": f"You will show the bulleted list content without translate any technical terms."},
            {"role": "system", "content": f"You will print all the content in {config.LANGUAGE_PROMPT}."},
        ]

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(call_AI_api,
                                       f"Summary keypoints (up to 1) for the following text, ensuring each point is independent and clear without pronouns or references and does not exceed 100 characters:\n{chunk}",
                                       system_messages) for chunk in text_chunks]
            for future in futures:
                result = future.result()
                if result:
                    summaries.append(result)
        return summaries
    # Возвращает: List[Claim]: Список извлеченных экземпляров Claim.

    except Exception as e:
        print(f"Error: {e}")
        return "Unknown error! Please contact the developer."


def call_AI_api(prompt, additional_messages=[]):
    try:
        client = Mistral(api_key=config.MISTRAL_API_KEY)
        response = client.chat.complete(
            model=config.MISTRAL_MODEL,
            messages=additional_messages + [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],

        )
        message = response.choices[0].message.content.strip()
        message = message.lstrip('-').strip()
        message = message.lstrip('•').strip()

        return message

    except Exception as e:
        print(f"Error: {e}")
        return ""

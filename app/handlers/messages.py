import re
from typing import List

from aiogram import F, Router, flags
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart
from aiogram.types import LinkPreviewOptions, Message

from app.factcheck.extractor import split_user_input, summarize
from app.factcheck.factcheck import process_fact_check_session
from app.utils.crawling import retrieve_yt_transcript_from_url, scrape_text_from_url
from app.utils.message_utils import messages

router = Router()


@router.message(CommandStart())
async def process_start_command(message: Message) -> None:
    await message.answer(messages['start_command']['welcome_text'], parse_mode="HTML")


@router.message(Command(commands="info"))
@flags.chat_action("typing")
async def process_info_command(message: Message) -> None:
    await message.answer(messages['info_command']['info_text'], parse_mode="HTML")


# другие команды
@flags.chat_action("typing")
@router.message(Command(commands=re.compile(r".*")))
async def process_other_commands(message: Message) -> None:
    await message.answer(messages['other_commands']['default_response'])


# Разделение текста на части для вывод информации
# Максимальная длина чанка 2000
def split_message(text: str, max_length: int = 2000) -> List[str]:
    # If text is shorter than max_length, return it as is
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ''

    # Разделяем текст на строки для сохранения форматирования
    lines = text.split('\n')

    for line in lines:
        # Если добавление этой строки превысит max_length
        if len(current_chunk + line + '\n') > max_length:
            # Если текущий фрагмент не пуст, добавляем его в chunks
            if current_chunk:
                chunks.append(current_chunk.rstrip())
                current_chunk = ''

            # Если одна строка длиннее max_length, разбиваем её
            if len(line) > max_length:
                words = line.split(' ')
                for word in words:
                    if len(current_chunk + word + ' ') > max_length:
                        chunks.append(current_chunk.rstrip())
                        current_chunk = word + ' '
                    else:
                        current_chunk += word + ' '
            else:
                current_chunk = line + '\n'
        else:
            current_chunk += line + '\n'

    # Добавляем последний фрагмент, если он не пуст
    if current_chunk:
        chunks.append(current_chunk.rstrip())

    return chunks


def process_user_input(text: str):
    youtube_pattern = re.compile(r"https?://(www\.|m\.)?(youtube\.com|youtu\.be)/")
    url_pattern = re.compile(r"https?://")

    if youtube_pattern.match(str(text)):
        text_array = retrieve_yt_transcript_from_url(str(text))

    elif url_pattern.match(str(text)):
        text_array = scrape_text_from_url(str(text))
    else:
        text_array = split_user_input(str(text))
        print(text_array)

    return text_array


@router.message(F.text | F.caption)
@flags.chat_action("typing")
async def message(message: Message) -> None:
    try:
        text = message.caption or message.text or ""
        text_array = process_user_input(text)

        try:
            claims = summarize(text_array)
        except Exception as e:
            await message.reply(
                messages['errors']['extraction_error'],
                parse_mode="HTML"
            )
            return

        # Бот отправляет пользователю сообщение, которое указывает на то, что утверждений не найдено. 
        if not claims:
            await message.reply(
                messages['fact_check']['no_claims'],
                parse_mode="HTML",
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
            return

        # Отправка промежуточного сообщения с извлеченными утверждениями
        claims_message = (
            messages['fact_check']['claims_found_single'] if len(claims) == 1
            else messages['fact_check']['claims_found_multiple']
        )

        # Этот код формирует сообщение для пользователя, перечисляя извлеченные утверждения. Если утверждений несколько, они нумеруются; если одно — просто выделяется жирным.
        for idx, claim in enumerate(claims, start=1):
            if len(claims) > 1:
                claims_message += f"{idx}. <b>{claim}</b>\n"
            else:
                claims_message += f"<b>{claim}</b>\n"

        claims_message += messages['fact_check']['checking_continue']

        await message.reply(claims_message, parse_mode="HTML",
                            link_preview_options=LinkPreviewOptions(is_disabled=True))

        # Продолжение процесса проверки фактов
        verification_results = await process_fact_check_session(claims)

        # Подготовка ответа на основе результатов проверки
        response_lines = [messages['fact_check']['results_header']]

        total_claims = len(claims)
        claims = list(set(claims))
        for idx, claim in enumerate(claims, start=1):
            # Добавление утверждения с номером только если есть несколько утверждений
            if total_claims > 1:
                response_lines.append(f"\n{idx}. <b>{claim}</b>\n")
            else:
                response_lines.append(f"\n<b>{claim}</b>\n")

            # Фильтруем результаты проверки только для текущего утверждения
            current_claim_verifications = [v for v in verification_results if v['claim'] == claim]

            for verification in current_claim_verifications:
                try:
                    source = verification['href']
                except KeyError:
                    source = messages['fact_check']['unknown_source']

                response_lines.append(f"{messages['fact_check']['source_label']} <a href='{source}'>{source}</a>")
                response_lines.append(f"<blockquote>{verification['body']}</blockquote>")

        response = "\n".join(response_lines)

        # Разделение ответа, если он слишком длинный
        message_parts = split_message(response)

        # Отправка каждой части отдельно
        for part in message_parts:
            await message.reply(
                part,
                parse_mode="HTML",
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )

        # --------------------ошибки-------------------
    except TelegramAPIError as e:
        try:
            await message.reply(
                messages['errors']['telegram_error'],
                parse_mode="HTML"
            )
            print(f"Ошибка при отправке сообщения: {e}")
        except TelegramAPIError:
            print('Не удалось отправить сообщение об ошибке пользователю')

    except Exception as e:
        try:
            await message.reply(
                messages['errors']['unexpected_error'],
                parse_mode="HTML"
            )
            print(f"Ошибка при отправке сообщения: {e}")


        except TelegramAPIError:
            print('Не удалось отправить сообщение об ошибке пользователю')


"""
Отче наш, сущий на небесах! Да святится имя Твое; да приидет Царствие Твое; да будет воля Твоя и на земле, как на небе; хлеб наш насущный дай нам на сей день; и прости нам долги наши, как и мы прощаем должникам нашим; и не введи нас в искушение, но избавь нас от лукавого. Ибо Твое есть Царство и сила и слава во веки.
"""

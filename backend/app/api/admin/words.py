"""Profanity and reserved nickname lists (TZ 8.1, 8.12)."""

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.admin.audit import audit
from app.admin.deps import AdminOnly
from app.admin.schemas import WordIn, WordOut
from app.deps import SessionDep
from app.models import BannedWord

router = APIRouter(prefix="/words", tags=["admin-users"])


@router.get("")
async def list_words(admin: AdminOnly, session: SessionDep) -> list[WordOut]:
    rows = await session.scalars(select(BannedWord).order_by(BannedWord.kind, BannedWord.word))
    return [WordOut.model_validate(w) for w in rows.all()]


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_word(body: WordIn, admin: AdminOnly, session: SessionDep) -> WordOut:
    """Applies to new nicknames right away; existing ones are handled through reports."""
    word = BannedWord(word=body.word, kind=body.kind)
    session.add(word)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "word_exists") from exc
    audit(session, admin, "word.add", "word", word.id, word=word.word, kind=word.kind.value)
    await session.commit()
    return WordOut.model_validate(word)


@router.delete("/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_word(word_id: int, admin: AdminOnly, session: SessionDep) -> Response:
    word = await session.get(BannedWord, word_id)
    if word is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "word_not_found")
    audit(session, admin, "word.delete", "word", word.id, word=word.word, kind=word.kind.value)
    await session.delete(word)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

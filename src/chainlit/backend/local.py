from typing import Optional, Dict
import uuid
import json
import os

import asyncio
import aiofiles
from chainlit.backend.base import PaginatedResponse, PageInfo

from .base import BaseBackend

from chainlit.logger import logger
from chainlit.config import config
from chainlit.element import mime_to_ext, Pyplot, Text, Image
from chainlit.message import Message, ErrorMessage

class LocalBackend(BaseBackend):
    conversation_id: Optional[str] = None
    lock: asyncio.Lock
    task_type: Optional[str] = None

    def __init__(self):
        self.lock = asyncio.Lock()
        self.headers = {
            "content-type": "application/json",
        }

    def before_write(self, variables: Dict):
        if "forIds" in variables:
            # Sqlite doesn't support list of primitives, so we need to serialize it.
            variables["forIds"] = json.dumps(variables["forIds"])

        if "tempId" in variables:
            del variables["tempId"]

    def after_read(self, variables: Dict):
        pass

    async def is_project_member(self):
        return True

    async def get_member_role(self):
        return "OWNER"

    async def get_project_members(self):
        return []

    async def get_conversation_id(self):
        self.conversation_id = await self.create_conversation()

        return self.conversation_id

    async def create_conversation(self):
        from prisma.models import Conversation

        # If we run multiple send concurrently, we need to make sure we don't create multiple conversations.
        async with self.lock:
            if self.conversation_id:
                return self.conversation_id

            res = await Conversation.prisma().create(data={})

            return res.id

    async def delete_conversation(self, conversation_id):
        from prisma.models import Conversation

        await Conversation.prisma().delete(where={"id": conversation_id})

        return True

    async def get_conversation(self, conversation_id: int):
        from prisma.models import Conversation

        c = await Conversation.prisma().find_unique_or_raise(
            where={"id": conversation_id}, include={"messages": True, "elements": True}
        )

        for e in c.elements:
            if e.forIds:
                e.forIds = json.loads(e.forIds)

        return json.loads(c.json())

    async def get_conversations(self, pagination, filter):
        from prisma.models import Conversation

        some_messages = {}

        if filter.feedback is not None:
            some_messages["humanFeedback"] = filter.feedback

        if filter.search is not None:
            some_messages["content"] = {"contains": filter.search or None}

        if pagination.cursor:
            cursor = {"id": pagination.cursor}
        else:
            cursor = None

        conversations = await Conversation.prisma().find_many(
            take=pagination.first,
            skip=1 if pagination.cursor else None,
            cursor=cursor,
            include={
                "messages": {
                    "take": 1,
                    "where": {
                        "authorIsUser": True,
                    },
                    "orderBy": [
                        {
                            "createdAt": "asc",
                        }
                    ],
                }
            },
            where={"messages": {"some": some_messages}},
            order={
                "createdAt": "desc",
            },
        )

        has_more = len(conversations) == pagination.first

        if has_more:
            end_cursor = conversations[-1].id
        else:
            end_cursor = None

        conversations = [json.loads(c.json()) for c in conversations]

        return PaginatedResponse(
            pageInfo=PageInfo(hasNextPage=has_more, endCursor=end_cursor),
            data=conversations,
        )

    async def create_message(self, variables):
        from prisma.models import Message

        c_id = await self.get_conversation_id()

        if not c_id:
            logger.warning("Missing conversation ID, could not persist the message.")
            return None

        variables = variables.copy()

        variables["conversationId"] = c_id

        self.before_write(variables)

        res = await Message.prisma().create(data=variables)
        return res.id

    async def get_message(self, message_id):
        from prisma.models import Message

        res = await Message.prisma().find_first(where={"id": message_id})
        res = res.dict()
        self.after_read(res)
        return res

    async def update_message(self, message_id, variables):
        from prisma.models import Message

        variables = variables.copy()

        self.before_write(variables)

        await Message.prisma().update(data=variables, where={"id": message_id})

        return True

    async def delete_message(self, message_id):
        from prisma.models import Message

        await Message.prisma().delete(where={"id": message_id})

        return True

    async def upsert_element(
        self,
        variables,
    ):
        from prisma.models import Element

        c_id = await self.get_conversation_id()

        if not c_id:
            logger.warning("Missing conversation ID, could not persist the element.")
            return None

        variables["conversationId"] = c_id

        self.before_write(variables)

        if "id" in variables:
            res = await Element.prisma().update(
                data=variables, where={"id": variables.get("id")}
            )
        else:
            res = await Element.prisma().create(data=variables)

        return res.dict()

    async def get_element(
        self,
        conversation_id,
        element_id,
    ):
        from prisma.models import Element

        res = await Element.prisma().find_unique_or_raise(where={"id": element_id})
        return json.loads(res.json())

    async def upload_element(self, content: bytes, mime: str):
        c_id = await self.get_conversation_id()

        if not c_id:
            logger.warning("Missing conversation ID, could not persist the message.")
            return None

        file_ext = mime_to_ext.get(mime, "bin")
        file_name = f"{uuid.uuid4()}.{file_ext}"

        sub_path = os.path.join(str(c_id), file_name)
        full_path = os.path.join(config.project.local_fs_path, sub_path)

        if not os.path.exists(os.path.dirname(full_path)):
            os.makedirs(os.path.dirname(full_path))

        async with aiofiles.open(full_path, "wb") as out:
            await out.write(content)
            await out.flush()

            url = f"/files/{sub_path}"
            return url

    async def set_human_feedback(self, message_id, feedback):
        from prisma.models import Message

        await Message.prisma().update(
            where={"id": message_id},
            data={
                "humanFeedback": feedback,
            },
        )

        return True

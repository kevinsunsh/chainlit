from typing import Dict, Any, Optional
import uuid

import asyncio
import aiohttp
from python_graphql_client import GraphqlClient

from .base import BaseBackend, PaginatedResponse, PageInfo

from chainlit.logger import logger
from chainlit.config import config


class CloudBackend(BaseBackend):
    conversation_id: Optional[str] = None
    lock: asyncio.Lock

    def __init__(self, project_id: str, access_token: str):
        self.lock = asyncio.Lock()
        self.project_id = project_id
        self.headers = {
            "Authorization": access_token,
            "content-type": "application/json",
        }
        # graphql_endpoint = f"{config.chainlit_server}/api/graphql"
        # self.graphql_client = GraphqlClient(
        #    endpoint=graphql_endpoint, headers=self.headers
        # )

        # def query(self, query: str, variables: Dict[str, Any] = {}) -> Dict[str, Any]:
        """
        Execute a GraphQL query.

        :param query: The GraphQL query string.
        :param variables: A dictionary of variables for the query.
        :return: The response data as a dictionary.
        """
        # return self.graphql_client.execute_async(query=query, variables=variables)

    def check_for_errors(self, response: Dict[str, Any], raise_error: bool = False):
        if "errors" in response:
            if raise_error:
                raise Exception(response["errors"][0])
            logger.error(response["errors"][0])
            return True
        return False

        # def mutation(self, mutation: str, variables: Dict[str, Any] = {}) -> Dict[str, Any]:
        """
        Execute a GraphQL mutation.

        :param mutation: The GraphQL mutation string.
        :param variables: A dictionary of variables for the mutation.
        :return: The response data as a dictionary.
        """

    #     return self.graphql_client.execute_async(query=mutation, variables=variables)

    async def get_member_role(
        self,
    ):
        return "OWNER"
        # data = {"projectId": self.project_id}
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(
        #         f"{config.chainlit_server}/api/role",
        #         json=data,
        #         headers=self.headers,
        #     ) as r:
        #         if not r.ok:
        #             reason = await r.text()
        #             logger.error(f"Failed to get user role. {r.status}: {reason}")
        #             return False
        #         json = await r.json()
        #         return json.get("role", "ANONYMOUS")

    async def is_project_member(self) -> bool:
        role = await self.get_member_role()
        return role != "ANONYMOUS"

    async def get_project_members(self):
        # query = """query ($projectId: String!) {
        #             projectMembers(projectId: $projectId) {
        #             edges {
        #                 cursor
        #                 node {
        #                 role
        #                 user {
        #                     email
        #                     name
        #                 }
        #                 }
        #             }
        #             }
        #         }"""
        # variables = {"projectId": self.project_id}
        # res = await self.query(query, variables)
        # self.check_for_errors(res, raise_error=True)

        members = []

        # for edge in res["data"]["projectMembers"]["edges"]:
        # node = edge["node"]
        role = "OWNER"  # node["role"]
        name = "kevin"  # node["user"]["name"]
        email = "sunzhipeng8@gmail.com"  # node["user"]["email"]
        members.append({"role": role, "name": name, "email": email})

        return members

    async def create_conversation(self) -> int:
        from prisma.models import Conversation

        # If we run multiple send concurrently, we need to make sure we don't create multiple conversations.
        async with self.lock:
            if self.conversation_id:
                return self.conversation_id

            res = await Conversation.prisma().create(data={})

            return res.id

    async def get_conversation_id(self):
        self.conversation_id = await self.create_conversation()

        return self.conversation_id

    async def delete_conversation(self, conversation_id: int):
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

    async def set_human_feedback(self, message_id, feedback):
        mutation = """mutation ($messageId: ID!, $humanFeedback: Int!) {
                        setHumanFeedback(messageId: $messageId, humanFeedback: $humanFeedback) {
                            id
                            humanFeedback
                    }
                }"""
        variables = {"messageId": message_id, "humanFeedback": feedback}
        res = await self.mutation(mutation, variables)
        self.check_for_errors(res, raise_error=True)

        return True

    async def get_message(self):
        from prisma.models import Message

        res = await Message.prisma().find_first(where={"id": message_id})
        res = res.dict()
        self.after_read(res)
        return res

    async def create_message(self, variables: Dict[str, Any]) -> int:
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

    async def update_message(self, message_id: int, variables: Dict[str, Any]) -> bool:
        from prisma.models import Message

        variables = variables.copy()

        self.before_write(variables)

        await Message.prisma().update(data=variables, where={"id": message_id})

        return True

    async def delete_message(self, message_id: int) -> bool:
        mutation = """
        mutation ($messageId: ID!) {
            deleteMessage(messageId: $messageId) {
                id
            }
        }
        """
        res = await self.mutation(mutation, {"messageId": message_id})

        if self.check_for_errors(res):
            logger.warning("Could not delete message.")
            return False

        return True

    async def get_element(self, conversation_id, element_id):
        query = """query (
        $conversationId: ID!
        $id: ID!
    ) {
        element(
        conversationId: $conversationId,
        id: $id
        ) {
        id
        conversationId
        type
        name
        url
        display
        language
        size
        forIds
        }
    }"""

        variables = {
            "conversationId": conversation_id,
            "id": element_id,
        }
        res = await self.query(query, variables)
        self.check_for_errors(res, raise_error=True)

        return res["data"]["element"]

    async def upsert_element(self, variables):
        c_id = await self.get_conversation_id()

        if not c_id:
            logger.warning("Missing conversation ID, could not persist the element.")
            return None

        if "id" in variables:
            mutation_name = "updateElement"
            mutation = """
            mutation ($conversationId: ID!, $id: ID!, $forIds: [String!]!) {
                updateElement(conversationId: $conversationId, id: $id, forIds: $forIds) {
                    id,
                }
            }
            """
            variables["conversationId"] = c_id
            res = await self.mutation(mutation, variables)
        else:
            mutation_name = "createElement"
            mutation = """
            mutation ($conversationId: ID!, $type: String!, $url: String!, $name: String!, $display: String!, $forIds: [String!]!, $size: String, $language: String) {
                createElement(conversationId: $conversationId, type: $type, url: $url, name: $name, display: $display, size: $size, language: $language, forIds: $forIds) {
                    id,
                    type,
                    url,
                    name,
                    display,
                    size,
                    language,
                    forIds
                }
            }
            """
            variables["conversationId"] = c_id
            res = await self.mutation(mutation, variables)

        if self.check_for_errors(res):
            logger.warning("Could not persist element.")
            return None

        return res["data"][mutation_name]

    async def upload_element(self, content: bytes, mime: str) -> str:
        id = f"{uuid.uuid4()}"
        body = {"projectId": self.project_id, "fileName": id, "contentType": mime}

        path = f"/api/upload/file"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config.chainlit_server}{path}",
                json=body,
                headers=self.headers,
            ) as r:
                if not r.ok:
                    reason = await r.text()
                    logger.error(f"Failed to upload file: {reason}")
                    return ""
                json_res = await r.json()

        upload_details = json_res["post"]
        permanent_url = json_res["permanentUrl"]

        form_data = aiohttp.FormData()

        # Add fields to the form_data
        for field_name, field_value in upload_details["fields"].items():
            form_data.add_field(field_name, field_value)

        # Add file to the form_data
        form_data.add_field("file", content, content_type="multipart/form-data")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                upload_details["url"],
                data=form_data,
            ) as upload_response:
                if not upload_response.ok:
                    reason = await upload_response.text()
                    logger.error(f"Failed to upload file: {reason}")
                    return ""

                url = f'{upload_details["url"]}/{upload_details["fields"]["key"]}'
                return permanent_url

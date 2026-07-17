import itertools
import json
import os
from typing import List
from bedrock_agentcore.memory import MemoryClient

class MemoryUtils:
    sessionId:str = None
    actorId:str = None

    def __init__(self, sessionId:str, actorId:str):
        self.sessionId = sessionId
        self.actorId = actorId

    def saveMemory(self, userPrompt:str, assistantResponse:str):
        memoryId = os.getenv("MEMORY_ID")
        if memoryId is None or memoryId == "":
            return

        userPrompt = userPrompt[:9000]
        assistantResponse = assistantResponse[:9000]
        
        payload = [
            [userPrompt, "user"],
            [assistantResponse, "assistant"]
        ]

        params = {
            "memory_id": memoryId,
            "actor_id": self.actorId,
            "session_id": self.sessionId,
            "messages": payload
        }
        MemoryClient().create_event(**params)

    def loadShortTermMemory(self, count:int=5):
        memoryId = os.getenv("MEMORY_ID")
        if memoryId is None or memoryId == "":
            return

        params = {
            "memory_id": memoryId,
            "actor_id": self.actorId,
            "session_id": self.sessionId,
            "k": count
        }
        turns = MemoryClient().get_last_k_turns(**params)
        flattened_list = list(itertools.chain.from_iterable(reversed(turns)))
        response = []
        for item in flattened_list:
            response.append(
                {
                    "role": item['role'].lower(),
                    "content":  item['content']['text']
                }
            )
        return response

    def extractSummary(self, query:str="Conversation Summary"):
        memoryId = os.getenv("MEMORY_ID")
        if memoryId is None or memoryId == "":
            return

        memoryStrategyId = os.getenv("MEMORY_SUMMARY_STRATEGY_ID")
        if memoryStrategyId is None or memoryStrategyId == "":
            return

        namespace = "/strategies/{memoryStrategyId}/actors/{actorId}/sessions/{sessionId}".format(memoryStrategyId=memoryStrategyId, actorId=self.actorId, sessionId=self.sessionId)
        params = {
            "memory_id": memoryId,
            "namespace": namespace,
            "query": query,
            "actor_id": self.actorId
        }
        memory_records = MemoryClient().retrieve_memories(**params)
        
        summary:List[str] = []
        for item in memory_records:
            if item['content'] and item['content']['text']:
                summary.append(item['content']['text'].replace("\n", " "))
        responseStr = "\n".join(summary)
        if responseStr == "":
            return

        return {
            "role": "user",
            "content":  "Summary of Conversation So Far: " + responseStr
        }

        

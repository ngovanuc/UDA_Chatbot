import asyncio
import os
from typing import List, Optional, Union

import numpy as np
from infinity_emb import AsyncEmbeddingEngine, EngineArgs
from uac.configs.config import Config


class InfinityEmbedding:
    def __init__(self, config: Optional[Config] = None, device: str = "cuda"):
        self.config = config or Config()
        self.model_name_or_path = (
            os.path.join(self.config.embedding_model_cache_dir, self.config.embedding_model_name)
            if os.path.exists(
                os.path.join(
                    self.config.embedding_model_cache_dir, self.config.embedding_model_name
                )
            )
            else self.config.embedding_model_name
        )

        self.embeder = AsyncEmbeddingEngine.from_args(
            EngineArgs(
                model_name_or_path=self.model_name_or_path,
                trust_remote_code=True,
                engine="torch",
                bettertransformer=False,
                embedding_dtype="float32",
                dtype="auto",
                device=device,
                model_warmup=False,
            )
        )

    async def aembed(self, sentences: Union[List[str], str]):
        async with self.embeder:
            if isinstance(sentences, str):
                embeddings, usage = await self.embeder.embed(sentences=[sentences])
                return np.array(embeddings[0])
            else:
                embeddings, usage = await self.embeder.embed(sentences=sentences)
                return np.array(embeddings)

    def embed(self, sentences: Union[List[str], str]):
        return asyncio.run(self.aembed(sentences))

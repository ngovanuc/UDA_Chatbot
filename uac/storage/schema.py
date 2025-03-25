from pymilvus import CollectionSchema, DataType, FieldSchema
from uac.configs.config import Config


class DocumentAdmissionSchema(CollectionSchema):
    """
    A schema for the history_chat collection in the Milvus database.

    Args:
        config (Config): Configuration object containing collection settings.

    Attributes:
        collection_name (str): Name of the collection.
        fields (list): List of FieldSchema objects defining the collection structure.
        description (str): Description of the collection.
        enable_dynamic_field (bool): Flag to enable or disable dynamic fields.
    """

    def __init__(self, config: Config) -> None:
        super().__init__(
            fields=[
                FieldSchema(
                    name="id",
                    dtype=DataType.VARCHAR,
                    is_primary=True,
                    description="The ID of the document.",
                    max_length=100,
                    auto_id=True,
                ),
                FieldSchema(
                    name="embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=config.vector_dim,
                    description="The embedding of the document.",
                ),
                FieldSchema(
                    name="metadata",
                    dtype=DataType.JSON,
                    description="metadata of the document.",
                ),
            ],
            description="A collection of documents.",
            enable_dynamic_field=False,
        )

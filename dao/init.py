from elasticsearch import Elasticsearch
from typing import Optional
from define import ELASTICSEARCH_URL
import os

ELASTIC_USERNAME = os.getenv("ELASTIC_USERNAME", "elastic")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "")

_es_client: Optional[Elasticsearch] = None


def get_es_client() -> Elasticsearch:
    """get Elasticsearch client (singleton pattern)"""
    global _es_client
    if _es_client is None:
        _es_client = Elasticsearch(
            hosts=[ELASTICSEARCH_URL],
            http_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD),
            scheme="http",
            port=9200,
        )
    return _es_client

from hashlib import md5
from pathlib import Path
from typing import Optional, List, Tuple

from debater_python_api.api.clients.pro_con_client import ProConClient
from debater_python_api.api.debater_api import DebaterApi
from nltk import sent_tokenize

from grimjack.model import Query
from grimjack.model.arguments import ArgumentRankedDocument
from grimjack.model.quality import (
    ArgumentQualitySentence, ArgumentQualityRankedDocument
)
from grimjack.model.stance import ArgumentStanceSentence
from grimjack.utils.nltk import download_nltk_dependencies


def get_quality_scores(
        query: Query,
        document: ArgumentRankedDocument,
        api_token: str,
        cache_path: Optional[Path] = None
) -> List[ArgumentQualitySentence]:
    if cache_path is not None:
        cache_path.mkdir(parents=True, exist_ok=True)

    content_hash: str = md5(document.content.encode()).hexdigest()
    title_hash: str = md5(query.title.encode()).hexdigest()
    cache_file = (
        cache_path / f"{query.id}-{document.id}-"
                     f"{title_hash}-{content_hash}.json"
        if cache_path is not None
        else None
    )

    # Check if the API response is found in the cache.
    if cache_file is not None and cache_file.exists() and cache_file.is_file():
        with cache_file.open("r") as file:
            return ArgumentQualitySentence.schema().loads(
                file.read(),
                many=True
            )

    quality = _fetch_quality_scores(query, document, api_token)

    # Cache the API response.
    if cache_file is not None:
        cache_file.parent.mkdir(exist_ok=True)
        with cache_file.open("w") as file:
            file.write(
                ArgumentQualitySentence.schema().dumps(
                    quality,
                    many=True
                )
            )

    return quality


def _fetch_quality_scores(
        query: Query,
        document: ArgumentRankedDocument,
        api_token: str
) -> List[ArgumentQualitySentence]:
    download_nltk_dependencies("punkt")

    debater_api = DebaterApi(api_token)
    argument_quality_client = debater_api.get_argument_quality_client()

    topic = query.title
    sentences = sent_tokenize(document.content)

    sentence_topic_pairs = [
        {
            "sentence": sentence,
            "topic": topic,
        }
        for sentence in sentences
    ]

    scores = argument_quality_client.run(sentence_topic_pairs)

    return [
        ArgumentQualitySentence(sentence, score)
        for sentence, score in zip(sentences, scores)
    ]


def get_stance_scores(
        query: Query,
        document: ArgumentQualityRankedDocument,
        api_token: str,
        cache_path: Optional[Path] = None
) -> List[ArgumentStanceSentence]:
    if cache_path is not None:
        cache_path.mkdir(parents=True, exist_ok=True)

    content_hash: str = md5(document.content.encode()).hexdigest()
    title_hash: str = md5(query.title.encode()).hexdigest()
    cache_file = (
        cache_path / f"{query.id}-{document.id}-"
                     f"{title_hash}-{content_hash}.json"
        if cache_path is not None
        else None
    )

    # Check if the API response is found in the cache.
    if cache_file is not None and cache_file.exists() and cache_file.is_file():
        with cache_file.open("r") as file:
            return ArgumentStanceSentence.schema().loads(
                file.read(),
                many=True
            )

    stance = _fetch_stance_scores(query, document, api_token)

    # Cache the API response.
    if cache_file is not None:
        cache_file.parent.mkdir(exist_ok=True)
        with cache_file.open("w") as file:
            file.write(
                ArgumentStanceSentence.schema().dumps(
                    stance,
                    many=True
                )
            )

    return stance


def _claim(comparative_object: str) -> str:
    return f"{comparative_object} is the best"


def _stance(
        pro_con_client: ProConClient,
        comparative_objects: Tuple[str, str],
        sentence: str
) -> float:
    object_a, object_b = comparative_objects
    stance_a, stance_b = pro_con_client.run([
        {
            "sentence": sentence,
            "topic": _claim(object_a),
        },
        {
            "sentence": sentence,
            "topic": _claim(object_b),
        },
    ])
    return stance_a - stance_b


def _fetch_stance_scores(
        query: Query,
        document: ArgumentQualityRankedDocument,
        api_token: str
) -> List[ArgumentStanceSentence]:
    download_nltk_dependencies("punkt")
    sentences = sent_tokenize(document.content)

    if query.comparative_objects is None:
        return [ArgumentStanceSentence(sentence, 0) for sentence in sentences]

    debater_api = DebaterApi(api_token)
    pro_con_client = debater_api.get_pro_con_client()

    return [
        ArgumentStanceSentence(
            sentence,
            _stance(pro_con_client, query.comparative_objects, sentence)
        )
        for sentence in sentences
    ]

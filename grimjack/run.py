from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Optional, Union

from grimjack.constants import DEFAULT_DOCUMENTS_ZIP_URL, \
    DEFAULT_TOPICS_ZIP_URL, DEFAULT_TOPICS_FILE_PATH, \
    DEFAULT_HUGGINGFACE_API_TOKEN_PATH
from grimjack.pipeline import Pipeline, Stemmer, QueryExpansion

_STEMMERS = {
    "porter": Stemmer.PORTER,
    "p": Stemmer.PORTER,
    "krovetz": Stemmer.KROVETZ,
    "k": Stemmer.KROVETZ,
}

_QUERY_EXPANSIONS = {
    "twitter-25-comparative-synonyms": QueryExpansion.TWITTER_25_COMPARATIVE_SYNONYMS,
    "twitter-25": QueryExpansion.TWITTER_25_COMPARATIVE_SYNONYMS,
    "wiki-gigaword-100-comparative-synonyms": QueryExpansion.WIKI_GIGAWORD_100_COMPARATIVE_SYNONYMS,
    "wiki-gigaword-100": QueryExpansion.WIKI_GIGAWORD_100_COMPARATIVE_SYNONYMS,
    "t0-comparative-synonyms": QueryExpansion.T0_COMPARATIVE_SYNONYMS,
    "t0": QueryExpansion.T0_COMPARATIVE_SYNONYMS,
}


def _prepare_parser(parser: ArgumentParser) -> ArgumentParser:
    parser.add_argument(
        "--documents-zip-url", "--documents-url", "-d",
        dest="documents_zip_url",
        type=str,
        default=DEFAULT_DOCUMENTS_ZIP_URL,
    )
    parser.add_argument(
        "--topics-zip-url", "--topics-url", "-t",
        dest="topics_zip_url",
        type=str,
        default=DEFAULT_TOPICS_ZIP_URL,
    )
    parser.add_argument(
        "--topics-file-path", "--topics-path",
        dest="topics_file_path",
        type=str,
        default=DEFAULT_TOPICS_FILE_PATH,
    )
    parser.add_argument(
        "--stopwords",
        dest="stopwords_file",
        type=Path,
        required=False,
    )
    parser.add_argument(
        "--no-stopwords",
        dest="stopwords_file",
        action="store_const",
        const=None
    )
    parser.add_argument(
        "--stemmer",
        dest="stemmer",
        type=str,
        choices=_STEMMERS.keys(),
        default="porter",
    )
    parser.add_argument(
        "--no-stemmer",
        dest="stemmer",
        action="store_const",
        const=None
    )
    parser.add_argument(
        "--language", "-l",
        dest="language",
        type=str,
        default="en",
    )
    parser.add_argument(
        "--query-expansion",
        dest="query_expansion",
        type=str,
        choices=_QUERY_EXPANSIONS.keys(),
        default=None,
    )
    parser.add_argument(
        "--no-query-expansion",
        dest="query_expansion",
        action="store_const",
        const=None
    )
    parser.add_argument(
        "--huggingface-api-token-file",
        dest="huggingface_api_token",
        type=Path,
        default=DEFAULT_HUGGINGFACE_API_TOKEN_PATH,
    )
    parser.add_argument(
        "--huggingface-api-token",
        dest="huggingface_api_token",
        type=str,
        default=None,
    )

    subparsers = parser.add_subparsers(title="subcommands", dest="command")
    _prepare_parser_search(subparsers.add_parser("search"))
    _prepare_parser_search_topics(subparsers.add_parser("search-topics"))

    return parser


def _prepare_parser_search(parser: ArgumentParser):
    parser.add_argument(
        dest="query",
        type=str,
    )
    parser.add_argument(
        "--num-hits", "-k",
        dest="num_hits",
        type=int,
        default=5,
    )


def _prepare_parser_search_topics(parser: ArgumentParser):
    parser.add_argument(
        "--num-hits", "-k",
        dest="num_hits",
        type=int,
        default=5,
    )


def _parse_stemmer(stemmer: str) -> Optional[Stemmer]:
    if stemmer is None:
        return None
    elif stemmer in _STEMMERS.keys():
        return _STEMMERS[stemmer]
    else:
        raise Exception(f"Unknown stemmer: {stemmer}")


def _parse_query_expansion(query_expansion: str) -> Optional[QueryExpansion]:
    if query_expansion is None:
        return None
    elif query_expansion in _QUERY_EXPANSIONS.keys():
        return _QUERY_EXPANSIONS[query_expansion]
    else:
        raise Exception(f"Unknown query expansion: {query_expansion}")


def _parse_huggingface_api_token(
        token_or_path: Union[Path, str]
) -> Optional[str]:
    if isinstance(token_or_path, Path):
        with token_or_path.open("r") as file:
            token_or_path = file.readline().rstrip()
    token_or_path = token_or_path.strip()
    return token_or_path if token_or_path else None


def main():
    parser: ArgumentParser = ArgumentParser()
    _prepare_parser(parser)
    args: Namespace = parser.parse_args()

    documents_zip_url: str = args.documents_zip_url
    topics_zip_url: str = args.topics_zip_url
    topics_file_path: str = args.topics_file_path
    stopwords_file: Optional[Path] = args.stopwords_file
    stemmer: Optional[Stemmer] = _parse_stemmer(args.stemmer)
    language: str = args.language
    query_expansion: Optional[QueryExpansion] = _parse_query_expansion(
        args.query_expansion
    )
    hugging_face_api_token = _parse_huggingface_api_token(
        args.huggingface_api_token
    )
    pipeline = Pipeline(
        documents_zip_url=documents_zip_url,
        topics_zip_url=topics_zip_url,
        topics_file_path=topics_file_path,
        stopwords_file=stopwords_file,
        stemmer=stemmer,
        language=language,
        query_expansion=query_expansion,
        hugging_face_api_token=hugging_face_api_token,
    )

    if args.command == "search":
        query: str = args.query
        num_hits: int = args.num_hits
        pipeline.print_search(query, num_hits)
    elif args.command == "search-topics":
        num_hits: int = args.num_hits
        pipeline.print_search_topics(num_hits)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

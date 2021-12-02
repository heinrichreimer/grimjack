from pathlib import Path
from typing import Optional, List, Set

from tqdm import tqdm

from grimjack.model import RankedDocument, Query
from grimjack.model.axiom import OriginalAxiom
from grimjack.model.axiom.length_norm import TF_LNC, LNC2, LNC1
from grimjack.model.axiom.lower_bound import LB1
from grimjack.model.axiom.proximity import PROX5, PROX4, PROX3, PROX2, PROX1
from grimjack.model.axiom.query_aspects import (
    LEN_DIV, DIV, LEN_M_AND, M_AND, LEN_AND, AND, ANTI_REG, REG
)
from grimjack.model.axiom.retrieval_score import (
    RS_TF, RS_TF_IDF, RS_BM25, RS_PL2, RS_QL
)
from grimjack.model.axiom.term_frequency import LEN_M_TDC, M_TDC, TFC3, TFC1
from grimjack.modules import (
    DocumentsStore, TopicsStore, Index, QueryExpander, Searcher, Reranker,
    ArgumentTagger, ArgumentQualityTagger,
)
from grimjack.modules.argument_quality_tagger import (
    DebaterArgumentQualityTagger
)
from grimjack.modules.argument_tagger import TargerArgumentTagger
from grimjack.modules.evaluater import evaluate
from grimjack.modules.index import AnseriniIndex
from grimjack.modules.options import (
    RetrievalScore, Stemmer, QueryExpansion, RetrievalModel, RerankerType
)
from grimjack.modules.query_expander import SimpleQueryExpander
from grimjack.modules.reranker import (
    OriginalReranker, AxiomaticReranker, TopReranker
)
from grimjack.modules.reranking_context import IndexRerankingContext
from grimjack.modules.searcher import AnseriniSearcher
from grimjack.modules.store import QrelStore, SimpleDocumentsStore, \
    TrecTopicsStore


class Pipeline:
    documents_store: DocumentsStore
    topics_store: TopicsStore
    index: Index
    query_expander: QueryExpander
    searcher: Searcher
    reranker: Reranker
    argument_tagger: ArgumentTagger
    argument_quality_tagger: ArgumentQualityTagger

    def __init__(
            self,
            documents_zip_url: str,
            topics_zip_url: str,
            topics_zip_path: str,
            stopwords_file: Optional[Path],
            stemmer: Optional[Stemmer],
            language: str,
            query_expansion: Optional[QueryExpansion],
            retrieval_model: Optional[RetrievalModel],
            reranker: Optional[RerankerType],
            rerank_hits: int,
            targer_api_url: str,
            targer_models: Set[str],
            cache_path: Optional[Path],
            huggingface_api_token: Optional[str],
            debater_api_token: str,
            retrieval_score: RetrievalScore,
            depth: int,
            qrel: str,
            qrel_zip: str
    ):
        self.documents_store = SimpleDocumentsStore(documents_zip_url)
        self.topics_store = TrecTopicsStore(topics_zip_url, topics_zip_path)
        self.index = AnseriniIndex(
            self.documents_store,
            stopwords_file,
            stemmer,
            language,
        )
        self.query_expander = SimpleQueryExpander(
            query_expansion,
            huggingface_api_token,
        )
        self.searcher = AnseriniSearcher(
            self.index,
            self.query_expander,
            retrieval_model,
        )
        self.retrieval_score = retrieval_score
        self.depth = depth
        self.qrel = qrel
        self.qrel_zip = qrel_zip
        self.qrelStore = QrelStore(self.qrel_zip, self.qrel)
        reranking_context = IndexRerankingContext(self.index)
        if reranker is None:
            self.reranker = OriginalReranker()
        elif reranker == RerankerType.AXIOMATIC:
            self.reranker = AxiomaticReranker(
                reranking_context,
                (
                        OriginalAxiom() +
                        TFC1() +
                        TFC3() +
                        M_TDC() +
                        LEN_M_TDC() +
                        LNC1() +
                        LNC2() +
                        TF_LNC() +
                        LB1() +
                        REG() +
                        ANTI_REG() +
                        AND() +
                        LEN_AND() +
                        M_AND() +
                        LEN_M_AND() +
                        DIV() +
                        LEN_DIV() +
                        PROX1() +
                        PROX2() +
                        PROX3() +
                        PROX4() +
                        PROX5() +
                        RS_TF() +
                        RS_TF_IDF() +
                        RS_BM25() +
                        RS_PL2() +
                        RS_QL()
                ).normalized().cached(),
            )
        else:
            raise ValueError(f"Unknown reranker: {reranker}")
        if rerank_hits is not None:
            self.reranker = TopReranker(self.reranker, rerank_hits)
        self.argument_tagger = TargerArgumentTagger(
            targer_api_url,
            targer_models,
            cache_path / "targer" if cache_path is not None else None,
        )
        self.argument_quality_tagger = DebaterArgumentQualityTagger(
            debater_api_token,
            cache_path / "debater" if cache_path is not None else None,
        )

    def _search(self, query: Query, num_hits: int) -> List[RankedDocument]:
        ranking = self.searcher.search(query, num_hits)
        ranking = self.argument_tagger.tag_ranking(ranking)
        ranking = self.argument_quality_tagger.tag_ranking(query, ranking)
        ranking = self.reranker.rerank(query, ranking)
        return ranking

    def print_search(self, query: str, num_hits: int):
        manual_query = Query(-1, query, [], "", "")
        results = self._search(manual_query, num_hits)
        for document in results:
            print(
                f"Rank {document.rank:3}: {document.id} "
                f"(Score: {document.score:.3f})\n"
                f"\t{document.content}\n\n\n"
            )

    def print_search_all(self, num_hits: int):
        for topic in self.topics_store.topics:
            print(f"Query {topic.id}: {topic.title}\n")
            self.print_search(topic.title, num_hits)
            print("\n\n")

    def run_search_all(self, path: Path, num_hits: int):
        with path.open("w") as file:
            topics = tqdm(
                self.topics_store.topics,
                desc="Searching",
                unit="queries",
            )
            for topic in topics:
                results = self._search(topic, num_hits)
                file.writelines(
                    f"{topic.id} Q0 {document.id} {document.rank} "
                    f"{document.score} {path.stem}\n"
                    for document in results
                )
        evaluation = evaluate(
                self.qrelStore.qrels_path,
                path.absolute(),
                self.depth,
                self.retrieval_score
        )
        print(evaluation)

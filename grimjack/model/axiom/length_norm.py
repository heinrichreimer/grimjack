from grimjack.model import RankedDocument, Query
from grimjack.model.axiom import Axiom
from grimjack.model.axiom.utils import (
    strictly_less,
    approximately_equal,
    strictly_greater
)
from grimjack.modules import IndexStatistics


class LNC1(Axiom):
    def preference(
            self,
            statistics: IndexStatistics,
            query: Query,
            document1: RankedDocument,
            document2: RankedDocument
    ):
        if not all(
                approximately_equal(
                    statistics.term_frequency(document1.content, term),
                    statistics.term_frequency(document2.content, term)
                )
                for term in statistics.term_set(query.title)
        ):
            return 0

        # Prefer the shorter document.
        return strictly_less(
            len(statistics.terms(document1.content)),
            len(statistics.terms(document2.content)),
        )


class LNC2(Axiom):
    def preference(
            self,
            statistics: IndexStatistics,
            query: Query,
            document1: RankedDocument,
            document2: RankedDocument
    ):
        # LNC2 makes no sense as implemented and was useless in previous trials
        # TODO: May we delete it?
        return 0


class TF_LNC(Axiom):
    def preference(
            self,
            statistics: IndexStatistics,
            query: Query,
            document1: RankedDocument,
            document2: RankedDocument
    ):

        sd1 = 0
        sd2 = 0

        for t in statistics.term_set(query.title):
            tf_d1 = statistics.term_frequency(document1.content, t)
            tf_d2 = statistics.term_frequency(document2.content, t)
            len_d1 = len(statistics.terms(document1.content))
            len_d2 = len(statistics.terms(document2.content))
            tf_len_d1 = len_d1 + tf_d2 - tf_d1
            tf_len_d2 = len_d2 + tf_d1 - tf_d2
            if tf_d1 > tf_d2 and len_d1 == tf_len_d2:
                sd1 += 1
            elif tf_d2 > tf_d1 and len_d2 == tf_len_d1:
                sd2 += 1

        return strictly_greater(sd1, sd2)

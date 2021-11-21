from grimjack.model import RankedDocument, Query
from grimjack.model.axiom import Axiom
from grimjack.model.axiom.utils import approximately_equal
from grimjack.modules import RerankingContext


class LB1(Axiom):
    def preference(
            self,
            context: RerankingContext,
            query: Query,
            document1: RankedDocument,
            document2: RankedDocument
    ):
        if not approximately_equal(document1.score, document2.score):
            return 0

        # TODO: Do we really want to use the term set here, not the list?
        for term in context.term_set(query.title):
            tf1 = context.term_frequency(document1.content, term)
            tf2 = context.term_frequency(document2.content, term)
            if tf1 == 0 and tf2 > 0:
                return -1
            if tf2 == 0 and tf1 > 0:
                return 1
        return 0

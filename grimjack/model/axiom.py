from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from random import randint
from typing import Iterable

from grimjack.model import RankedDocument
from grimjack.modules import Index


class AxiomContext:
    index: Index


class Axiom(ABC):

    @abstractmethod
    def preference(
            self,
            context: AxiomContext,
            query: str,
            document1: RankedDocument,
            document2: RankedDocument
    ) -> float:
        pass

    def weighted(self, weight: float) -> "Axiom":
        return WeightedAxiom(self, weight)

    def __mul__(self, weight: float):
        return self.weighted(weight)

    def aggregate(self, *others: "Axiom") -> "Axiom":
        return AggregatedAxiom([self, *others])

    def __add__(self, other: "Axiom"):
        return self.aggregate(other)

    def normalized(self) -> "Axiom":
        return NormalizedAxiom(self)

    def cached(self) -> "Axiom":
        return CachedAxiom(self)


@dataclass
class WeightedAxiom(Axiom):
    axiom: Axiom
    weight: float

    def preference(
            self,
            context: AxiomContext,
            query: str,
            document1: RankedDocument,
            document2: RankedDocument
    ) -> float:
        return self.weight * self.axiom.preference(
            context,
            query,
            document1,
            document2
        )


@dataclass
class AggregatedAxiom(Axiom):
    axioms: Iterable[Axiom]

    def preference(
            self,
            context: AxiomContext,
            query: str,
            document1: RankedDocument,
            document2: RankedDocument
    ) -> float:
        return sum(
            axiom.preference(context, query, document1, document2)
            for axiom in self.axioms
        )


@dataclass
class NormalizedAxiom(Axiom):
    axiom: Axiom

    def preference(
            self,
            context: AxiomContext,
            query: str,
            document1: RankedDocument,
            document2: RankedDocument
    ) -> float:
        preference = self.axiom.preference(
            context,
            query,
            document1,
            document2
        )
        if preference > 0:
            return 1
        elif preference < 0:
            return -1
        else:
            return 0


@dataclass
class CachedAxiom(Axiom):
    axiom: Axiom
    _cache: dict[tuple[str, str], float] = field(
        default_factory=lambda: {},
        init=False,
        repr=False
    )

    def preference(
            self,
            context: AxiomContext,
            query: str,
            document1: RankedDocument,
            document2: RankedDocument
    ) -> float:
        if (document1.id, document2.id) in self._cache:
            return self._cache[document1.id, document2.id]
        elif (document2.id, document1.id) in self._cache:
            return -self._cache[document2.id, document1.id]
        else:
            preference = self.axiom.preference(
                context,
                query,
                document1,
                document2
            )
            self._cache[document1.id, document2.id] = preference
            return preference


class RandomAxiom(Axiom):
    def preference(
            self,
            context: AxiomContext,
            query: str,
            document1: RankedDocument,
            document2: RankedDocument
    ) -> float:
        return randint(-1, 1)


class DocumentIdAxiom(Axiom):
    """
    For testing purposes only.
    """

    def preference(
            self,
            context: AxiomContext,
            query: str,
            document1: RankedDocument,
            document2: RankedDocument
    ) -> float:
        if document1.id < document2.id:
            return 1
        elif document1.id > document2.id:
            return -1
        else:
            return 0

"""
Estructura de conjuntos disjuntos (Union-Find / Disjoint Set Union)
implementada desde cero con compresión de caminos y unión por rango.

Complejidad:
- Tiempo: O(α(N)) por operación find/union, donde α es la inversa de Ackermann (efectivamente ≤ 4).
- Espacio: O(N).
"""

from typing import Dict, Generic, Iterable, List, Set, TypeVar

T = TypeVar("T")


class UnionFind(Generic[T]):
    """
    Estructura de datos Union-Find para particionamiento dinámico de conjuntos.
    """

    def __init__(self, elementos: Iterable[T] = ()) -> None:
        self.padre: Dict[T, T] = {}
        self.rango: Dict[T, int] = {}
        self.tamano: Dict[T, int] = {}
        self._num_conjuntos: int = 0

        for elem in elementos:
            self.agregar(elem)

    def agregar(self, elem: T) -> None:
        """Agrega un nuevo elemento como conjunto unitario si no existe."""
        if elem not in self.padre:
            self.padre[elem] = elem
            self.rango[elem] = 0
            self.tamano[elem] = 1
            self._num_conjuntos += 1

    def find(self, x: T) -> T:
        """
        Encuentra el representante canónico del conjunto que contiene a x
        aplicando compresión de caminos (path compression).

        Complejidad: O(α(N)).
        """
        if x not in self.padre:
            self.agregar(x)
            return x

        raiz = x
        while self.padre[raiz] != raiz:
            raiz = self.padre[raiz]

        # Compresión de caminos en dos pasadas
        curr = x
        while curr != raiz:
            sig = self.padre[curr]
            self.padre[curr] = raiz
            curr = sig

        return raiz

    def union(self, x: T, y: T) -> bool:
        """
        Une los conjuntos que contienen a x y a y utilizando unión por rango.

        Retorna True si pertenecían a conjuntos distintos y se unieron;
        False si ya estaban en el mismo conjunto.

        Complejidad: O(α(N)).
        """
        raiz_x = self.find(x)
        raiz_y = self.find(y)

        if raiz_x == raiz_y:
            return False

        if self.rango[raiz_x] < self.rango[raiz_y]:
            self.padre[raiz_x] = raiz_y
            self.tamano[raiz_y] += self.tamano[raiz_x]
        elif self.rango[raiz_x] > self.rango[raiz_y]:
            self.padre[raiz_y] = raiz_x
            self.tamano[raiz_x] += self.tamano[raiz_y]
        else:
            self.padre[raiz_y] = raiz_x
            self.tamano[raiz_x] += self.tamano[raiz_y]
            self.rango[raiz_x] += 1

        self._num_conjuntos -= 1
        return True

    def conectados(self, x: T, y: T) -> bool:
        """Determina si x e y pertenecen al mismo conjunto."""
        return self.find(x) == self.find(y)

    @property
    def num_conjuntos(self) -> int:
        """Número actual de conjuntos disjuntos."""
        return self._num_conjuntos

    def obtener_tamano_conjunto(self, x: T) -> int:
        """Retorna la cardinalidad del conjunto que contiene a x."""
        raiz = self.find(x)
        return self.tamano[raiz]

    def obtener_componentes(self) -> Dict[T, List[T]]:
        """
        Agrupa los elementos por su representante canónico.
        Complejidad: O(N α(N)).
        """
        componentes: Dict[T, List[T]] = {}
        for elem in self.padre:
            raiz = self.find(elem)
            if raiz not in componentes:
                componentes[raiz] = []
            componentes[raiz].append(elem)
        return componentes

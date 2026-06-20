"""
Fila implementada com lista encadeada simples (singly linked list).

Escolha da estrutura:
  - Lista encadeada garante enqueue e dequeue em O(1) real,
    sem realocação de memória como ocorreria com lista Python.
  - Mantemos ponteiros para head (frente) e tail (fim),
    permitindo inserção no tail e remoção no head, ambas O(1).

Invariantes:
  - head aponta para o próximo elemento a ser removido (frente da fila).
  - tail aponta para o último elemento inserido (fim da fila).
  - Se a fila está vazia, head = tail = None e _size = 0.
"""


class _No:
    __slots__ = ("valor", "proximo")   # economiza memória

    def __init__(self, valor):
        self.valor   = valor
        self.proximo = None   # próximo nó em direção ao tail


class Fila:

    def __init__(self):
        self._head  = None   # frente da fila (próximo a sair)
        self._tail  = None   # fim da fila    (último a entrar)
        self._size  = 0

    # ------------------------------------------------------------------ #
    #  Operações principais                                                #
    # ------------------------------------------------------------------ #

    def enqueue(self, valor):
        """Insere `valor` no fim da fila."""
        novo = _No(valor)

        if self._tail is None:          # fila estava vazia
            self._head = novo
            self._tail = novo
        else:
            self._tail.proximo = novo   # encadeia no fim
            self._tail         = novo   # atualiza ponteiro do tail

        self._size += 1

    def dequeue(self):
        """
        Remove e retorna o valor da frente da fila.
        Lança IndexError se a fila estiver vazia.
        """
        if self.is_empty():
            raise IndexError("dequeue em fila vazia")

        valor      = self._head.valor
        self._head = self._head.proximo   # avança frente

        if self._head is None:            # fila ficou vazia
            self._tail = None

        self._size -= 1
        return valor

    def peek(self):
        """
        Retorna o valor da frente sem removê-lo.
        Lança IndexError se a fila estiver vazia.
        """
        if self.is_empty():
            raise IndexError("peek em fila vazia")
        return self._head.valor

    def is_empty(self):
        """Retorna True se a fila não contiver elementos."""
        return self._size == 0

    def size(self):
        """Retorna o número de elementos na fila."""
        return self._size

    # ------------------------------------------------------------------ #
    #  Utilitários                                                         #
    # ------------------------------------------------------------------ #

    def __len__(self):
        return self._size

    def __repr__(self):
        """Representação para depuração: frente → ... → fim."""
        elementos = []
        atual = self._head
        while atual is not None:
            elementos.append(repr(atual.valor))
            atual = atual.proximo
        return "Fila([" + ", ".join(elementos) + "])  frente→fim"

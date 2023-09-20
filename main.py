import sys
from math import log2


class IO:
    def output(self, s):
        print(s, end='')


# Exceção (erro)
class EnderecoInvalido(Exception):
    def __init__(self, ender):
        self.ender = ender


class RAM:
    def __init__(self, k):
        self.capacidade = 2 ** k
        self.memoria = [0] * self.capacidade  # Cria uma lista com o tamanho da capacidade

    def verifica_endereco(self, ender):
        if (ender < 0) or (ender >= self.capacidade):
            raise EnderecoInvalido(ender)

    def tamanho(self):
        return self.capacidade

    def read(self, ender):
        self.verifica_endereco(ender)
        return self.memoria[ender]

    def write(self, ender, val):
        self.verifica_endereco(ender)
        self.memoria[ender] = val


class CacheLine:
    def __init__(self, tamanho):
        self.tag = None
        self.cache_line = [0] * tamanho
        self.modif = False


class Cache(RAM):
    def __init__(self, tamanho_cache, quantidade_palavras_bloco, ram):
        self.ram = ram
        self.palavras = quantidade_palavras_bloco
        self.quantidade_cache_lines = tamanho_cache // quantidade_palavras_bloco
        self.cache_lines = [CacheLine(quantidade_palavras_bloco) for _ in range(self.quantidade_cache_lines)]

    def read(self, ender):
        r, t, w = self.decompor_endereco(ender)
        if self.esta_em_cache(ender):
            #retorna para CPU
            return self.cache_lines[r].cache_line[w]
        else:
            #carrega bloco correto
            self.carregar_bloco_da_ram(ender)
            #retorna para CPU
            return self.cache_lines[r].cache_line[w]

    def write(self, ender, val):
        r, t, w = self.decompor_endereco(ender)
        if self.esta_em_cache(ender):
            #Incrementa valor na posição
            self.cache_lines[r].cache_line[w] = val
            #Marca como modificado
            self.cache_lines[r].modif = True
        else:
            #carrega bloco correto
            self.carregar_bloco_da_ram(ender)
            #Incrementa valor na posição
            self.cache_lines[r].cache_line[w] = val
            #Marca como modificado
            self.cache_lines[r].modif = True

    def esta_em_cache(self, ender):
        r, t, w = self.decompor_endereco(ender)
        if self.cache_lines[r].tag == t:
            return True
        else:
            return False

    def decompor_endereco(self, ender):
        w_bits = int(log2(self.palavras))
        r_bits = int(log2(self.quantidade_cache_lines))
        t_bits = int(log2(self.ram.capacidade)) - w_bits - r_bits

        #print(w_bits)
        #print(r_bits)
        #print(t_bits)

        w = ender & ((1 << w_bits) - 1)
        r = (ender >> w_bits) & ((1 << r_bits) - 1)
        t = (ender >> (w_bits + r_bits)) & ((1 << t_bits) - 1)

        #print(w)
        #print(r)
        #print(t)

        w_int = int(bin(w), 2)
        r_int = int(bin(r), 2)
        t_int = int(bin(t), 2)

        return r_int, t_int, w_int

    def carregar_bloco_da_ram(self, ender):
        r, t, w = self.decompor_endereco(ender)
        if self.cache_lines[r].modif:
            # retornar bloco modificado para posição do bloco da ram
            for i in range(self.palavras):
                self.ram.memoria[(t + r) + i] = self.cache_lines[r].cache_line[i]
            return
        # tras bloco correto da RAM para posição da cache
        for i in range(self.palavras):
            self.cache_lines[r].cache_line[i] = self.ram.memoria[(t + r) + i]
            self.cache_lines[r].tag = t


class CPU:
    def __init__(self, mem, io):
        self.mem = mem
        self.io = io
        self.PC = 0
        self.A = self.B = self.C = 0

    def run(self, ender):
        self.PC = ender
        self.A = self.mem.read(self.PC)
        self.io.output(f"{self.A}")
        self.PC += 1
        self.B = self.mem.read(self.PC)
        self.PC += 1

        self.C = 1
        while self.A <= self.B:
            self.mem.write(self.A, self.C)
            self.io.output(f"{self.A} -> {self.C}\n")
            self.C += 1
            self.A += 1


try:
    io = IO()
    ram = RAM(11)   # 2K de RAM (2**11)
    cache = Cache(128, 16, ram) # total cache = 128, cacheline = 16 palavras
    cpu = CPU(cache, io)

    inicio = 0;
    ram.write(inicio, 110)
    ram.write(inicio+1, 130)
    cpu.run(inicio)
except EnderecoInvalido as e:
    print("Endereco inválido:", e.ender, file=sys.stderr)
# -*- coding: utf-8 -*-
"""Generateur de QR code minimal, sans dependance.

Mode octet, niveau de correction M, versions 1 a 10 (largement suffisant pour
une URL de salle de classe). Rend une matrice de 0/1, du SVG ou du texte.
"""

# --- Corps de Galois GF(256) ------------------------------------------------

_EXP = [0] * 512
_LOG = [0] * 256
_x = 1
for _i in range(255):
    _EXP[_i] = _x
    _LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
for _i in range(255, 512):
    _EXP[_i] = _EXP[_i - 255]


def _mul(a, b):
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]


def _rs_generator(n):
    poly = [1]
    for i in range(n):
        new = [0] * (len(poly) + 1)
        for j, p in enumerate(poly):
            new[j] ^= _mul(p, 1)
            new[j + 1] ^= _mul(p, _EXP[i])
        poly = new
    return poly


def _rs_encode(data, n):
    gen = _rs_generator(n)[1:]  # on ignore le coefficient de tete (1)
    rem = [0] * n
    for byte in data:
        factor = byte ^ rem[0]
        rem = rem[1:] + [0]
        if factor:
            for i, g in enumerate(gen):
                rem[i] ^= _mul(g, factor)
    return rem


# --- Tables (niveau de correction M, versions 1 a 10) -----------------------

# version -> (ec codewords par bloc, [(nb blocs, data cw par bloc), ...])
_SPEC = {
    1: (10, [(1, 16)]),
    2: (16, [(1, 28)]),
    3: (26, [(1, 44)]),
    4: (18, [(2, 32)]),
    5: (24, [(2, 43)]),
    6: (16, [(4, 27)]),
    7: (18, [(4, 31)]),
    8: (22, [(2, 38), (2, 39)]),
    9: (22, [(3, 36), (2, 37)]),
    10: (26, [(4, 43), (1, 44)]),
}

_ALIGN = {
    1: [],
    2: [6, 18],
    3: [6, 22],
    4: [6, 26],
    5: [6, 30],
    6: [6, 34],
    7: [6, 22, 38],
    8: [6, 24, 42],
    9: [6, 26, 46],
    10: [6, 28, 50],
}

_MASKS = [
    lambda i, j: (i + j) % 2 == 0,
    lambda i, j: i % 2 == 0,
    lambda i, j: j % 3 == 0,
    lambda i, j: (i + j) % 3 == 0,
    lambda i, j: (i // 2 + j // 3) % 2 == 0,
    lambda i, j: (i * j) % 2 + (i * j) % 3 == 0,
    lambda i, j: ((i * j) % 2 + (i * j) % 3) % 2 == 0,
    lambda i, j: ((i + j) % 2 + (i * j) % 3) % 2 == 0,
]


def _data_capacity(version):
    return sum(n * k for n, k in _SPEC[version][1])


def _choose_version(nbytes):
    for v in range(1, 11):
        header = 4 + (8 if v <= 9 else 16)
        if _data_capacity(v) * 8 >= header + nbytes * 8:
            return v
    raise ValueError("Contenu trop long pour ce generateur (max version 10).")


def _bit(value, i):
    return (value >> i) & 1


# --- Encodage des donnees ---------------------------------------------------


def _bitstream(data, version):
    total_bits = _data_capacity(version) * 8
    bits = [0, 1, 0, 0]  # mode octet
    count_len = 8 if version <= 9 else 16
    bits += [_bit(len(data), i) for i in range(count_len - 1, -1, -1)]
    for byte in data:
        bits += [_bit(byte, i) for i in range(7, -1, -1)]

    bits += [0] * min(4, total_bits - len(bits))  # terminateur
    while len(bits) % 8:
        bits.append(0)
    pad = (0xEC, 0x11)
    k = 0
    while len(bits) < total_bits:
        bits += [_bit(pad[k % 2], i) for i in range(7, -1, -1)]
        k += 1
    return bits


def _codewords(data, version):
    bits = _bitstream(data, version)
    dcw = [int("".join(str(b) for b in bits[i : i + 8]), 2) for i in range(0, len(bits), 8)]

    ecc_len, groups = _SPEC[version]
    blocks, ecblocks, pos = [], [], 0
    for count, size in groups:
        for _ in range(count):
            block = dcw[pos : pos + size]
            pos += size
            blocks.append(block)
            ecblocks.append(_rs_encode(block, ecc_len))

    out = []
    for i in range(max(len(b) for b in blocks)):
        for b in blocks:
            if i < len(b):
                out.append(b[i])
    for i in range(ecc_len):
        for b in ecblocks:
            out.append(b[i])
    return out


# --- Construction de la matrice --------------------------------------------


class _Canvas:
    """Matrice de modules, avec la trace des modules fonctionnels."""

    def __init__(self, version):
        self.version = version
        self.size = version * 4 + 17
        self.m = [[0] * self.size for _ in range(self.size)]
        self.fn = [[False] * self.size for _ in range(self.size)]

    def put(self, row, col, dark):
        self.m[row][col] = 1 if dark else 0
        self.fn[row][col] = True

    def inside(self, row, col):
        return 0 <= row < self.size and 0 <= col < self.size

    # -- motifs fonctionnels ------------------------------------------------

    def draw_function_patterns(self):
        n = self.size
        for i in range(n):  # synchronisation
            self.put(6, i, i % 2 == 0)
            self.put(i, 6, i % 2 == 0)

        for r, c in ((3, 3), (3, n - 4), (n - 4, 3)):  # reperes + separateurs
            for dr in range(-4, 5):
                for dc in range(-4, 5):
                    if self.inside(r + dr, c + dc):
                        dist = max(abs(dr), abs(dc))
                        self.put(r + dr, c + dc, dist not in (2, 4))

        centers = _ALIGN[self.version]
        corners = {(6, 6), (6, n - 7), (n - 7, 6)}
        for r in centers:
            for c in centers:
                if (r, c) in corners:
                    continue
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        self.put(r + dr, c + dc, max(abs(dr), abs(dc)) != 1)

        self.draw_format(0)  # reserve la zone
        self.draw_version()

    def draw_format(self, mask):
        data = (0b00 << 3) | mask  # niveau M = 00
        rem = data
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = ((data << 10) | rem) ^ 0x5412

        for i in range(6):
            self.put(i, 8, _bit(bits, i))
        self.put(7, 8, _bit(bits, 6))
        self.put(8, 8, _bit(bits, 7))
        self.put(8, 7, _bit(bits, 8))
        for i in range(9, 15):
            self.put(8, 14 - i, _bit(bits, i))

        n = self.size
        for i in range(8):
            self.put(8, n - 1 - i, _bit(bits, i))
        for i in range(8, 15):
            self.put(n - 15 + i, 8, _bit(bits, i))
        self.put(n - 8, 8, 1)  # module toujours sombre

    def draw_version(self):
        if self.version < 7:
            return
        rem = self.version
        for _ in range(12):
            rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
        bits = (self.version << 12) | rem
        n = self.size
        for i in range(18):
            b = _bit(bits, i)
            a, c = n - 11 + i % 3, i // 3
            self.put(c, a, b)
            self.put(a, c, b)

    # -- donnees ------------------------------------------------------------

    def draw_codewords(self, cw):
        n = self.size
        i = 0
        total = len(cw) * 8
        right = n - 1
        while right >= 1:
            if right == 6:
                right = 5
            for vert in range(n):
                for j in range(2):
                    col = right - j
                    upward = ((right + 1) & 2) == 0
                    row = (n - 1 - vert) if upward else vert
                    if not self.fn[row][col] and i < total:
                        self.m[row][col] = _bit(cw[i >> 3], 7 - (i & 7))
                        i += 1
            right -= 2

    def apply_mask(self, mask):
        f = _MASKS[mask]
        for r in range(self.size):
            for c in range(self.size):
                if not self.fn[r][c] and f(r, c):
                    self.m[r][c] ^= 1

    def penalty(self):
        n, m = self.size, self.m
        score = 0
        lines = [list(row) for row in m] + [list(col) for col in zip(*m, strict=True)]
        pat1 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]
        pat2 = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1]
        for line in lines:
            run, prev = 1, line[0]
            for v in line[1:]:
                if v == prev:
                    run += 1
                else:
                    if run >= 5:
                        score += 3 + (run - 5)
                    run, prev = 1, v
            if run >= 5:
                score += 3 + (run - 5)
            for i in range(n - 10):
                seg = line[i : i + 11]
                if seg == pat1 or seg == pat2:
                    score += 40
        for r in range(n - 1):
            for c in range(n - 1):
                if m[r][c] == m[r][c + 1] == m[r + 1][c] == m[r + 1][c + 1]:
                    score += 3
        dark = sum(sum(row) for row in m)
        score += 10 * (abs(dark * 100 // (n * n) - 50) // 5)
        return score


def matrix(text):
    """Matrice du QR code encodant `text` (liste de listes de 0/1)."""
    data = text.encode("utf-8")
    version = _choose_version(len(data))
    cw = _codewords(data, version)

    best, best_score = None, None
    for mask in range(8):
        canvas = _Canvas(version)
        canvas.draw_function_patterns()
        canvas.draw_codewords(cw)
        canvas.apply_mask(mask)
        canvas.draw_format(mask)
        s = canvas.penalty()
        if best_score is None or s < best_score:
            best, best_score = canvas.m, s
    return best


# --- Rendu ------------------------------------------------------------------


def svg(text, quiet=3, dark="#0b1020", light="#ffffff"):
    m = matrix(text)
    n = len(m)
    total = n + 2 * quiet
    path = []
    for r in range(n):
        c = 0
        while c < n:
            if m[r][c]:
                start = c
                while c < n and m[r][c]:
                    c += 1
                path.append("M%d %dh%dv1h-%dz" % (start + quiet, r + quiet, c - start, c - start))
            else:
                c += 1
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {t} {t}" '
        'shape-rendering="crispEdges" role="img" aria-label="QR code">'
        '<rect width="{t}" height="{t}" fill="{light}"/>'
        '<path fill="{dark}" d="{d}"/></svg>'
    ).format(t=total, d="".join(path), dark=dark, light=light)


def ascii_art(text, quiet=2):
    """Rendu console en demi-blocs (deux lignes de modules par ligne texte)."""
    m = matrix(text)
    n = len(m)
    width = n + 2 * quiet
    grid = [[0] * width for _ in range(quiet)]
    grid += [[0] * quiet + list(row) + [0] * quiet for row in m]
    grid += [[0] * width for _ in range(quiet)]
    if len(grid) % 2:
        grid.append([0] * width)

    chars = {(0, 0): " ", (1, 0): "▀", (0, 1): "▄", (1, 1): "█"}
    return "\n".join(
        "".join(chars[(grid[r][c], grid[r + 1][c])] for c in range(width))
        for r in range(0, len(grid), 2)
    )

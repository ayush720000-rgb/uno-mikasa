#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Telegram bot to play UNO in group chats
# Copyright (c) 2016 Jannes Höke <uno@jhoeke.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


# Colors
RED = 'r'
BLUE = 'b'
GREEN = 'g'
YELLOW = 'y'
BLACK = 'x'

COLORS = (RED, BLUE, GREEN, YELLOW)

COLOR_ICONS = {
    RED: '❤️',
    BLUE: '💙',
    GREEN: '💚',
    YELLOW: '💛',
    BLACK: '⬛️'
}

# Values
ZERO = '0'
ONE = '1'
TWO = '2'
THREE = '3'
FOUR = '4'
FIVE = '5'
SIX = '6'
SEVEN = '7'
EIGHT = '8'
NINE = '9'
DRAW_TWO = 'draw'
REVERSE = 'reverse'
SKIP = 'skip'

VALUES = (ZERO, ONE, TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, DRAW_TWO,
          REVERSE, SKIP)
WILD_VALUES = (ONE, TWO, THREE, FOUR, FIVE, DRAW_TWO, REVERSE, SKIP)

# Special cards
CHOOSE = 'colorchooser'
DRAW_FOUR = 'draw_four'

SPECIALS = (CHOOSE, DRAW_FOUR)

CARDS_CLASSIC_COLORBLIND = {
    "normal": {
        "colorchooser": "CAACAgUAAxkBAAESLC5q8FIwFHFAMmcAAeAWpxyBAmK75ZgAAlcmAAIivolX7YT8Y43b9Ck9BA",
        "draw_four": "CAACAgUAAxkBAAESLDlq8FJcIsd1_2vGY6EnMy_yiYlDugACgyEAAn_kgVeZpzRWaQ4ahT0E",
        "r_0": "CAACAgUAAxkBAAESLDtq8FJdP0fe19OHYYurQVvKkSjDlwACmyEAAk-3gVdZZbRBNlyCrz0E",
        "r_1": "CAACAgUAAxkBAAESLD1q8FJePD1jakWtklXcD3qVVVICcAAC4ScAAp11iVfcinmmk8F_Hj0E",
        "r_2": "CAACAgUAAxkBAAESLD9q8FJfjKgTC4K5TY9wirRJLYD68gACTB4AAoqIiFdLLff7DbYBBz0E",
        "r_3": "CAACAgUAAxkBAAESLEFq8FJgCwYW2Ppb2dhGGxwav3_gfAAC3iAAAgYOgFdIiWKhPdlvSz0E",
        "r_4": "CAACAgUAAxkBAAESLGpq8FUx3yj2U2tvOOGZoe3QeuDJ6wACuCMAAqz6gFe01MK2jkxK7D0E",
        "r_5": "CAACAgUAAxkBAAESLGxq8FUz2tPURJKlbjuR15do63PzgAAC1iUAAijZgVfRjmX3G2oszD0E",
        "r_6": "CAACAgUAAxkBAAESLEZq8FJhBz7eVlUhqwK1Q9sJBh7joAACCiQAAmDOgVcTaPRO5bPXjz0E",
        "r_7": "CAACAgUAAxkBAAESLE9q8FJk1JKpVYoVdxOz8YQBa_U-GQACHiYAAlN6gVfs8Q-pfF-i4j0E",
        "r_8": "CAACAgUAAxkBAAESLEpq8FJjtvsM_M9zGD08Y6eMuv-VVQACyykAAitBiFdgEJIPSdUt5D0E",
        "r_9": "CAACAgUAAxkBAAESLEtq8FJjaGxCQ6djJmweYJFscYXO2wACiSIAArvvgVfuLMpi_VJkXD0E",
        "r_draw": "CAACAgUAAxkBAAESLExq8FJjG4dvrR8H4JZ_ycgm4sFgpAACxSAAAnLpgVcoYd1Alg4dhD0E",
        "r_reverse": "CAACAgUAAxkBAAESLE5q8FJjoCUkUyd85c5K-5Rxh5tkcgACrCEAAuYzgFduOs-rRZ7m8D0E",
        "r_skip": "CAACAgUAAxkBAAESLHpq8FVTiQ5mokfi57piSmAgidVvOwACIyUAAtJXgFdT_c2MLXxx_j0E",
        "g_0": "CAACAgUAAxkBAAESLFBq8FJkauoI8M5PVwgUyfrv_HyPcwACfyQAAqDPgVcxGd3vfiWiAj0E",
        "g_1": "CAACAgUAAxkBAAESLFJq8FJkHQF_gHS3rBEUP86hVA_q2AACQCQAAgrmgFf8ZivfQ0lsxz0E",
        "g_2": "CAACAgUAAxkBAAESLIBq8FVZ29KxXbAMdD-_ikL_e-VbHgACLysAAgg_gVfynw1cL2dP9T0E",
        "g_3": "CAACAgUAAxkBAAESLIJq8FVbjfg-_CMCW4r5ZKXRs_kRwAACuSQAAjvdgFdaWuSZCzhduz0E",
        "g_4": "CAACAgUAAxkBAAESLFVq8FJls8m0vXD78ib2t7EOSkRc3QAC4CcAAqxXgVcRRcuJMSCjVT0E",
        "g_5": "CAACAgUAAxkBAAESLIZq8FVeO7ats-ZE4OVfavhJytVM9AACoSUAAqsIgVf2UcQcSuo5cD0E",
        "g_6": "CAACAgUAAxkBAAESLIhq8FVgb9tk-PMLwelbdIYM17IfmwACTCYAAo5ggVcgHqJdLORnmD0E",
        "g_7": "CAACAgUAAxkBAAESLIpq8FVig3x1Od2hUrRpZ-VDw9dRKgAC_icAAppLgVeoB43_-Cb9IT0E",
        "g_8": "CAACAgUAAxkBAAESLIxq8FVj-EE_dWxdvOlATu3LYhrBiwACHCYAAk2-gFfWwFjvP16pUD0E",
        "g_9": "CAACAgUAAxkBAAESLI5q8FVkwfWYTvZDsjzIiH1Bc0mDlwACbyMAAvNqgVeHAfnLo6vYIT0E",
        "g_draw": "CAACAgUAAxkBAAESLJBq8FVmh8_ecn7MfnnKrjM2eeu8BwAC7SQAAv8XgVd6JU5pOeuT-j0E",
        "g_reverse": "CAACAgUAAxkBAAESLJJq8FVnz19SMcGH8crLaqRXrkC6CQACcCMAAu7zgFeyJAYBIN4zGz0E",
        "g_skip": "CAACAgUAAxkBAAESLJRq8FVpWVXtCAQkX3qcxMWF3cYSAgACrSMAAtfTgVcGJ35upV4Pej0E",
        "b_0": "CAACAgUAAxkBAAESLJZq8FVrJzb9IpBsO0mC8bkbxr030QAC7CIAAt2cgFdpXAUfrkifGz0E",
        "b_1": "CAACAgUAAxkBAAESLJhq8FVtfJRCylQp6X7T9YlpviK9YAACw68AArk-gVeEckI7zbRwEj0E",
        "b_2": "CAACAgUAAxkBAAESLJpq8FVvT4sf2cVeyj4AAUTc5WQLpZIAAlolAAJncYBXjJehcurS_mA9BA",
        "b_3": "CAACAgUAAxkBAAESLJxq8FVzf7X00bC-Z5msk-9x72x_9gAC5iMAAj04gFdf-icDulfMKT0E",
        "b_4": "CAACAgUAAxkBAAESLJ5q8FV1Fk09j2YCiosgRqcdek9r_QACLiQAAiUzgFdlB2WyqZYlrz0E",
        "b_5": "CAACAgUAAxkBAAESLKBq8FV3HoU2cJum9U0AAT3yvd4FLPkAAosiAAIfLIFXndWZ0s4B3eI9BA",
        "b_6": "CAACAgUAAxkBAAESLKJq8FV44VjhVrSjPwVi4OPKGPaBTAACsSEAAj0hgVfoPbiS2WC1yz0E",
        "b_7": "CAACAgUAAxkBAAESLKRq8FV6ezqltEzLVdD6dgwSbwTDOgACOyAAAtFDgVdAAAEiuDkd_CI9BA",
        "b_8": "CAACAgUAAxkBAAESLKZq8FV75iW_8tD3kojhxTBVXyCFhwACECUAAmj5gVffU6KVy9tW2j0E",
        "b_9": "CAACAgUAAxkBAAESLKhq8FV9H4AG7HE2qeZ5NQKQYalxAAPZJAACHIyJV-TuKl47fxbyPQQ",
        "b_draw": "CAACAgUAAxkBAAESLKpq8FV_5f0_pJZk7UHjana5zwABkB4AAsQpAALAooBXrQR3iwABLf7NPQQ",
        "b_reverse": "CAACAgUAAxkBAAESLKxq8FWAd0R2xjXafPTiOLpjfJauZQACkykAAkfGiVdGJrID8eg5nz0E",
        "b_skip": "CAACAgUAAxkBAAESLK5q8FWC9AGgKDfmRmsWAjiPThR2nQAC4SUAAuOtgFdGActh3vt6jz0E",
        "y_0": "CAACAgUAAxkBAAESLLBq8FWDvrzd6uq2AxxHrmP4f9EmYQACWycAAhDBgFel2iZW6_oYPz0E",
        "y_1": "CAACAgUAAxkBAAESLLJq8FWFyoYMZ6uxQvjBSXjmFCKWGQACMyYAAqPeiFfD8cPPijQjAT0E",
        "y_2": "CAACAgUAAxkBAAESLLRq8FWGj7VxtF7p-F_Z_x_EMzwcxwACcCkAAtefiVeFaPEp5l4gIj0E",
        "y_3": "CAACAgUAAxkBAAESLLZq8FWI4moKXLmNXrhRdIi_kqsgzAACtygAApLUgVfVCObVz25Q2D0E",
        "y_4": "CAACAgUAAxkBAAESLLhq8FWJ11_H8fNOIS82k7t_cnV1nQACySMAAkOPgVe4F7ImK__wXz0E",
        "y_5": "CAACAgUAAxkBAAESLLpq8FWLXwVOthuSxYiY9xV4HlRM_QACwCUAAj3lgVet-eQk2YuDbz0E",
        "y_6": "CAACAgUAAxkBAAESLLxq8FWNWSbFsVFa8OpLSAq026QWaQAC1iMAAokqgFehNf2NpTArpj0E",
        "y_7": "CAACAgUAAxkBAAESLMBq8FWXihL9ZJTMAgZD64a4jzexVwACpyMAAogfgFdoyPyg_gbNdT0E",
        "y_8": "CAACAgUAAxkBAAESLMJq8FWZW14F-PWQj3_USwEmCUFdLAAChSkAAmJigVcoK_g1I9CzfT0E",
        "y_9": "CAACAgUAAxkBAAESLMRq8FWaIrOVRas0hNXeGo1iJne0bQACRCMAAuCvgFcmpAc_vVmmVj0E",
        "y_draw": "CAACAgUAAxkBAAESLMZq8FWcB7Hjlsff84XE89ar7qB1GQACQyoAAlCPgVfSYLPD_gSluD0E",
        "y_reverse": "CAACAgUAAxkBAAESLMhq8FWdhRUHx_jviYG7VQKdcQRfCwACuSMAAjfeiFfDHtT5Z71q-T0E",
        "y_skip": "CAACAgUAAxkBAAESLMpq8FWf3ajMpihik7Nhug2wLTFrBAACYyIAAoFVgFddNbAuUPW6Uz0E",
    },
    "not_playable": {
        "colorchooser": "CAADBAADpQ4AAlfDmFFHGkwyGFeCFQI",
        "draw_four": "CAADBAADMRMAAv7amFHvKGLoNyFbNQI",
        "r_0": "CAADBAADsBMAAuGdkFHTZ-jl4eNn-gI",
        "r_1": "CAADBAADVA4AAhpfkFEKt19qveGSPgI",
        "r_2": "CAADBAADrw0AAoWsmVHguULNoYJwUwI",
        "r_3": "CAADBAADzxMAAjvkkFFdtKJu5WGwUgI",
        "r_4": "CAADBAAD1Q8AAoHZkFFvyQnFHzfwiQI",
        "r_5": "CAADBAADWxEAAvkHkFGUo86qxKV0kwI",
        "r_6": "CAADBAAD_hIAAjx0mVGmlm-b_FHQBAI",
        "r_7": "CAADBAADmhEAAslomFHOv7bqcDJkDAI",
        "r_8": "CAADBAADtw0AAgqVmVG2HdSbcJYxZgI",
        "r_9": "CAADBAADNxEAAuF6mVE3WzTMJkSVAgI",
        "r_draw": "CAADBAADVxAAAiNukFE1K2xORNnfMwI",
        "r_reverse": "CAADBAADQxMAAvH0mVHKznpt-uu9ngI",
        "r_skip": "CAADBAADZA4AApbPkFFB9E2Px-HFpgI",
        "g_0": "CAADBAAD8w4AAjDEmFG7DwKggUEj9QI",
        "g_1": "CAADBAAD2g0AAo_DmVHIPG84WdIo1wI",
        "g_2": "CAADBAADEhEAAoRXmVGIG2nuN45P6AI",
        "g_3": "CAADBAADug8AAsSRmFFzk0TcRuG8VAI",
        "g_4": "CAADBAADrQ8AAvgmkFESfo9BjF7-3gI",
        "g_5": "CAADBAADVhAAAnPqkFFtxtFX9HlT-AI",
        "g_6": "CAADBAADMg8AAiSBmFHIQw1jFjv6UwI",
        "g_7": "CAADBAADvREAAv0BkVGDq3H1DCq_DQI",
        "g_8": "CAADBAADWQ4AAhOEkVG96JDgCtFrEwI",
        "g_9": "CAADBAAD2xYAAruDmFFAUMFryEwjoAI",
        "g_draw": "CAADBAADLA4AAu9tkVGTzBbeeYydIQI",
        "g_reverse": "CAADBAADVAwAAhYYmFExJS0ozE8-rAI",
        "g_skip": "CAADBAADYg4AAulsmFHxOkaz9OsTiwI",
        "b_0": "CAADBAADVxUAAtnOkFEIAAGw5CZEIxgC",
        "b_1": "CAADBAAD1RAAAnQqkFF9kDqD0wp3ngI",
        "b_2": "CAADBAADZg4AAvcUmVHTXwldirf1hAI",
        "b_3": "CAADBAADfBAAAkX1mVHw0CWX0h31iQI",
        "b_4": "CAADBAADPBAAAuTCmFFDpvXzes4qjwI",
        "b_5": "CAADBAADTQ4AAsWQmVHcrxDQUWOB4AI",
        "b_6": "CAADBAAD_hAAAoUhmVG8kjd65J8EngI",
        "b_7": "CAADBAADlRAAArtjkFGko5TuFNnncwI",
        "b_8": "CAADBAADZQ8AAltEmFE_fDYIXBrV3QI",
        "b_9": "CAADBAADrhAAAtM-mVGwhrWTD9IaYgI",
        "b_draw": "CAADBAADtQ0AAnVbmFGC1hI60JaOQQI",
        "b_reverse": "CAADBAADShEAAlcOmFHStPeFzfVIEwI",
        "b_skip": "CAADBAAD_xEAAgZFmVFMRA1J8Y1gxAI",
        "y_0": "CAADBAAD7xAAAqjjmFHnCu7eKJvSBgI",
        "y_1": "CAADBAADJQwAAp6tmFE2zDPVMieQ2QI",
        "y_2": "CAADBAADNA4AAl2mmVFpQOxJ41gk_gI",
        "y_3": "CAADBAAD3A4AAsxPmFGyZFv42UlxAQI",
        "y_4": "CAADBAADwg8AAm88kVEc9HZpl2gmzQI",
        "y_5": "CAADBAAD5hIAAkQ6mFHS-aGVuYZAnAI",
        "y_6": "CAADBAADvQ8AAs3RmVHVkVBfEF7eIwI",
        "y_7": "CAADBAAD1gwAAjlbmFGGH6rBdqP8QQI",
        "y_8": "CAADBAADbg8AAqvXkVH1ESeZFcGVrgI",
        "y_9": "CAADBAADOQ8AAnjokVG96pmCP7aZ3AI",
        "y_draw": "CAADBAAD6w4AAgsJmVETUteFwqTVJgI",
        "y_reverse": "CAADBAADtg8AAqiFmFFwothyN9TrXwI",
        "y_skip": "CAADBAADSxEAAhcSmFGu_F5LffmsZgI",
    },
}

STICKERS_OPTIONS = {
    "option_draw": "BQADBAAD-AIAAl9XmQABxEjEcFM-VHIC",
    "option_pass": "BQADBAAD-gIAAl9XmQABcEkAAbaZ4SicAg",
    "option_bluff": "BQADBAADygIAAl9XmQABJoLfB9ntI2UC",
    "option_info": "BQADBAADxAIAAl9XmQABC5v3Z77VLfEC",
}

# TODO: Support multiple card packs
# For now, just use classic colorblind
STICKERS = {
    **CARDS_CLASSIC_COLORBLIND["normal"],
    **STICKERS_OPTIONS,
}

STICKERS_GREY = {
    **CARDS_CLASSIC_COLORBLIND["not_playable"],
}


def sticker_unique_id(file_id):
    """Returns the stable ``file_unique_id`` for a Telegram sticker ``file_id``.

    The same sticker gets a different ``file_id`` when it is sent through
    inline mode, but its ``file_unique_id`` never changes. Deriving it from the
    ids stored in this file lets the bot recognise played cards. Returns None
    for ids it cannot decode (such as the old style option stickers).
    """
    import base64
    import struct

    try:
        raw = base64.urlsafe_b64decode(file_id + "=" * (-len(file_id) % 4))
        data = bytearray()
        i = 0
        while i < len(raw):  # Telegram run-length encodes zero bytes
            if raw[i] == 0:
                data += b"\x00" * raw[i + 1]
                i += 2
            else:
                data.append(raw[i])
                i += 1

        file_type = struct.unpack("<i", data[:4])[0]
        pos = 8
        if file_type & (1 << 25):  # a file reference comes before the id
            length = data[pos]
            if length >= 254:
                length = int.from_bytes(data[pos + 1:pos + 4], "little")
                header = 4
            else:
                header = 1
            pos += header + length + (-(header + length)) % 4
        doc_id = data[pos:pos + 8]
        if len(doc_id) != 8:
            return None

        unique = bytearray()
        zeros = 0
        for byte in struct.pack("<i", 2) + bytes(doc_id):
            if byte == 0:
                zeros += 1
            else:
                if zeros:
                    unique += bytes([0, zeros])
                    zeros = 0
                unique.append(byte)
        if zeros:
            unique += bytes([0, zeros])
        return base64.urlsafe_b64encode(bytes(unique)).decode().rstrip("=")
    except Exception:
        return None


class Card(object):
    """This class represents an UNO card"""

    def __init__(self, color, value, special=None):
        self.color = color
        self.value = value
        self.special = special

    def __str__(self):
        if self.special:
            return self.special
        else:
            return '%s_%s' % (self.color, self.value)

    def __repr__(self):
        if self.special:
            return '%s%s%s' % (COLOR_ICONS.get(self.color, ''),
                               COLOR_ICONS[BLACK],
                               ' '.join([s.capitalize()
                                         for s in self.special.split('_')]))
        else:
            return '%s%s' % (COLOR_ICONS[self.color], self.value.capitalize())

    def __eq__(self, other):
        """Needed for sorting the cards"""
        return str(self) == str(other)

    def __lt__(self, other):
        """Needed for sorting the cards"""
        return str(self) < str(other)


def from_str(string):
    """Decodes a Card object from a string"""
    if string not in SPECIALS:
        color, value = string.split('_')
        return Card(color, value)
    else:
        return Card(None, None, string)

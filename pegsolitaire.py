#!/usr/bin/env python3
"""pegsolitaire - 英式孔明棋(English peg solitaire),纯标准库。

7x7 十字棋盘,中央留空。跳过相邻棋子落到空位,吃掉被跳过的棋子。
目标:最后只剩一颗棋子。
"""

import argparse
import random
import sys

SIZE = 7
DIRS = ((2, 0), (-2, 0), (0, 2), (0, -2))


def valid_cell(r, c):
    """英式棋盘有效格:(r,c) 在 0..6 范围内,且行或列落在中间三条。"""
    return 0 <= r < SIZE and 0 <= c < SIZE and (2 <= r <= 4 or 2 <= c <= 4)


def parse_coord(text):
    """'D4' -> (r, c)。非法抛 ValueError。"""
    t = text.strip().upper()
    if len(t) != 2 or not ("A" <= t[0] <= "G") or not ("1" <= t[1] <= "7"):
        raise ValueError(f"坐标无效: {text!r},应为 A1..G7 格式")
    c, r = ord(t[0]) - ord("A"), int(t[1]) - 1
    if not valid_cell(r, c):
        raise ValueError(f"坐标 {t} 不在棋盘上")
    return r, c


def to_coord(r, c):
    return f"{chr(ord('A') + c)}{r + 1}"


class Board:
    def __init__(self):
        self.grid = [[None] * SIZE for _ in range(SIZE)]
        for r in range(SIZE):
            for c in range(SIZE):
                if valid_cell(r, c):
                    self.grid[r][c] = True  # True=有子, False=空, None=无效格
        self.grid[3][3] = False  # 中央留空
        self.history = []  # undo 栈: (from, mid, to)
        self.moves = 0

    def pegs(self):
        return sum(cell is True for row in self.grid for cell in row)

    def can_move(self, fr, to):
        r1, c1 = fr
        r2, c2 = to
        if not (valid_cell(r1, c1) and valid_cell(r2, c2)):
            return False
        dr, dc = r2 - r1, c2 - c1
        if (dr, dc) not in DIRS:
            return False
        mid = (r1 + dr // 2, c1 + dc // 2)
        return (self.grid[r1][c1] is True and self.grid[mid[0]][mid[1]] is True
                and self.grid[r2][c2] is False)

    def do_move(self, fr, to):
        """合法走子返回 True,否则 False。"""
        if not self.can_move(fr, to):
            return False
        r1, c1 = fr
        r2, c2 = to
        mid = ((r1 + r2) // 2, (c1 + c2) // 2)
        self.grid[r1][c1] = False
        self.grid[mid[0]][mid[1]] = False
        self.grid[r2][c2] = True
        self.history.append((fr, mid, to))
        self.moves += 1
        return True

    def undo(self):
        if not self.history:
            return False
        fr, mid, to = self.history.pop()
        self.grid[fr[0]][fr[1]] = True
        self.grid[mid[0]][mid[1]] = True
        self.grid[to[0]][to[1]] = False
        self.moves -= 1
        return True

    def any_moves(self):
        for r in range(SIZE):
            for c in range(SIZE):
                if self.grid[r][c] is True:
                    for dr, dc in DIRS:
                        if self.can_move((r, c), (r + dr, c + dc)):
                            return True
        return False

    def render(self):
        lines = ["    " + " ".join(chr(ord("A") + c) for c in range(SIZE))]
        for r in range(SIZE):
            row = [f"{r + 1}  "]
            for c in range(SIZE):
                cell = self.grid[r][c]
                row.append("●" if cell is True else ("·" if cell is False else " "))
            lines.append(" ".join(row))
        return "\n".join(lines)


# 演示解法:31 步标准解(英式棋盘,中央开局中央收官),由离线程序逐一验证合法。
# 记谱来源为公开发表的经典解法,已用本程序引擎校验:31 步全部合法、终局剩 1 子。
DEMO_MOVES = [
    "D2 D4", "F3 D3", "E1 E3", "E4 E2", "E6 E4", "G5 E5", "D5 F5",
    "G3 G5", "G5 E5",
    "C3 E3", "A3 C3",
    "B5 D5", "D5 F5", "F5 F3", "F3 D3", "D3 B3",
    "C7 C5", "C4 C6",
    "E7 C7", "C7 C5",
    "A5 A3", "A3 C3",
    "C1 E1", "E1 E3", "E3 E5",
    "C2 C4", "C4 C6", "C6 E6", "E6 E4", "E4 C4",
    "B4 D4",
]


def play_demo():
    board = Board()
    for i, text in enumerate(DEMO_MOVES, 1):
        fr_s, to_s = text.split()
        ok = board.do_move(parse_coord(fr_s), parse_coord(to_s))
        if not ok:
            print(f"演示解法第 {i} 步非法: {text}", file=sys.stderr)
            return 1
    print(board.render())
    n = board.pegs()
    print(f"\n演示结束:共 {board.moves} 步,剩余 {n} 颗棋子。")
    if n == 1:
        print("🎉 完美!只剩一颗棋子。")
        return 0
    print("演示解法未达到单子终局。", file=sys.stderr)
    return 1


def play_interactive():
    board = Board()
    print("孔明棋(英式):跳过相邻棋子落到空位,吃掉被跳过的棋子。")
    print("输入如 'D4 D6',u 悔棋,q 退出。目标:只剩一颗棋子。\n")
    while True:
        print(board.render())
        print(f"\n剩余 {board.pegs()} 子,已走 {board.moves} 步")
        if board.pegs() == 1:
            print("🎉 完美!只剩一颗棋子,你赢了!")
            return 0
        if not board.any_moves():
            print("无棋可走,游戏结束。")
            return 0
        try:
            cmd = input("> ").strip()
        except EOFError:
            print("\n再见。")
            return 0
        if not cmd:
            continue
        if cmd.lower() == "q":
            print("再见。")
            return 0
        if cmd.lower() == "u":
            print("已悔棋。" if board.undo() else "没有可悔的棋。")
            continue
        parts = cmd.split()
        if len(parts) != 2:
            print("格式不对,示例: D4 D6")
            continue
        try:
            fr, to = parse_coord(parts[0]), parse_coord(parts[1])
        except ValueError as e:
            print(e)
            continue
        if not board.do_move(fr, to):
            print("这步不合法:需要跳过一颗相邻棋子落到空位。")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pegsolitaire", description="英式孔明棋(终端版)")
    ap.add_argument("--demo", action="store_true", help="播放 31 步标准解法演示")
    ap.add_argument("--seed", type=int, default=None, help="保留参数(当前版本未使用)")
    args = ap.parse_args(argv)
    if args.demo:
        return play_demo()
    return play_interactive()


if __name__ == "__main__":
    raise SystemExit(main())

/**
 * The eight "Tarot Groups" of the Tarot Instruction's last lesson (the
 * Second Section's Supplement 1), the data behind the format's
 * <TarotGroups /> tag: the print renderer draws the tableau from it
 * (render.ts), and a site's web component imports it from here, so the two
 * can never disagree.
 *
 * The 112 nine-Key combinations fall into eight groups of fourteen. Each
 * group is one of the eight symmetries of the square (the dihedral group D4)
 * applied to a basic 3x3 arrangement of nine consecutive Keys. Grid k
 * (k = 1..14) holds the nine consecutive numbers k-1 .. k+7; the offset
 * matrix for each group fixes which of those numbers sits in each cell.
 * Deriving the grids rather than transcribing them keeps every one of the
 * 112 arrangements provably correct (the printed tables are the source of
 * truth and were verified against these).
 */

export type TarotGroup = {
  name: string;
  offsets: readonly (readonly number[])[];
};

/** Grids per group, k = 1..14. */
export const TAROT_GRIDS_PER_GROUP = 14;

export const TAROT_GROUPS: readonly TarotGroup[] = [
  {
    name: "First Group",
    offsets: [
      [-1, 0, 1],
      [2, 3, 4],
      [5, 6, 7],
    ],
  },
  {
    name: "Second Group",
    offsets: [
      [1, 0, -1],
      [4, 3, 2],
      [7, 6, 5],
    ],
  },
  {
    name: "Third Group",
    offsets: [
      [-1, 2, 5],
      [0, 3, 6],
      [1, 4, 7],
    ],
  },
  {
    name: "Fourth Group",
    offsets: [
      [5, 2, -1],
      [6, 3, 0],
      [7, 4, 1],
    ],
  },
  {
    name: "Fifth Group",
    offsets: [
      [5, 6, 7],
      [2, 3, 4],
      [-1, 0, 1],
    ],
  },
  {
    name: "Sixth Group",
    offsets: [
      [7, 6, 5],
      [4, 3, 2],
      [1, 0, -1],
    ],
  },
  {
    name: "Seventh Group",
    offsets: [
      [7, 4, 1],
      [6, 3, 0],
      [5, 2, -1],
    ],
  },
  {
    name: "Eighth Group",
    offsets: [
      [1, 4, 7],
      [0, 3, 6],
      [-1, 2, 5],
    ],
  },
];

/** The nine Key numbers of grid `k` in a group, row by row. */
export function tarotGridNumbers(group: TarotGroup, k: number): number[] {
  return group.offsets.flatMap((row) => row.map((offset) => k + offset));
}

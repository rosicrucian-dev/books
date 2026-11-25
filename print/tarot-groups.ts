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
  /** Its place in the series: "First" … "Eighth". */
  ordinal: string;
  offsets: readonly (readonly number[])[];
};

/**
 * What one of the eight is CALLED, which is not the same in every
 * edition that prints these tables. The School of Ageless Wisdom's
 * Second Section, Supplement 1 calls them groups — "The 112
 * combinations fall into eight groups of 14 combinations each" — and
 * B.O.T.A.'s Tarot Interpretation lesson 31 calls the same eight sets
 * CLASSES, heading them FIRST CLASS … EIGHTH CLASS.
 *
 * The tables themselves are the same 112 arrangements in the same
 * order (lesson 31's transcription was checked against these offsets:
 * every one of the 112 agrees). Each edition keeps its own word and
 * neither is modernised into the other, so the tag takes the noun:
 * `<TarotGroups />`, `<TarotGroups unit="Class" />`.
 */
export const TAROT_UNIT = "Group";

export function tarotGroupLabel(group: TarotGroup, unit = TAROT_UNIT): string {
  return `${group.ordinal} ${unit}`;
}

/** Grids per group, k = 1..14. */
export const TAROT_GRIDS_PER_GROUP = 14;

export const TAROT_GROUPS: readonly TarotGroup[] = [
  {
    ordinal: "First",
    offsets: [
      [-1, 0, 1],
      [2, 3, 4],
      [5, 6, 7],
    ],
  },
  {
    ordinal: "Second",
    offsets: [
      [1, 0, -1],
      [4, 3, 2],
      [7, 6, 5],
    ],
  },
  {
    ordinal: "Third",
    offsets: [
      [-1, 2, 5],
      [0, 3, 6],
      [1, 4, 7],
    ],
  },
  {
    ordinal: "Fourth",
    offsets: [
      [5, 2, -1],
      [6, 3, 0],
      [7, 4, 1],
    ],
  },
  {
    ordinal: "Fifth",
    offsets: [
      [5, 6, 7],
      [2, 3, 4],
      [-1, 0, 1],
    ],
  },
  {
    ordinal: "Sixth",
    offsets: [
      [7, 6, 5],
      [4, 3, 2],
      [1, 0, -1],
    ],
  },
  {
    ordinal: "Seventh",
    offsets: [
      [7, 4, 1],
      [6, 3, 0],
      [5, 2, -1],
    ],
  },
  {
    ordinal: "Eighth",
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

#!/usr/bin/env python3
"""TEMPLATE: copy to <generators>/tables/table_<table_name>.py and replace the example data."""

from __future__ import annotations

import csv
import io

from paper_kit import tables

TABLE_NAME = "example_table"
SOURCE = "the example data in this template"

# Replace with: csv.DictReader(open(CSV_PATH, encoding="utf-8")), where CSV_PATH is a constant.
EXAMPLE_CSV = "case,error,runtime_s\ncase_a,0.0123,1.5\ncase_b,0.00001,20.25\ncase_c,nan,3.0\n"

FILTERS = {}  # column -> required value
SORT_BY = "case"

# Heading, source column and cell formatter. This list is the layout of the table.
COLUMNS = [
    ("Case", "case", tables.tex_wrap),
    ("Error (-)", "error", tables.num_or_sci),
    (r"Runtime (s)", "runtime_s", lambda value: tables.num(value, 1)),
]


def main() -> None:
    rows = list(csv.DictReader(io.StringIO(EXAMPLE_CSV)))
    tables.require_columns(rows[0], [*FILTERS, SORT_BY, *(column for _, column, _ in COLUMNS)])
    rows = [row for row in rows if all(row[key] == value for key, value in FILTERS.items())]
    rows.sort(key=lambda row: row[SORT_BY])

    lines = [
        tables.provenance(__file__, SOURCE),
        r"\begin{table}[tbp]",
        r"\caption{Example results per case. A dash marks a case without a value.}",
        rf"\label{{tab:{TABLE_NAME}}}",
        r"\centering",
        rf"\begin{{tabular}}{{l{'r' * (len(COLUMNS) - 1)}}}",
        r"\hline",
        tables.row_line(heading for heading, _, _ in COLUMNS),
        r"\hline",
        *(tables.row_line(fmt(row[column]) for _, column, fmt in COLUMNS) for row in rows),
        r"\hline",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ]
    tables.save("\n".join(lines), TABLE_NAME)


if __name__ == "__main__":
    main()

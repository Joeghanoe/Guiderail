#!/usr/bin/env python3
"""Build a business end-to-end test plan (.xlsx) that follows the process, from a JSON spec.

For a project manager or business owner who runs or signs off an end-to-end test. One sheet, laid out like a
process walk-through: scenarios, each split into stages, each stage a few steps. Per step: the status in two
systems, who acts, a time target, what must be seen, and cells for the tester (time, result, remarks).
The playbook playbooks/write-business-test-plan.md says what to put in the spec.

Input:  a spec (see templates/business-testplan.spec.json)
          title, process (one line), systems [header A, header B], reference and example (optional lines),
          scenarios[ id, title, stages[ title, steps[ who, step, status_a, status_b, target, expected ] ] ]
        Per step only `who` and `step` are required.
Output: the workbook. Exit 1 with one line per problem when the spec is incomplete; exit 2 without openpyxl.
        The result counter at the bottom is a formula; Excel calculates it when the file opens.

Example:
  python3 tools/testing/business-testplan.py templates/business-testplan.spec.json plan.xlsx
"""

import json
import sys

try:
    from openpyxl import Workbook
    from openpyxl.formatting.rule import CellIsRule
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
except ImportError:
    print("business-testplan.py needs openpyxl: python3 -m venv .venv && .venv/bin/pip install openpyxl", file=sys.stderr)
    sys.exit(2)

FONT = "Arial"
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
INPUT = "FFF8DC"
WIDTH = [4, 60, 14, 18, 17, 12, 58, 10, 10, 44]
CENTER = (1, 3, 4, 6, 8, 9)
INPUT_COLS = (8, 9, 10)
RESULT_COL = 9
HEADER_ROW = 7


def font(bold=False, size=10, color="000000", italic=False):
    return Font(name=FONT, size=size, bold=bold, color=color, italic=italic)


def fill(color):
    return PatternFill("solid", start_color=color, end_color=color)


def problems(spec):
    found = []
    for key in ("title", "systems", "scenarios"):
        if not spec.get(key):
            found.append(f"missing '{key}'")
    if len(spec.get("systems") or []) != 2:
        found.append("'systems' needs exactly two names (the status columns)")
    for scenario in spec.get("scenarios") or []:
        label = f"scenario {scenario.get('id', '?')}"
        if not scenario.get("title") or not scenario.get("stages"):
            found.append(f"{label}: needs a title and stages")
        for stage in scenario.get("stages") or []:
            if not stage.get("title") or not stage.get("steps"):
                found.append(f"{label}: every stage needs a title and steps")
            for step in stage.get("steps") or []:
                if not step.get("who") or not step.get("step"):
                    found.append(f"{label}, stage '{stage.get('title', '?')}': every step needs 'who' and 'step'")
    return found


def band(ws, row, color, marker, text, size, height):
    for col in range(1, len(WIDTH) + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill, cell.border = fill(color), BORDER
    cell = ws.cell(row=row, column=1, value=marker)
    cell.font = font(True, 16 if size == 11 and marker not in ("•",) else 11)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell = ws.cell(row=row, column=2, value=text)
    cell.font = font(True, size)
    cell.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[row].height = height


def build(spec, out_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Testplan"
    ws.sheet_view.showGridLines = False
    for col, width in enumerate(WIDTH, 1):
        ws.column_dimensions[get_column_letter(col)].width = width

    ws["B1"] = spec["title"]
    ws["B1"].font = font(True, 16, "1F3864")
    lines = [spec.get("process", ""),
             "Fill in the yellow cells: Time, Result and Remarks. Pick OK or NOK in Result. "
             "Example:   " + spec.get("example", "13:15  |  OK  |  Order 1042 created in the order system"),
             None, spec.get("reference", "")]
    for row, text in zip((2, 3, 4, 5), lines):
        if text is not None:
            ws[f"B{row}"] = text
            ws[f"B{row}"].font = font(italic=True, color="595959")
    ws["B4"] = "Environment:"
    ws["B4"].font = font(True)
    ws["G4"] = "Tester / date:"
    ws["G4"].font = font(True)
    for col in ("C", "D", "E", "F", "H", "I", "J"):
        ws[f"{col}4"].fill = fill(INPUT)

    headers = ["", "Process step", spec["systems"][0], spec["systems"][1], "Who acts", "Time target",
               "What you should see", "Time", "Result", "Remarks"]
    for col, text in enumerate(headers, 1):
        cell = ws.cell(row=HEADER_ROW, column=col, value=text)
        cell.font = font(True, 10, "FFFFFF")
        cell.fill, cell.border = fill("1F3864"), BORDER
        cell.alignment = Alignment(vertical="center", wrap_text=True, horizontal="center" if col in CENTER else None)
    ws.freeze_panes = ws.cell(row=HEADER_ROW + 1, column=3)

    row = first = HEADER_ROW + 1
    steps = 0
    for scenario in spec["scenarios"]:
        band(ws, row, "BDD0EA", scenario["id"], scenario["title"], 11, 28)
        row += 1
        for stage in scenario["stages"]:
            band(ws, row, "E8EEF8", "•", stage["title"], 10, 20)
            row += 1
            for step in stage["steps"]:
                values = ["o", step["step"], step.get("status_a", ""), step.get("status_b", ""), step["who"],
                          step.get("target", ""), step.get("expected", ""), "", "", ""]
                for col, value in enumerate(values, 1):
                    cell = ws.cell(row=row, column=col, value=value)
                    cell.font = font()
                    cell.border = BORDER
                    cell.alignment = Alignment(wrap_text=True, vertical="top", horizontal="center" if col in CENTER else None)
                    if col in INPUT_COLS:
                        cell.fill = fill(INPUT)
                # Wrapped text does not auto-size rows when the file is written, so estimate the lines needed.
                needed = max(-(-len(values[1]) // 62), -(-len(values[6]) // 60), 1)
                ws.row_dimensions[row].height = max(28, 13.5 * needed)
                row += 1
                steps += 1
        row += 1
    last = row

    column = get_column_letter(RESULT_COL)
    validation = DataValidation(type="list", formula1='"OK,NOK"', allow_blank=True)
    ws.add_data_validation(validation)
    validation.add(f"{column}{first}:{column}{last}")
    for value, color in (("OK", "C6EFCE"), ("NOK", "FFC7CE")):
        ws.conditional_formatting.add(f"{column}{first}:{column}{last}",
                                      CellIsRule(operator="equal", formula=[f'"{value}"'], fill=fill(color)))

    ws.cell(row=last + 1, column=2, value="Result so far").font = font(True)
    counters = (("OK", f'=COUNTIF({column}{first}:{column}{last},"OK")'),
                ("NOK", f'=COUNTIF({column}{first}:{column}{last},"NOK")'),
                ("Not done", f'=COUNTIF(A{first}:A{last},"o")-D{last + 1}-D{last + 2}'))
    for offset, (label, formula) in enumerate(counters, 1):
        ws.cell(row=last + offset, column=3, value=label).font = font(True)
        ws.cell(row=last + offset, column=4, value=formula).font = font(True)

    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = f"{HEADER_ROW}:{HEADER_ROW}"
    wb.calculation.fullCalcOnLoad = True
    wb.save(out_path)
    print(f"{out_path}: {len(spec['scenarios'])} scenarios, {steps} steps")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    with open(sys.argv[1], encoding="utf-8") as handle:
        spec = json.load(handle)
    found = problems(spec)
    if found:
        print("\n".join(f"business-testplan: {line}" for line in found), file=sys.stderr)
        sys.exit(1)
    build(spec, sys.argv[2])


if __name__ == "__main__":
    main()

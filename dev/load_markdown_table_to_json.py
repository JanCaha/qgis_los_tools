from pathlib import Path


def extract_table(file: Path) -> dict:

    table = []

    previous_line_table = False

    with open(file) as f:

        for line in f.readlines():

            current_line_table = line.startswith("|")

            if current_line_table:
                table.append(line.split("|"))
                previous_line_table = True

            if previous_line_table and not current_line_table:
                break

    table = table[2:]

    data = {}

    for l in table:
        data.update({l[2].strip().replace("`", ""): l[4].strip()})

    return data


folder = Path(__file__).parent.parent / "website" / "pages"

file = folder / "tools" / "Export to table" / "tool_export_los.md"

print(extract_table(file))

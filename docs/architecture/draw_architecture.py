"""
Draw the architecture diagram with official AWS icons (no extra Python packages needed).

    python3 docs/architecture/draw_architecture.py

Writes docs/architecture/architecture.svg, then architecture.png using Google Chrome (if installed).
To change the picture: edit the NODES / GROUPS / ARROWS lists below, then rerun.
  - NODES:  x, y = centre of the icon
  - ARROWS: a list of corner points; the arrow is drawn through them with right angles
Icons in icons/ are the AWS Architecture Icons (as bundled in the open-source `diagrams` package).
"""
import base64
import pathlib
import shutil
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
WIDTH, HEIGHT = 1680, 810
ICON = 64                                   # icon size in px
FONT = "Helvetica, Arial, sans-serif"
ROW1, ROW2, ROW3 = 170, 440, 690            # y of the three rows

# (x, y, width, height, title, border colour, title at "top" or "bottom")  -- AWS category colours
GROUPS = [
    (20, 60, 230, 730, "Deploy as code", "#545b64", "top"),
    (290, 20, 1370, 780, "AWS Cloud · us-east-2", "#232f3e", "top"),
    (310, 330, 170, 230, "Infra as code", "#e7157b", "top"),
    (510, 70, 860, 200, "Glue Workflow · one trigger", "#8c4fff", "top"),
    (740, 330, 630, 230, "Amazon S3 · one bucket · Block Public Access", "#7aa116", "bottom"),
    (1400, 70, 240, 490, "Catalog + analytics", "#8c4fff", "bottom"),
    (510, 610, 680, 175, "Monitoring · failure alerts", "#e7157b", "bottom"),
    (1230, 610, 410, 175, "Security", "#dd344c", "top"),
]

# name: (icon file or None for a start circle, x, y, bold label, small label)
NODES = {
    "github":    ("github.png", 135, 200, "GitHub repo", "pipeline as code"),
    "python":    ("python.png", 135, 440, "Python scripts (boto3)", "deploy · run · teardown"),
    "cfn":       ("cloudformation.png", 395, ROW2, "AWS CloudFormation", "creates every resource"),
    "start":     (None, 610, ROW1, "Start trigger", "run.py or daily schedule"),
    "crawler":   ("glue-crawler.png", 830, ROW1, "Glue Crawler", "detects CSV schema"),
    "job":       ("glue.png", 1050, ROW1, "Glue ETL job", "PySpark · ~40 DQ checks"),
    "raw":       ("s3-bucket.png", 830, ROW2, "Raw/sales/", "24 CSVs · read-only"),
    "dq":        ("s3-bucket.png", 1050, ROW2, "data-quality/", "run reports · rejected rows"),
    "processed": ("s3-bucket.png", 1270, ROW2, "processed/sales/", "Parquet · by month"),
    "catalog":   ("glue-data-catalog.png", 1520, ROW1, "Glue Data Catalog", "sales · sales_processed"),
    "athena":    ("athena.png", 1520, ROW2, "Amazon Athena", "SQL E1–E8"),
    "eb":        ("eventbridge-rule.png", 610, ROW3, "EventBridge rule", "job / crawler failed"),
    "sns":       ("sns-topic.png", 830, ROW3, "SNS topic", "dunkin-pipeline-alerts"),
    "email":     ("email.png", 1050, ROW3, "Email alert", ""),
    "iam":       ("iam-role.png", 1435, ROW3, "IAM role (least privilege)", "read Raw · write processed, DQ"),
}

# (corner points, label, label position, style)   style: solid | dashed
ARROWS = [
    ([(135, 276), (135, 398)], "", None, "solid"),                                     # GitHub -> scripts
    ([(180, 460), (361, 460)], "deploy.py", (214, 460), "solid"),                      # scripts -> CloudFormation
    ([(175, 420), (270, 420), (270, ROW1), (572, ROW1)], "run.py", (420, ROW1), "dashed"),  # scripts -> start

    ([(650, ROW1), (788, ROW1)], "", None, "solid"),                                   # start -> crawler
    ([(870, ROW1), (1008, ROW1)], "on success", (939, ROW1), "solid"),                 # crawler -> job
    ([(830, 246), (830, 398)], "scans", (830, 300), "solid"),                          # crawler -> raw
    ([(870, ROW2), (940, ROW2), (940, 195), (1008, 195)], "reads", (940, 300), "solid"),  # raw -> job
    ([(1050, 246), (1050, 398)], "DQ report", (1050, 300), "solid"),                   # job -> data-quality
    ([(1090, ROW1), (1270, ROW1), (1270, 398)], "clean rows", (1180, ROW1), "solid"),  # job -> processed
    ([(830, 128), (830, 52), (1520, 52), (1520, 128)], "registers table: sales", (1180, 52), "solid"),
    ([(1310, ROW2), (1478, ROW2)], "query data", (1394, ROW2), "solid"),               # processed -> Athena
    ([(1520, 246), (1520, 398)], "table schemas", (1520, 320), "solid"),               # catalog -> Athena

    ([(610, 270), (610, 648)], "FAILED · TIMEOUT · STOPPED", (610, 460), "dashed"),   # workflow -> EventBridge
    ([(650, ROW3), (788, ROW3)], "", None, "solid"),
    ([(870, ROW3), (1008, ROW3)], "", None, "solid"),
]


def icon_data(file):
    return "data:image/png;base64," + base64.b64encode((HERE / "icons" / file).read_bytes()).decode()


def text(x, y, value, size=13, weight="normal", anchor="middle", colour="#16191f"):
    value = value.replace("&", "&amp;").replace("<", "&lt;")
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{colour}">{value}</text>')


def backing(x, y, width, height):
    """White rectangle behind text, so no line ever runs through it."""
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="#ffffff"/>'


def draw():
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
             '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
             'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#545b64"/></marker></defs>',
             f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>']

    group_titles = []                                   # drawn last, so no line crosses them
    for x, y, w, h, title, colour, place in GROUPS:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="none" '
                     f'stroke="{colour}" stroke-width="1.6"/>')
        ty = y + 20 if place == "top" else y + h - 10
        group_titles.append(backing(x + 8, ty - 14, len(title) * 7.6 + 8, 19))
        group_titles.append(text(x + 12, ty, title, size=13, weight="bold", anchor="start", colour=colour))

    for points, label, label_at, style in ARROWS:
        dash = ' stroke-dasharray="6,5"' if style == "dashed" else ""
        path = "M" + " L".join(f"{x},{y}" for x, y in points)
        parts.append(f'<path d="{path}" fill="none" stroke="#545b64" stroke-width="1.6"{dash} '
                     f'stroke-linejoin="round" marker-end="url(#arrow)"/>')
        if label:
            lx, ly = label_at
            width = len(label) * 6.4 + 10
            parts.append(backing(lx - width / 2, ly - 9, width, 17))
            parts.append(text(lx, ly + 4, label, size=11, colour="#545b64"))

    for icon, x, y, title, subtitle in NODES.values():
        if icon:
            parts.append(f'<image href="{icon_data(icon)}" x="{x - ICON / 2}" y="{y - ICON / 2}" width="{ICON}" height="{ICON}"/>')
        else:
            parts.append(f'<circle cx="{x}" cy="{y}" r="{ICON / 2 - 2}" fill="#8c4fff"/>')
            parts.append(f'<path d="M{x - 8},{y - 13} L{x + 14},{y} L{x - 8},{y + 13} z" fill="#ffffff"/>')
        for line, char_width, top, height in ((title, 7.6, 5, 17), (subtitle, 6.2, 23, 15)):
            if line:
                width = len(line) * char_width + 6
                parts.append(backing(x - width / 2, y + ICON / 2 + top, width, height))
        parts.append(text(x, y + ICON / 2 + 18, title, weight="bold"))
        if subtitle:
            parts.append(text(x, y + ICON / 2 + 34, subtitle, size=11.5, colour="#545b64"))

    parts.extend(group_titles)
    parts.append("</svg>")
    svg_file = HERE / "architecture.svg"
    svg_file.write_text("\n".join(parts))
    print(f"wrote {svg_file}")
    return svg_file


def to_png(svg_file):
    chrome = shutil.which("google-chrome") or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if not pathlib.Path(chrome).exists():
        print("Chrome not found: open architecture.svg in a browser and save it as PNG instead.")
        return
    png_file = HERE / "architecture.png"
    subprocess.run([chrome, "--headless", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                    f"--window-size={WIDTH},{HEIGHT}", f"--screenshot={png_file}", svg_file.as_uri()],
                   check=True, capture_output=True)
    print(f"wrote {png_file}")


if __name__ == "__main__":
    to_png(draw())

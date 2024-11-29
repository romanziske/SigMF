import json
import subprocess

from pylatex import (Command, Document, Figure, Package, Section, Subsection,
                     Subsubsection, Tabular)
from pylatex.utils import NoEscape, bold

with open("sigmf-schema.json", "r") as f:
    data = json.load(f)
with open("collection-schema.json", "r") as f:
    data_collection = json.load(f)
with open("extensions/antenna-schema.json", "r") as f:
    data_antenna = json.load(f)
with open("extensions/capture-detail-schema.json", "r") as f:
    data_capture_detail = json.load(f)
with open("extensions/signal-schema.json", "r") as f:
    data_signal = json.load(f)
with open("extensions/spatial-schema.json", "r") as f:
    data_spatial = json.load(f)
with open("extensions/traceability-schema.json", "r") as f:
    data_traceability = json.load(f)

sigmf_version = data["$id"].split("/")[-2]
print("SigMF Version: " + sigmf_version)


USED_LABELS = set()


def make_unique_label(prefix, text):
    """Generate unique label for LaTeX references"""
    base = f"{prefix}_{text.lower().replace(':', '_').replace(' ', '_')}"
    if base not in USED_LABELS:
        USED_LABELS.add(base)
        return base

    counter = 1
    while f"{base}_{counter}" in USED_LABELS:
        counter += 1
    label = f"{base}_{counter}"
    USED_LABELS.add(label)
    return label


def add_code_tags(text):  # swaps every pair of ` ` for \code{}
    # need to escape underscores when inside a command
    text = text.replace("_", "\\_")
    while text.find("`") != -1:
        text = text.replace("`", "\\code{", 1)
        text = text.replace("`", "}", 1)
    return text


def gen_table(table, d):
    table.append(NoEscape("\\toprule"))
    table.add_row((bold("Field"), bold("Required"),
                  bold("Type"), bold("Short Description")))
    table.append(NoEscape("\\midrule"))
    for key, value in d["properties"].items():
        field = key.replace("core:", "")
        required = "Required" if key in d.get("required", {}) else ""
        dtype = value.get("type", "MISSING")
        # default = str(value.get("default", ""))
        longdescription = value.get("description", "")
        shortdescription = longdescription[: longdescription.find(".")].replace(
            "\n", "")  # short description, which is up to the first period
        table.add_row((field, required, dtype, shortdescription))
    table.append(NoEscape("\\bottomrule"))


def gen_fields(doc, d, prefix=""):
    """Generate fields with unique labels"""
    for key, value in d["properties"].items():
        clean_key = key.replace("core:", "").replace(
            "signal:", "").replace("capture_details:", "")
        label = make_unique_label(prefix, clean_key)

        with doc.create(Subsubsection(clean_key)):
            doc.append(NoEscape(f"\\label{{ssubsec:{label}}}"))
            if "description" in value:
                doc.append(NoEscape(add_code_tags(value["description"])))
            for key2, value2 in d["properties"][key].items():
                if key2 not in ["$id", "description", "items", "additionalItems", "pattern"]:
                    doc.append("\n")
                    doc.append(bold(key2))
                    doc.append(": ")
                    doc.append(str(value2))


geometry_options = {"tmargin": "1in", "lmargin": "1in",
                    "rmargin": "1in", "bmargin": "1in"}
doc = Document(geometry_options=geometry_options)
# doesn't actually show up anywhere, but was causing a warning when not included
doc.preamble.append(Command("title", "SigMF"))
# makes it so _ never means math mode!
doc.packages.append(Package("underscore"))
# allows for \rowcolors
doc.packages.append(Package("xcolor", options=["table"]))
doc.packages.append(Package("listings"))
doc.packages.append(Package("microtype"))
doc.packages.append(Package("fancyhdr"))
doc.packages.append(Package("booktabs"))
doc.packages.append(Package("svg"))
doc.packages.append(
    Package("hyperref", options=[
            "hidelinks", "colorlinks=true", "urlcolor=blue", "linkcolor=black"])
)  # \usepackage[, urlcolor=blue, linkcolor=red]{hyperref}

# Colors
# for `short code`
doc.append(NoEscape("\\definecolor{mylightgray}{RGB}{240,240,240}"))
# for table rows
doc.append(NoEscape("\\definecolor{lightblue}{RGB}{240,240,255}"))

# Custom commands
doc.append(
    NoEscape("\\newcommand{\\code}[1]{\\texttt{\colorbox{mylightgray}{#1}}}")
)  # \\code{} displays using monospace font and light gray background
# \\nn gives a new line with space and no indent
doc.append(NoEscape("\\newcommand{\\nn}[0]{\\vspace{4mm}\\\\\\noindent}"))

# Footer
doc.append(NoEscape("\\pagestyle{fancy}"))
doc.append(NoEscape("\\fancyhf{}"))  # clear all header/footer fields
doc.append(NoEscape("\\renewcommand{\headrulewidth}{0pt}"))
doc.append(NoEscape("\\fancyfoot[LE,RO]{\\thepage}"))
doc.append(NoEscape(
    "\\fancyfoot[LO,CE]{\\footnotesize SigMF Specification Version " + sigmf_version + "}"))

with doc.create(Figure(position="h!")) as logo:
    doc.append(NoEscape("\\vspace{-0.8in}\\centering"))
    # doc.append(NoEscape('\\includesvg[width=200pt]{logo/sigmf\string_logo.svg}')) # Using SVG made PDF take a couple extra seconds to open...
    logo.add_image("logo/sigmf_logo.png", width="120px")
    doc.append(NoEscape("\\vspace{-0.3in}"))

with doc.create(Section("SigMF Specification Version " + sigmf_version)):
    with doc.create(Subsection("Abstract")):  # Abstract lives in the JSON Schema
        doc.append(data["description"])

    with doc.create(Subsection("Copyright Notice")):
        doc.append(
            NoEscape(
                "This document is available under the \href{http://creativecommons.org/licenses/by-sa/4.0/}{CC-BY-SA License}. Copyright of contributions to SigMF are retained by their original authors. All contributions under these terms are welcome."
            )
        )

    with doc.create(Subsection("Table of Contents")):
        doc.append(NoEscape(
            "\\vspace{-0.4in}\\def\\contentsname{\\empty}\\setcounter{tocdepth}{3}\\tableofcontents"))

    doc.append(NoEscape(add_code_tags(open("additional_content.md", "r").read(
    ).split("<<<<<<<<<<content from JSON schema>>>>>>>>>>>>")[0])))

    with doc.create(Subsection("Global Object")):
        doc.append(NoEscape(add_code_tags(
            data["properties"]["global"]["description"])))
        doc.append("\n\n")
        doc.append(NoEscape("\\rowcolors{1}{}{lightblue}"))
        with doc.create(Tabular("lllp{3.8in}")) as table:
            gen_table(table, data["properties"]["global"])
        gen_fields(doc, data["properties"]["global"])

    with doc.create(Subsection("Captures Array")):
        doc.append(NoEscape(add_code_tags(
            data["properties"]["captures"]["description"])))
        doc.append("\n\n")
        doc.append(NoEscape("\\rowcolors{1}{}{lightblue}"))
        with doc.create(Tabular("lllp{3.8in}")) as table:
            gen_table(table, data["properties"]
                      ["captures"]["items"]["anyOf"][0])
        gen_fields(doc, data["properties"]["captures"]["items"]["anyOf"][0])

    with doc.create(Subsection("Annotations Array")):
        doc.append(NoEscape(add_code_tags(
            data["properties"]["annotations"]["description"])))
        doc.append("\n\n")
        doc.append(NoEscape("\\rowcolors{1}{}{lightblue}"))
        with doc.create(Tabular("lllp{3.8in}")) as table:
            gen_table(table, data["properties"]
                      ["annotations"]["items"]["anyOf"][0])
        gen_fields(doc, data["properties"]["annotations"]["items"]["anyOf"][0])

    with doc.create(Subsection("SigMF Collection Format")):
        doc.append(NoEscape(add_code_tags(
            data_collection["properties"]["collection"]["description"])))
        doc.append("\n\n")
        doc.append(NoEscape("\\rowcolors{1}{}{lightblue}"))
        with doc.create(Tabular("lllp{3.8in}")) as table:
            gen_table(table, data_collection["properties"]["collection"])
        gen_fields(doc, data_collection["properties"]["collection"])

    doc.append(NoEscape(add_code_tags(open("additional_content.md", "r").read(
    ).split("<<<<<<<<<<content from JSON schema>>>>>>>>>>>>")[1])))

with doc.create(Section("Extensions")):
    with doc.create(Subsection("Antenna")):
        # Main description
        doc.append(NoEscape(add_code_tags(data_antenna["description"])))
        doc.append(NoEscape("\\vspace{4mm}\\par\\noindent"))

        # Global section
        doc.append(NoEscape(add_code_tags(
            data_antenna["properties"]["global"]["description"])))
        doc.append("\n\n")
        doc.append(NoEscape("\\rowcolors{1}{}{lightblue}"))
        with doc.create(Tabular("lllp{2.8in}")) as table:
            gen_table(table, data_antenna["properties"]["global"])
        gen_fields(doc, data_antenna["properties"]["global"])

        # Annotations section
        doc.append(NoEscape("\\nn"))
        doc.append(NoEscape(add_code_tags(
            data_antenna["properties"]["annotations"]["description"])))
        doc.append("\n\n")
        doc.append(NoEscape("\\rowcolors{1}{}{lightblue}"))
        with doc.create(Tabular("lllp{3.8in}")) as table:
            gen_table(table, data_antenna["properties"]
                      ["annotations"]["items"]["anyOf"][0])
        gen_fields(doc, data_antenna["properties"]
                   ["annotations"]["items"]["anyOf"][0])

        # Collection section
        doc.append(NoEscape("\\nn"))
        doc.append(NoEscape(add_code_tags(
            data_antenna["properties"]["collection"]["description"])))
        doc.append("\n\n")
        doc.append(NoEscape("\\rowcolors{1}{}{lightblue}"))
        with doc.create(Tabular("lllp{3.8in}")) as table:
            gen_table(table, data_antenna["properties"]["collection"])
        gen_fields(doc, data_antenna["properties"]["collection"])

    with doc.create(Subsection("Capture Detail")):
        # Main description
        doc.append(NoEscape(add_code_tags(data_capture_detail["description"])))
        doc.append(NoEscape("\\vspace{4mm}\\par\\noindent"))

        # Capture section
        doc.append(NoEscape(add_code_tags(
            data_capture_detail["properties"]["captures"]["description"])))
        doc.append("\n\n")
        doc.append(NoEscape("\\rowcolors{1}{}{lightblue}"))
        with doc.create(Tabular("lllp{2.8in}")) as table:
            gen_table(
                table, data_capture_detail["properties"]["captures"]["items"])
        gen_fields(doc, data_capture_detail["properties"]["captures"]["items"])

        # Annotations section
        doc.append(NoEscape(add_code_tags(
            data_capture_detail["properties"]["annotations"]["description"])))
        doc.append("\n\n")
        doc.append(NoEscape("\\rowcolors{1}{}{lightblue}"))
        with doc.create(Tabular("lllp{3.8in}")) as table:
            gen_table(table, data_capture_detail["properties"]
                      ["annotations"]["items"])
        gen_fields(doc, data_capture_detail["properties"]
                   ["annotations"]["items"])

    with doc.create(Subsection("Signal")):
        # Main description
        doc.append(NoEscape(add_code_tags(data_signal["description"])))
        doc.append(NoEscape("\\vspace{4mm}\\par\\noindent"))

        # Signal Detail section
        doc.append(NoEscape("Signal Detail Properties:"))
        doc.append(NoEscape(add_code_tags(
            data_signal["properties"]["annotations"]["description"])))
        doc.append("\n\n")
        doc.append(NoEscape("\\rowcolors{1}{}{lightblue}"))
        with doc.create(Tabular("lllp{2.8in}")) as table:
            gen_table(table, data_signal["properties"]["annotations"]
                      ["items"]["properties"]["signal:detail"])
        gen_fields(doc, data_signal["properties"]["annotations"]["items"]["properties"]["signal:detail"]
                   )

        # Signal Emitter section
        doc.append("\n\n")
        doc.append(NoEscape("Signal Emitter Properties:"))
        doc.append("\n\n")
        doc.append(NoEscape("\\rowcolors{1}{}{lightblue}"))
        with doc.create(Tabular("lllp{2.8in}")) as table:
            gen_table(
                table,
                data_signal["properties"]["annotations"]["items"]["properties"]["signal:emitter"]
            )
        gen_fields(
            doc,
            data_signal["properties"]["annotations"]["items"]["properties"]["signal:emitter"]
        )

    with doc.create(Subsection("Spatial")):
        # Main description
        doc.append(NoEscape(add_code_tags(data_spatial["description"])))
        doc.append(NoEscape("\\vspace{4mm}\\par\\noindent"))

        # Definitions section
        doc.append(Subsubsection("Definitions"))
        doc.append(NoEscape("\\vspace{2mm}\\par\\noindent"))

        # Bearing definition
        doc.append(NoEscape("\\textbf{Bearing Object}"))
        doc.append(NoEscape("\\vspace{2mm}\\par\\noindent"))
        with doc.create(Tabular("lllp{2.8in}")) as table:
            gen_table(table, data_spatial["$defs"]["bearing"])

        # Cartesian Point definition
        doc.append(NoEscape("\\vspace{2mm}\\par\\noindent"))
        doc.append(NoEscape("\\textbf{Cartesian Point Object}"))
        doc.append(NoEscape("\\vspace{2mm}\\par\\noindent"))
        with doc.create(Tabular("lllp{2.8in}")) as table:
            gen_table(table, data_spatial["$defs"]["cartesian_point"])

        # Global section
        doc.append(NoEscape("\\vspace{2mm}\\par\\noindent"))
        doc.append(NoEscape(add_code_tags(
            data_spatial["properties"]["global"]["description"])))
        doc.append("\n\n")
        doc.append(NoEscape("\\rowcolors{1}{}{lightblue}"))
        with doc.create(Tabular("lllp{2.8in}")) as table:
            gen_table(table, data_spatial["properties"]["global"])
        gen_fields(doc, data_spatial["properties"]["global"], "spatial_global")

        # Captures section
        doc.append(NoEscape("\\nn"))
        doc.append(NoEscape("Captures Properties:"))
        doc.append("\n\n")
        doc.append(NoEscape("\\rowcolors{1}{}{lightblue}"))
        with doc.create(Tabular("lllp{2.8in}")) as table:
            gen_table(table, data_spatial["properties"]["captures"]["items"])
        gen_fields(doc, data_spatial["properties"]
                   ["captures"]["items"], "spatial_captures")

        # Annotations section
        doc.append(NoEscape("\\nn"))
        doc.append(NoEscape("Annotations Properties:"))
        doc.append("\n\n")
        doc.append(NoEscape("\\rowcolors{1}{}{lightblue}"))
        with doc.create(Tabular("lllp{2.8in}")) as table:
            gen_table(
                table, data_spatial["properties"]["annotations"]["items"])
        gen_fields(doc, data_spatial["properties"]
                   ["annotations"]["items"], "spatial_annotations")

        # Collection section
        doc.append(NoEscape("\\nn"))
        doc.append(NoEscape("Collection Properties:"))
        doc.append("\n\n")
        doc.append(NoEscape("\\rowcolors{1}{}{lightblue}"))
        with doc.create(Tabular("lllp{2.8in}")) as table:
            gen_table(table, data_spatial["properties"]["collection"])
        gen_fields(doc, data_spatial["properties"]
                   ["collection"], "spatial_collection")

    with doc.create(Subsection("Traceability")):
        # Main description
        doc.append(NoEscape(add_code_tags(data_traceability["description"])))
        doc.append(NoEscape("\\vspace{4mm}\\par\\noindent"))

        # Definitions first
        doc.append(NoEscape("\\textbf{DataChange Object}"))
        doc.append(NoEscape("\\vspace{2mm}\\par\\noindent"))
        with doc.create(Tabular("lllp{2.8in}")) as table:
            gen_table(table, data_traceability["$defs"]["DataChange"])
        gen_fields(doc, data_traceability["$defs"]
                   ["DataChange"], "trace_datachange")

        doc.append(NoEscape("\\vspace{4mm}\\par\\noindent"))
        doc.append(NoEscape("\\textbf{Origin Object}"))
        doc.append(NoEscape("\\vspace{2mm}\\par\\noindent"))
        with doc.create(Tabular("lllp{2.8in}")) as table:
            gen_table(table, data_traceability["$defs"]["Origin"])
        gen_fields(
            doc, data_traceability["$defs"]["Origin"], "trace_origin")

        # Global section
        doc.append(NoEscape("\\vspace{4mm}\\par\\noindent"))
        doc.append(NoEscape("\\textbf{Global Properties}"))
        doc.append(NoEscape("\\vspace{2mm}\\par\\noindent"))
        with doc.create(Tabular("lllp{2.8in}")) as table:
            gen_table(table, data_traceability["properties"]["global"])
        gen_fields(
            doc, data_traceability["properties"]["global"], "trace_global")

        # Annotations section
        doc.append(NoEscape("\\vspace{4mm}\\par\\noindent"))
        doc.append(NoEscape("\\textbf{Annotations Properties}"))
        doc.append(NoEscape("\\vspace{2mm}\\par\\noindent"))
        with doc.create(Tabular("lllp{2.8in}")) as table:
            gen_table(
                table, data_traceability["properties"]["annotations"]["items"])
        gen_fields(doc, data_traceability["properties"]
                   ["annotations"]["items"], "trace_anno")

print("Generating...")
try:
    # clean_tex will remove the generated tex file
    doc.generate_pdf("sigmf-spec", clean_tex=False,
                     compiler_args=["--shell-escape"])
except subprocess.CalledProcessError as e:
    print(e)  # this seems normal to occur

# 2nd time, so table of contents loads
try:
    # clean_tex will remove the generated tex file
    doc.generate_pdf("sigmf-spec", clean_tex=False,
                     compiler_args=["--shell-escape"])
except subprocess.CalledProcessError as e:
    print(e)  # this seems normal to occur

# Create CSS file
css_string = """
#TOC {
    position: fixed;
    width: 20em;
    left: -1em;
    top: 0;
    height: 100%;
    background-color: white;
    overflow-y: scroll;
    padding: 0;
}
#subsec\:TableofContents {
    display: none;
}
body {
    padding-left: 20em;
}
@media (max-width:800px){
    #TOC {display:none; width: 0em;}
    body {padding-left: 0em;}
}
code {
    color: #000;
    font-family: monospace;
    background: #f4f4f4;
}
tr:nth-of-type(odd) {
    background-color:#f0f0ff;
}
"""
with open("main.css", "w") as f:
    f.write(css_string)

# Generate HTML from tex with Pandoc
css_url = "https://cdn.jsdelivr.net/npm/bootstrap@4.4.1/dist/css/bootstrap.min.css"
pandoc_out = subprocess.run(
    f"pandoc sigmf-spec.tex -f latex -t html -s -o sigmf-spec.html --toc --toc-depth=3 -c {css_url} -c main.css".split(
    ),
    capture_output=True,
    text=True,
)
if len(pandoc_out.stderr):
    raise Exception("Pandoc error: " + pandoc_out.stderr)

import re
from fpdf import FPDF

class MarkdownPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_page()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_font("Arial", size=12)

    def render_markdown(self, text):
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()

            # ## Heading (h2)
            if re.match(r"^##\s", line):
                heading = re.sub(r"^##\s+", "", line)
                self.set_font("Arial", "B", 16)
                self.ln(5)
                self.multi_cell(0, 10, heading)
                self.ln(2)

            # ### Subheading (h3)
            elif re.match(r"^###\s", line):
                subheading = re.sub(r"^###\s+", "", line)
                self.set_font("Arial", "B", 14)
                self.ln(4)
                self.multi_cell(0, 8, subheading)
                self.ln(1)

            # #### Sub-subheading (h4)
            elif re.match(r"^####\s", line):
                subsubheading = re.sub(r"^####\s+", "", line)
                self.set_font("Arial", "B", 12)
                self.multi_cell(0, 8, subsubheading)

            elif re.match(r"^\*\*(.+?)\*\*:\s*(.*)", line):
                match = re.match(r"^\*\*(.+?)\*\*:\s*(.*)", line)
                label, value = match.groups()
                self.set_font("Helvetica", "B", 12)
                self.cell(0, 8, f"{label}:", ln=1)
                self.set_font("Helvetica", "", 12)
                self.multi_cell(0, 8, value)

            # * **Bold:** content
            elif re.match(r"\*\s\*\*(.+?)\*\*\s(.+)", line):
                match = re.match(r"\*\s\*\*(.+?)\*\*\s(.+)", line)
                label, value = match.groups()
                label = label.rstrip(":")
            
                self.set_font("Arial", "B", 12)
                self.cell(self.get_string_width(f"- {label}: "), 8, f"- {label}:", ln=0)
            
                self.set_font("Arial", "", 12)
                self.cell(0, 8, f"  {value}", ln=1)
            
            elif re.match(r"[*\-]?\s*\*\*(.+?)\*\*\s*(.*)", line):
                match = re.match(r"[*\-]?\s*\*\*(.+?)\*\*\s*(.*)", line)
                label, value = match.groups()
                label = label.rstrip(":")
                self.set_font("Arial", "B", 12)
                self.cell(self.get_string_width(f"- {label}: "), 8, f"- {label}:", ln=0)
                self.set_font("Arial", "", 12)
                self.cell(0, 8, value, ln=1)

            elif re.match(r"^\*\*(.+?)\*\*$", line):
                heading = re.match(r"^\*\*(.+?)\*\*$", line).group(1)
                self.set_font("Arial", "B", 16)
                self.ln(5)
                self.multi_cell(0, 10, heading)
                self.ln(2)

            elif re.match(r"^\*\*(.+?)\*\*$", line):
                heading = re.match(r"^\*\*(.+?)\*\*$", line).group(1)
                self.set_font("Arial", "B", 16)
                self.ln(5)
                self.multi_cell(0, 10, heading)
                self.ln(2)

            # Bullet point
            elif re.match(r"^\*\s", line):
                content = re.sub(r"^\*\s+", "- ", line)
                self.set_font("Arial", "", 12)
                self.multi_cell(0, 8, content)

            # Normal paragraph
            else:
                self.set_font("Arial", "", 12)
                self.multi_cell(0, 8, line)
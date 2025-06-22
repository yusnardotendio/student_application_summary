import re
from fpdf import FPDF

class MarkdownPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_left_margin(15)
        self.set_right_margin(15)
        self.add_page()
        self.set_font("Helvetica", size=12)

    def safe_multicell(self, text, style="", size=12, line_height=8):
        self.set_font("Helvetica", style, size)
        safe_width = self.w - 2 * self.l_margin
        try:
            self.multi_cell(safe_width, line_height, text)
        except Exception:
            # Add soft breaks into long words if needed
            safe_text = re.sub(r'(\S{60,})', lambda m: '\u200b'.join(m.group(0)), text)
            self.multi_cell(safe_width, line_height, safe_text)

    def render_markdown(self, text):
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()

            # H2
            if re.match(r"^##\s+", line):
                heading = re.sub(r"^##\s+", "", line)
                self.set_font("Helvetica", "B", 16)
                self.ln(4)
                self.multi_cell(0, 10, heading)
                self.ln(2)

            # H3
            elif re.match(r"^###\s+", line):
                subheading = re.sub(r"^###\s+", "", line)
                self.set_font("Helvetica", "B", 14)
                self.ln(3)
                self.multi_cell(0, 8, subheading)
                self.ln(1)

            # H4
            elif re.match(r"^####\s+", line):
                subsubheading = re.sub(r"^####\s+", "", line)
                self.set_font("Helvetica", "B", 12)
                self.multi_cell(0, 8, subsubheading)
                self.ln(1)

            elif re.match(r"(.+?)\*\*(.+?)\*\*(.*)", line):
                match = re.match(r"(.+?)\*\*(.+?)\*\*(.*)", line)
                before, bold_text, after = match.groups()
                self.set_font("Helvetica", "", 12)
                self.write(8, before)
                self.set_font("Helvetica", "B", 12)
                self.write(8, bold_text)
                self.set_font("Helvetica", "", 12)
                self.write(8, after + "\n")

            # Bullet with bold label: * **Label:** content
            elif re.match(r"^\*\s+\*\*(.+?)\*\*:\s*(.*)", line):
                match = re.match(r"^\*\s+\*\*(.+?)\*\*:\s*(.*)", line)
                label, value = match.groups()
                self.set_font("Helvetica", "B", 12)
                self.cell(self.get_string_width(f"- {label}: ") + 1, 8, f"- {label}:", ln=0)
                self.set_font("Helvetica", "", 12)
                self.multi_cell(0, 8, value)
                self.ln(1)

            # Bold label only: **Label:** content
            elif re.match(r"^\*\*(.+?)\*\*:\s*(.*)", line):
                match = re.match(r"^\*\*(.+?)\*\*:\s*(.*)", line)
                label, value = match.groups()
                self.set_font("Helvetica", "B", 12)
                self.cell(self.get_string_width(f"{label}: ") + 1, 8, f"{label}:", ln=0)
                self.set_font("Helvetica", "", 12)
                self.multi_cell(0, 8, value)
                self.ln(1)

            # Bullet point (regular)
            elif re.match(r"^\*\s+", line):
                content = re.sub(r"^\*\s+", "- ", line)
                self.set_font("Helvetica", "", 12)
                self.multi_cell(0, 8, content)
                self.ln(1)

            # Standalone bold line (e.g. **Important**)
            elif re.match(r"^\*\*(.+?)\*\*$", line):
                heading = re.match(r"^\*\*(.+?)\*\*$", line).group(1)
                self.set_font("Helvetica", "B", 14)
                self.multi_cell(0, 10, heading)
                self.ln(2)

            # Default text
            else:
                self.set_font("Helvetica", "", 12)
                self.multi_cell(0, 8, line)
                self.ln(1)

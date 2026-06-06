import io

from fpdf import FPDF

from app.config import DEJAVU_PATH, DEJAVU_BOLD_PATH
from app.utils import ms_to_readable
from app.exporters.helpers import HEADER_DEFAULT


def make_pdf(data, title: str = "Transcript", header_info: dict = None,
             gdata: dict = None, label_map: dict = None) -> bytes:
    if isinstance(data, str):
        data = {"text": data}
    use_unicode = DEJAVU_PATH.exists()
    use_bold = DEJAVU_BOLD_PATH.exists()
    _summary = gdata.get("summary", "") if gdata else ""
    _font = "DejaVu" if use_unicode else "Helvetica"

    class PDF(FPDF):
        def header(self):
            if self.page_no() == 1:
                self.set_font(_font, size=14)
                self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", align="C")
                if header_info:
                    self.set_font(_font, size=8)
                    self.set_text_color(120, 120, 120)
                    lb = header_info.get("labels", HEADER_DEFAULT)
                    meta = f"{lb['date']}: {header_info['date']}  |  {lb['duration']}: {header_info['duration']}  |  {lb['lang']}: {header_info['language']}"
                    if header_info.get("speakers"):
                        meta += f"  |  {lb['speakers']}: {header_info['speakers']}"
                    self.cell(0, 6, meta, new_x="LMARGIN", new_y="NEXT", align="C")
                    self.set_text_color(0, 0, 0)
                self.ln(2)
                y = self.get_y()
                self.set_draw_color(200, 200, 200)
                self.line(self.l_margin, y, self.w - self.r_margin, y)
                self.ln(3)
            else:
                self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font(_font, size=8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f"{self.page_no()} / {{nb}}", align="C")

    pdf = PDF()
    pdf.alias_nb_pages()
    if use_unicode:
        pdf.add_font("DejaVu", fname=str(DEJAVU_PATH))
        if use_bold:
            pdf.add_font("DejaVu", style="B", fname=str(DEJAVU_BOLD_PATH))
    pdf.set_font(_font, size=11)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    if _summary:
        pdf.set_font(_font, size=9)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(0, 5, _summary)
        pdf.ln(3)
        pdf.set_text_color(0, 0, 0)

    lm = label_map or {}

    if data.get("utterances"):
        for u in data["utterances"]:
            ts = ms_to_readable(u.get("start", 0))
            spk = lm.get(u.get("speaker", ""), u.get("speaker", "Speaker"))
            text = u.get("text", "")

            # Speaker label — bold, matching DOCX style
            label = f"[{ts}] {spk}:"
            if use_bold:
                pdf.set_font(_font, style="B", size=11)
            else:
                pdf.set_font(_font, size=11)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")

            # Text body — always from left margin, consistent alignment
            pdf.set_font(_font, size=11)
            pdf.multi_cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
    else:
        pdf.set_font(_font, size=11)
        pdf.multi_cell(0, 5, data.get("text", ""))

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()

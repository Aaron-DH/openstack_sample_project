# coding=utf-8
import copy
import uuid

from PIL import Image as SOImage
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.platypus import Table
from reportlab.platypus import Image
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import ParagraphStyle as PS
from reportlab.platypus import Spacer
from reportlab.platypus import Paragraph
from reportlab.platypus import PageBreak
from reportlab.platypus import Flowable
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4

from oslo_config import cfg

ReportFileOpts = {
    cfg.StrOpt('logo_path',
               secret=True,
               default='/usr/share/report/logo/haiyun.png',
               help='Get logo of the doc from the logo_path')
}

CONF = cfg.CONF
CONF.register_opts(ReportFileOpts, group='report_file')

# before register font, copy the font file into the correct dir
registerFont(TTFont('song', '/usr/share/report/font/SURSONG.TTF'))
registerFont(TTFont('hei', '/usr/share/report/font/SIMHEI.TTF'))


stylesheet = getSampleStyleSheet()

headstyle = copy.deepcopy(stylesheet['Title'])
headstyle.fontName = 'hei'

h4style = copy.deepcopy(stylesheet['Heading4'])
h4style.fontName = 'hei'

bodystyle = copy.deepcopy(stylesheet['Normal'])
bodystyle.fontName = 'song'

levelStyle = {
    0: headstyle,
    1: h4style,
    2: h4style,
    3: h4style
}


class BookMark(Flowable):
    def __init__(self, title, level=0, closed=0):
        self.title = title
        self.key = str(uuid.uuid4())
        self.level = level
        self.align = None
        self.closed = closed
        Flowable.__init__(self)

    def wrap(self, availWidth, availHeigth):
        self.align = availWidth, availHeigth
        """Take no space"""
        return 0, 0

    def draw(self):
        # set the bookmark outline
        self.canv.showOutline()
        # put a bookmark
        self.canv.bookmarkHorizontal(self.key, self.align[0], self.align[1])
        # put an entry  in the bookmark outline
        self.canv.addOutlineEntry(self.title, self.key,
                                  self.level, self.closed)


class ReportDocTemplate(SimpleDocTemplate):
    def __init__(self, filename, **kw):
        apply(SimpleDocTemplate.__init__, (self, filename), kw)

    def afterFlowable(self, flowable):
        "Registers TOC entries."
        if (flowable.__class__.__name__ == 'BookMark'):
            text = flowable.title
            level = flowable.level
            if level < 3:
                E = [level, text, self.page]
                bn = getattr(flowable, 'key', None)
                if bn is not None:
                    E.append(bn)
                self.notify('TOCEntry', tuple(E))


class PdfReport(object):
    def __init__(self, filename):
        self.obj = []
        self.filename = filename

    def add_cover(self, **kwargs):
        self.obj.insert(0, kwargs)
        self.obj.insert(1, PageBreak())

    def add_catalog_title(self, title):
        # self.obj.append(BookMark(title, level=0))
        self.obj.append(Paragraph('<b>' + title + '</b>', headstyle))

        toc = TableOfContents()
        toc.levelStyles = [
            PS(fontName='song', fontSize=10, name='TOCHeading1', leftIndent=10,
               firstLineIndent=-20, spaceBefore=0, leading=12),
            PS(fontName='song', fontSize=10, name='TOCHeading2', leftIndent=20,
               firstLineIndent=-20, spaceBefore=0, leading=12),
            PS(fontName='song', fontSize=10, name='TOCHeading3', leftIndent=30,
               firstLineIndent=-20, spaceBefore=0, leading=12),
        ]
        self.obj.append(toc)

    def _add_logo(self, canvas):
        logo_path = CONF.report_file.logo_path
        logo = SOImage.open(logo_path)
        x, y = logo.size
        logo_x = 1 * cm
        canvas.drawInlineImage(logo, 5.8*inch, 10.9*inch, 0.7*logo_x*x/y, 0.7*logo_x)

    def _add_headerline(self, canvas):
        canvas.setFillColor('#219cd5')
        canvas.rect(0.5*inch, 11.05*inch, 5.5*inch, 0.05*inch,
                    fill=1, stroke=False)

    def _add_cuttingline(self, canvas, y):
        """
        :param canvas: the canvas obj,
                       which used for template,such as header,footer
        :param y:position of the line, the unit is inch
        :return:None
        """
        canvas.line(1*inch, y*inch, 7.27*inch, y*inch)

    def _add_catalog(self, canvas, doc):
        page = str(doc.page)
        canvas.bookmarkPage(page)
        # canvas.addOutlineEntry("Page %s" % page, page)

    def myFirstPage(self, canvas, doc):
        canvas.saveState()
        # self._add_headerline(canvas)
        self._add_cuttingline(canvas, 10.7)
        self._add_logo(canvas)
        canvas.setFont('hei', 9)
        canvas.setFillColor(colors.black)
        canvas.drawString(7 * inch, 0.5 * inch, "Page %d " % (doc.page))
        canvas.restoreState()

    def myLaterPages(self, canvas, doc):
        canvas.saveState()
        # self._add_headerline(canvas)
        self._add_cuttingline(canvas, 10.7)
        self._add_logo(canvas)
        canvas.setFont('hei', 9)
        canvas.setFillColor(colors.black)
        canvas.drawString(7 * inch, 0.5 * inch, "Page %d " % (doc.page))
        canvas.restoreState()

    def draw_title(self, title, level=0, closed=1, style=None):
        if level == 0:
            self.obj.append(PageBreak())
        if style is None:
            style = levelStyle.get(level)
        self.obj.append(Paragraph(title, style))
        self.obj.append(Spacer(0, 10))
        self.obj.append(BookMark(title, level=level, closed=closed))

    def draw_text(self, content):
        self.obj.append(Paragraph(content, bodystyle))
        self.obj.append(Spacer(0, 10))

    def draw_table(self, data, ts):
        self.obj.append(Table(data, style=ts))
        self.obj.append(Spacer(0, 10))

    def draw_pic(self, filepath):
        size = SOImage.open(filepath).size
        I = Image(filepath)
        I.drawWidth = 15 * cm
        I.drawHeight = I.drawWidth * (float(size[1]) / float(size[0]))
        self.obj.append(I)
        self.obj.append(Spacer(1, 15))

    def flush(self):
        doc = ReportDocTemplate(self.filename, pagesize=A4, topMargin=1.4*inch)
        doc.multiBuild(self.obj,
                       onFirstPage=self.myFirstPage,
                       onLaterPages=self.myLaterPages)

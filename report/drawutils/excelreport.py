#encoding:utf-8
from xlsxwriter import Workbook
from reportlab.lib import colors

data = [
    ['主机名', 'CPU使用率', '', '', '内存使用率', '', '', '交换空间', '', ''],
    ['', '平均值', '最大值', '最小值', '平均值', '最大值', '最小值','平均值', '最大值', '最小值'],
    ['node11', '15.67', '27.80', '13.30', '56.09', '56.20', '56.00', '0.00', '0.00', '0.00'],
    ['node14', '0.92', '13.50', '0.30', '9.84', '11.00', '9.30', '0.00', '0.00', '0.00']]
ts = [
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('SPAN', (0, 0), (0, 1)),
            ('SPAN', (1, 0), (3, 0)),
            ('SPAN', (4, 0), (6, 0)),
            ('SPAN', (7, 0), (9, 0)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 1), colors.lightblue),
            ('FONTNAME', (0, 0), (-1, 1), 'song')
        ]

color = ['#2EFEF7', '#81F7D8']

class ExcelReport(object):

    def __init__(self, filename):
        self.rptfile = Workbook('%s.xlsx' % filename)
        defdault_sheet = self.rptfile.add_worksheet("default")
        current_index = [0, 0]
        table_width = 0
        self.sheet_dict = {"default": [defdault_sheet, current_index, table_width]}


    def add_sheet(self, sheetname=None):
        sheet = self.rptfile.add_worksheet(sheetname)
        sheet.set_header('default')
        self.sheet_dict[sheetname] = [sheet, [0, 0]]
        return sheet

    def get_sheet(self, sheetname):
        if not sheetname:
            sheet = self.sheet_dict.get("default")
        else:
            sheet = self.sheet_dict.get(sheetname)
        return sheet


    def _merge_range(self, sheet, ts_list):
        for ts_span in ts_list:
            sheet.merge_range(ts_span[1][1],  # first_row
                              ts_span[1][0],  # first_col
                              ts_span[2][1],  # last_row
                              ts_span[2][0],  # last_col
                              '')

    def _current_sheet(self, sheet_name):
        if sheet_name:
            current_sheet = self.sheet_dict.get(sheet_name)
            if not current_sheet:
                current_sheet = self.add_sheet(sheet_name)
        else:
            current_sheet = self.sheet_dict.get("default")
        return current_sheet

    def _add_title(self, current_sheet, current_index, title, last_col=None, ts_list=None):
        _format = self.rptfile.add_format({
                'bold':True,
                'border':6,
                'align':'center',
                'font_size': 15,
                'valign': 'vcenter',
            })
        current_sheet.set_row(current_index[0], 25)
        current_sheet.merge_range(
            current_index[0],
            current_index[1],
            current_index[0],
            last_col,
            title,
            _format
        )
        current_index[0] += 1
        span_list = []
        for ts_span in ts_list:
            span_list.append(('SPAN',
                              (ts_span[1][0], ts_span[1][1]+1),
                              (ts_span[2][0], ts_span[2][1]+1)))
        self._current_sheet(current_sheet.name)[1] = current_index

        return span_list


    def _set_format(self, current_index_r):
        bg_list = self._tb_style(ts)[1]
        def _get_header_index(bg_list):
            max_index = 0
            for bg in bg_list:
                max_index = max_index if max_index > bg[2][1] else bg[2][1]
            return max_index
        if current_index_r-1 <= _get_header_index(bg_list):
            _format = self.rptfile.add_format({
                'bold':True,
                'border':6,
                'align':'center',
                'font_size': 12,
                'valign': 'vcenter',
                'bg_color': '#CEE3F6'
            })
        else:
            _format = self.rptfile.add_format({
                'bold':True,
                'border':6,
                'font_size': 12,
                'align':'center',
                'valign': 'vcenter',
                'bg_color': color[current_index_r%len(color)]
            })
        return _format


    def draw_table(self, title, data_array, ts=None, sheet_name=None):
        current_sheet = self._current_sheet(sheet_name)[0]
        current_sheet.set_column(0, len(data_array[0])-1, 12)
        span_cell = self._tb_style(ts)[0]
        def _encoding(data):
            if type(data) != unicode:
                return unicode(data,"utf-8")
            else:
                return data
        current_index = self._current_sheet(sheet_name)[1]
        if sheet_name:
            self.sheet_dict.get(sheet_name)[2] = len(data_array[0])
        else:
            self.sheet_dict.get("default")[2] = len(data_array[0])
        span_cell = self._add_title(current_sheet,
                                    current_index,
                                    title,
                                    len(data_array[0])-1,
                                    span_cell)
        current_index = self._current_sheet(sheet_name)[1]
        self._merge_range(current_sheet, span_cell)
        for data_row in data_array:
            data_row_u = map(_encoding, data_row)
            _format = self._set_format(current_index[0])
            for data in data_row_u:
                if data != '':
                    current_sheet.write_rich_string(
                        current_index[0],
                        current_index[1],
                        data,
                        _format
                    )
                current_index[1] += 1
            current_index[0] += 1
            current_index[1] = 0
        current_index[0] += 2
        self._current_sheet(sheet_name)[1] = current_index

    def draw_pic(self, title, file_path, sheet_name=None):
        current_sheet = self._current_sheet(sheet_name)[0]
        current_index = self._current_sheet(sheet_name)[1]
        pic_width = 712 # The pic we created are fixed. The cell_width is 89.
        if sheet_name:
            table_width = self.sheet_dict.get(sheet_name)[2] * 89
        else:
            table_width = self.sheet_dict.get("default")[2] * 89
        x_offset = (table_width - pic_width)/2 if table_width - pic_width > 0 else 0

        current_sheet.insert_image(current_index[0],
                                   current_index[1],
                                   file_path,
                                   {
                                       'x_offset': x_offset,
                                   }
                                   )
        current_index[0] += 2
        current_index[0] += 25
        self._current_sheet(sheet_name)[1] = current_index

    def _tb_style(self, ts):
        def _get_span(item):
            return item[0] == 'SPAN'
        def __get_bg(item):
            return item[0] == 'BACKGROUND'
        span_ts = filter(_get_span, ts)
        bg_ts = filter(_get_span, ts)
        return span_ts, bg_ts


    def flush(self):
        self.rptfile.close()

if __name__ =="__main__":
    workbook = ExcelReport("report")
    workbook.draw_table(u'虚拟机周报', data, ts)
    workbook.draw_pic(u'虚拟机周报', 'machine.png')
    workbook.draw_pic(u'虚拟机周报', 'machine.png')
    workbook.flush()

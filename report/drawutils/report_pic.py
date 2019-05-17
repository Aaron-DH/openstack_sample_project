# coding=utf-8
import pygal
import uuid
import os
from datetime import datetime
from datetime import date
from datetime import time
from pygal.style import BlueStyle
from pygal.style import DefaultStyle
from oslo_log import log
from oslo_config import cfg

CONF = cfg.CONF
LOG = log.getLogger(__name__)

PIC_OPTS = {
    cfg.StrOpt('pic_path',
               secret=True,
               default='.',
               help='The DataSource to get monitor data'),
}

CONF.register_opts(PIC_OPTS, 'report_file')

X_TIME_FORMAT = {
    "day": "%H",
    "week": "%Y-%m-%d",
    "month": "%d",
    "year": "%m"
}


class PicDriver(object):
    @classmethod
    def _render(cls, c_type, f_type):
        if not os.path.exists(CONF.report_file.pic_path):
            os.mkdir(CONF.report_file.pic_path)

        filepath = CONF.report_file.pic_path + '/' + \
            str(uuid.uuid4()) + "." + f_type

        if f_type == 'png':
            c_type.render_to_png(filepath)
        elif f_type == 'svg':
            c_type.render_to_file(filepath)

        return filepath

    @classmethod
    def bar_chart(cls, data, f_type="png"):
        bar_chart = pygal.Bar(title=unicode(data["title"], 'utf-8'),
                              height=500,
                              fill=False,
                              print_values=True,
                              rounded_bars=7,
                              print_zeroes=False)
        bar_chart.x_labels = map(str, data["x_label_list"])
        for bar in data["value_list"]:
            bar_chart.add(bar[0], bar[1])

        return PicDriver._render(bar_chart, f_type)

    @classmethod
    def line_chart(cls, data, f_type="png", time_format=None):
        line_class = pygal.DateLine

        x_data_list = data["x_label_list"]
        x_labels = [date(x.year, x.month, x.day) for x in x_data_list]

        if time_format == 'day':
            line_class = pygal.Line
            x_labels = [x.strftime('%H') for x in x_data_list]

        elif time_format == 'year':
            x_labels = [date(x.year, x.month) for x in x_data_list]

        x = X_TIME_FORMAT[time_format]

        line_chart = line_class(title=data["title"],
                                height=500,
                                fill=True,
                                x_label_rotation=20,
                                style=BlueStyle(legend_font_family='SIMHEI',title_font_family='SIMHEI'),
                                legend_at_bottom=True,
                                x_value_formatter=lambda dt: dt.strftime(x)
                                )
        line_chart.x_labels = sorted(set(x_labels))

        if time_format == 'day':
            for line in data["value_list"]:
                line_chart.add(line[0], line[1])
        else:
            for line in data["value_list"]:
                value = zip(data["x_label_list"], line[1])
                line_chart.add(line[0], value)

        return PicDriver._render(line_chart, f_type)

    @classmethod
    def pie_chart(cls, data, f_type="png"):
        pie_chart = pygal.Pie(title=data["title"],
                              height=500,
                              human_readable=True,
                              fill=True,
                              print_values=True,
                              style=BlueStyle)
        for pie in data["value_list"]:
            pie_chart.add(pie[0], pie[1])

        return PicDriver._render(pie_chart, f_type)

"""
ECharts图表生成工具 - 用于导出Excel时生成与前端一致的图表样式
"""
from io import BytesIO
import tempfile
import os
import threading

# 全局Chrome驱动实例（单例模式加速）
_driver_lock = threading.Lock()
_driver_instance = None

def _get_driver():
    """获取或创建Chrome驱动实例"""
    global _driver_instance
    with _driver_lock:
        if _driver_instance is None:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            opts = Options()
            opts.add_argument('--headless')
            opts.add_argument('--disable-gpu')
            opts.add_argument('--no-sandbox')
            opts.add_argument('--disable-dev-shm-usage')
            opts.add_argument('--window-size=1200,900')
            
            _driver_instance = webdriver.Chrome(options=opts)
        return _driver_instance

def _cleanup_driver():
    """清理Chrome驱动实例"""
    global _driver_instance
    with _driver_lock:
        if _driver_instance is not None:
            try:
                _driver_instance.quit()
            except:
                pass
            _driver_instance = None

# 注册退出时清理
import atexit
atexit.register(_cleanup_driver)

def generate_pie_chart(data, title, colors=None):
    """
    生成饼图并返回图片数据
    :param data: 列表，每个元素是 {'name': '名称', 'value': 数值}
    :param title: 图表标题
    :param colors: 颜色列表
    :return: BytesIO 图片数据
    """
    from pyecharts import options as opts
    from pyecharts.charts import Pie
    from pyecharts.render import make_snapshot
    from snapshot_selenium import snapshot
    
    if colors is None:
        colors = ['#67C23A', '#F56C6C', '#409EFF', '#E6A23C', '#909399', '#606266', '#E91E63', '#9C27B0']
    
    pie = (
        Pie(init_opts=opts.InitOpts(width="550px", height="400px", bg_color="white"))
        .add(
            "",
            [(d['name'], d['value']) for d in data],
            radius=["25%", "50%"],
            center=["50%", "50%"],
            label_opts=opts.LabelOpts(
                formatter="{b}: {c}例 ({d}%)",
                font_size=11,
            ),
        )
        .set_colors(colors[:len(data)])
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title, pos_left="center", pos_top="5px"),
            legend_opts=opts.LegendOpts(is_show=False),
        )
        .set_series_opts(
            label_opts=opts.LabelOpts(
                formatter="{b}: {c}例 ({d}%)",
                font_size=10,
            ),
            itemstyle_opts=opts.ItemStyleOpts(
                border_color="#fff",
                border_width=2,
            ),
        )
    )
    
    # 生成图片
    return _render_chart_to_image(pie)


def generate_bar_chart(data, title, x_field, y_fields, colors=None, horizontal=False):
    """
    生成柱状图并返回图片数据
    :param data: 数据列表
    :param title: 图表标题
    :param x_field: X轴字段名
    :param y_fields: Y轴字段列表，如 [{'field': '一般', 'name': '一般'}, ...]
    :param colors: 颜色列表
    :param horizontal: 是否水平柱状图
    :return: BytesIO 图片数据
    """
    from pyecharts import options as opts
    from pyecharts.charts import Bar
    
    if colors is None:
        colors = ['#67C23A', '#F56C6C', '#409EFF', '#E6A23C']
    
    x_data = [d[x_field] for d in data]
    
    bar = Bar(init_opts=opts.InitOpts(width="700px", height="450px", bg_color="white"))
    
    if horizontal:
        bar.add_xaxis(x_data[::-1])
        for i, y_info in enumerate(y_fields):
            values = [d.get(y_info['field'], 0) for d in data][::-1]
            bar.add_yaxis(
                y_info['name'], 
                values,
                label_opts=opts.LabelOpts(position="right", font_size=10),
                itemstyle_opts=opts.ItemStyleOpts(color=colors[i % len(colors)])
            )
        bar.reversal_axis()
    else:
        bar.add_xaxis(x_data)
        for i, y_info in enumerate(y_fields):
            values = [d.get(y_info['field'], 0) for d in data]
            bar.add_yaxis(
                y_info['name'], 
                values,
                label_opts=opts.LabelOpts(position="top", font_size=10),
                itemstyle_opts=opts.ItemStyleOpts(color=colors[i % len(colors)])
            )
    
    bar.set_global_opts(
        title_opts=opts.TitleOpts(title=title, pos_left="center"),
        xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=30 if not horizontal else 0, font_size=9)),
        yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(font_size=10)),
        legend_opts=opts.LegendOpts(pos_top="30px"),
    )
    
    return _render_chart_to_image(bar)


def generate_horizontal_bar_chart(data, title, name_field, value_field, color='#409EFF', value_prefix=''):
    """
    生成水平柱状图并返回图片数据
    :param data: 数据列表，已排序
    :param title: 图表标题
    :param name_field: 名称字段
    :param value_field: 数值字段
    :param color: 柱子颜色
    :param value_prefix: 数值前缀，如 '¥'
    :return: BytesIO 图片数据
    """
    from pyecharts import options as opts
    from pyecharts.charts import Bar
    
    names = [d[name_field] for d in data][::-1]
    values = [d[value_field] for d in data][::-1]
    
    bar = (
        Bar(init_opts=opts.InitOpts(width="650px", height="400px", bg_color="white"))
        .add_xaxis(names)
        .add_yaxis(
            "", 
            values,
            label_opts=opts.LabelOpts(
                position="right", 
                font_size=10,
                formatter=f"{value_prefix}{{c}}" if value_prefix else "{c}"
            ),
            itemstyle_opts=opts.ItemStyleOpts(color=color)
        )
        .reversal_axis()
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title, pos_left="center"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(font_size=10)),
            yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(font_size=10)),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )
    
    return _render_chart_to_image(bar)


def generate_reward_pie_chart(data, title):
    """
    生成奖励类型饼图
    :param data: 列表，每个元素是 {'name': '名称', 'value': 金额}
    :param title: 图表标题
    :return: BytesIO 图片数据
    """
    from pyecharts import options as opts
    from pyecharts.charts import Pie
    
    colors = ['#67C23A', '#F56C6C', '#409EFF', '#E6A23C']
    
    pie = (
        Pie(init_opts=opts.InitOpts(width="550px", height="400px", bg_color="white"))
        .add(
            "",
            [(d['name'], d['value']) for d in data],
            radius=["25%", "50%"],
            center=["50%", "50%"],
        )
        .set_colors(colors[:len(data)])
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title, pos_left="center", pos_top="5px"),
            legend_opts=opts.LegendOpts(is_show=False),
        )
        .set_series_opts(
            label_opts=opts.LabelOpts(
                formatter="{b}: ¥{c} ({d}%)",
                font_size=10,
            ),
            itemstyle_opts=opts.ItemStyleOpts(
                border_color="#fff",
                border_width=2,
            ),
        )
    )
    
    return _render_chart_to_image(pie)


def generate_drug_pie_chart(data, title):
    """
    生成药品分布饼图
    :param data: 列表，每个元素是 {'name': '药品名称', 'value': 数量}
    :param title: 图表标题
    :return: BytesIO 图片数据
    """
    from pyecharts import options as opts
    from pyecharts.charts import Pie
    
    colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#606266', '#E91E63', '#9C27B0', '#3F51B5', '#00BCD4']
    
    pie = (
        Pie(init_opts=opts.InitOpts(width="600px", height="450px", bg_color="white"))
        .add(
            "",
            [(d['name'], d['value']) for d in data],
            radius=["20%", "45%"],
            center=["50%", "50%"],
        )
        .set_colors(colors[:len(data)])
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title, pos_left="center", pos_top="5px"),
            legend_opts=opts.LegendOpts(is_show=False),
        )
        .set_series_opts(
            label_opts=opts.LabelOpts(
                formatter="{b}: {c}例 ({d}%)",
                font_size=9,
            ),
            itemstyle_opts=opts.ItemStyleOpts(
                border_color="#fff",
                border_width=2,
            ),
        )
    )
    
    return _render_chart_to_image(pie)


def _render_chart_to_image(chart):
    """
    将ECharts图表渲染为图片（使用复用的Chrome实例加速）
    :param chart: pyecharts图表对象
    :return: BytesIO 图片数据
    """
    import time
    
    # 创建临时HTML文件
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as html_file:
        html_path = html_file.name
    
    try:
        # 渲染HTML
        chart.render(html_path)
        
        # 获取复用的Chrome驱动
        driver = _get_driver()
        
        # 获取图表尺寸并调整窗口（完全匹配图表大小）
        opts = chart.options.get('init_opts', {})
        width = opts.get('width', '600px').replace('px', '')
        height = opts.get('height', '450px').replace('px', '')
        try:
            w = int(width)
            h = int(height)
            # 窗口大小需要精确匹配，避免白边
            driver.set_window_size(w, h)
        except:
            driver.set_window_size(600, 450)
        
        # 加载HTML
        driver.get(f'file://{html_path}')
        
        # 等待ECharts渲染完成
        time.sleep(0.5)
        
        # 直接截取整个视窗（大小已精确设置）
        png_data = driver.get_screenshot_as_png()
        
        return BytesIO(png_data)
    finally:
        # 清理临时文件
        try:
            os.unlink(html_path)
        except:
            pass

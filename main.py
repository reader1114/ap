import flet as ft
import json
import os
from datetime import datetime
from threading import Timer

# ====== 常数 ======
BASE_PRICES = {"一对一": 120, "一对二": 130, "一对三": 140, "一对四": 150}
GRADE_COEFF = {
    "小学": 1.0, "初一": 1.1, "初二": 1.1, "初三": 1.2,
    "高一": 1.5, "高二": 1.7, "高三": 2.0
}
COURSE_TYPES = ["一对一", "一对二", "一对三", "一对四"]
GRADES = ["小学", "初一", "初二", "初三", "高一", "高二", "高三"]
DATA_DIR = "salary_data"

# ====== 数据管理 ======
def get_file_path(year, month):
    return os.path.join(DATA_DIR, f"{year}_{month:02d}.json")

def load_data(year, month):
    path = get_file_path(year, month)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"trial": False, "eighty_min_count": 0, "cells": {}}

def save_data(year, month, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(get_file_path(year, month), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ====== 计算逻辑 ======
def calc_cell(grade, ctype, count):
    if count <= 0: return 0
    return count * BASE_PRICES[ctype] * GRADE_COEFF[grade]

def calc_total(data):
    normal_fee = 0
    for key, cnt in data["cells"].items():
        grade, ctype = key.split("|")
        normal_fee += calc_cell(grade, ctype, cnt or 0)
    if data["trial"]:
        normal_fee *= 0.9
    eighty_fee = data.get("eighty_min_count", 0) * 100
    return normal_fee + eighty_fee, eighty_fee

# ====== 主应用 ======
class SalaryApp:
    def __init__(self):
        now = datetime.now()
        self.current_year = now.year
        self.current_month = now.month
        self.data = None
        self.inputs = {}
        self.save_timer = None
        self.load_current_month()

    def load_current_month(self):
        self.data = load_data(self.current_year, self.current_month)
        self._ensure_cells()

    def _ensure_cells(self):
        for grade in GRADES:
            for ctype in COURSE_TYPES:
                key = f"{grade}|{ctype}"
                if key not in self.data["cells"]:
                    self.data["cells"][key] = 0
        if "eighty_min_count" not in self.data:
            self.data["eighty_min_count"] = 0

    def auto_save(self, delay=0.5):
        if self.save_timer: self.save_timer.cancel()
        self.save_timer = Timer(delay, self.do_save)
        self.save_timer.start()

    def do_save(self):
        save_data(self.current_year, self.current_month, self.data)

    def main(self, page: ft.Page):
        page.title = "教师薪资计算器"
        page.bgcolor = "#FFF8F0"
        page.scroll = ft.ScrollMode.AUTO
        page.padding = 12

        # 适配手机屏幕尺寸（桌面调试用，手机端自动忽略）
        page.window_width = 390
        page.window_height = 700

        # 颜色定义
        title_color = "#FFB300"
        accent = "#FF8F00"
        dark_text = "#4E342E"

        # ---------- 月份导航 ----------
        self.month_label = ft.Text(
            f"{self.current_year}年 {self.current_month}月",
            size=22, weight=ft.FontWeight.BOLD, color=title_color
        )

        def prev_month(e):
            if self.current_month == 1:
                self.current_year -= 1
                self.current_month = 12
            else:
                self.current_month -= 1
            self.load_current_month()
            self.month_label.value = f"{self.current_year}年 {self.current_month}月"
            self.refresh_all(page)
            page.update()

        def next_month(e):
            if self.current_month == 12:
                self.current_year += 1
                self.current_month = 1
            else:
                self.current_month += 1
            self.load_current_month()
            self.month_label.value = f"{self.current_year}年 {self.current_month}月"
            self.refresh_all(page)
            page.update()

        month_row = ft.Row(
            [
                ft.IconButton(icon="arrow_back", on_click=prev_month, icon_color=title_color, icon_size=24),
                self.month_label,
                ft.IconButton(icon="arrow_forward", on_click=next_month, icon_color=title_color, icon_size=24),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # ---------- 试用期开关 ----------
        self.trial_switch = ft.Switch(
            label="试用期 (普通课时费 × 0.9)",
            value=self.data["trial"],
            active_color=accent,
            label_style=ft.TextStyle(color=dark_text, size=13),
            on_change=lambda e: self.update_trial(e.control.value)
        )

        # ---------- 八十分钟课程 ----------
        self.eighty_input = ft.TextField(
            value=str(self.data["eighty_min_count"]) if self.data["eighty_min_count"] > 0 else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=60, height=34, text_align=ft.TextAlign.CENTER,
            border_color="#BCAAA4", focused_border_color=accent,
            color="black", text_size=13,
            on_change=lambda e: self.update_eighty(e.control)
        )
        self.eighty_fee_text = ft.Text("", size=13, color=accent)
        eighty_label = ft.Text("八十分钟课程 (节数):", color=dark_text, size=13)

        eighty_row = ft.Row(
            [eighty_label, self.eighty_input, self.eighty_fee_text],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True,
        )

        # ---------- 表格表头 ----------
        header_cells = [
            ft.Text("年级", width=48, color=title_color, weight=ft.FontWeight.BOLD, size=12)
        ]
        for ctype in COURSE_TYPES:
            price = BASE_PRICES[ctype]
            header_cells.append(
                ft.Text(
                    f"{ctype}\n({price}元)",
                    size=11, color=dark_text,
                    text_align=ft.TextAlign.CENTER, width=62,
                    no_wrap=False
                )
            )
        header_row = ft.Row(header_cells, spacing=2)

        # ---------- 数据行 ----------
        self.table_rows = []
        self.inputs.clear()
        for grade in GRADES:
            coeff = GRADE_COEFF[grade]
            row_ctrls = [
                ft.Text(
                    f"{grade}\n(×{coeff})",
                    size=10, color=dark_text, width=48,
                    text_align=ft.TextAlign.CENTER
                )
            ]
            for ctype in COURSE_TYPES:
                key = f"{grade}|{ctype}"
                cnt = self.data["cells"].get(key, 0)
                tf = ft.TextField(
                    value=str(cnt) if cnt > 0 else "",
                    keyboard_type=ft.KeyboardType.NUMBER,
                    width=56, height=34, text_align=ft.TextAlign.CENTER,
                    dense=True, content_padding=ft.padding.all(2),
                    border_color="#BCAAA4", focused_border_color=accent,
                    color="black", text_size=13,
                    on_change=lambda e, k=key: self.cell_changed(k, e.control)
                )
                self.inputs[key] = tf
                row_ctrls.append(tf)
            row = ft.Row(row_ctrls, spacing=2)
            self.table_rows.append(row)

        # ---------- 薪资总计 ----------
        self.total_text = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=accent)

        # ---------- 清除按钮 ----------
        def clear_month(e):
            self.data = {"trial": self.data["trial"], "eighty_min_count": 0, "cells": {}}
            self.do_save()
            self.refresh_all(page)
            page.update()

        def clear_all(e):
            if os.path.exists(DATA_DIR):
                for f in os.listdir(DATA_DIR):
                    if f.endswith(".json"):
                        os.remove(os.path.join(DATA_DIR, f))
            self.load_current_month()
            self.refresh_all(page)
            page.update()

        clear_row = ft.Row(
            [
                ft.ElevatedButton(
                    "清除当月数据", on_click=clear_month,
                    style=ft.ButtonStyle(bgcolor="#FFCC80", color="#4E342E", text_style=ft.TextStyle(size=12))
                ),
                ft.ElevatedButton(
                    "清除所有数据", on_click=clear_all,
                    style=ft.ButtonStyle(bgcolor="#FFAB91", color="#4E342E", text_style=ft.TextStyle(size=12))
                ),
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # ---------- 组装页面 ----------
        page.add(
            month_row,
            ft.Divider(color="#BCAAA4", height=1),
            self.trial_switch,
            eighty_row,
            ft.Divider(color="#BCAAA4", height=1),
            ft.Text("课时节数 (空白为0)", italic=True, color="#8D6E63", size=12),
            header_row,
            *self.table_rows,
            ft.Divider(color="#BCAAA4", height=1),
            self.total_text,
            ft.Container(height=6),
            clear_row,
        )

        self.update_total()
        page.update()

    # ---------- 事件处理 ----------
    def cell_changed(self, key, tf):
        val = tf.value.strip()
        if val == "":
            self.data["cells"][key] = 0
        else:
            try:
                self.data["cells"][key] = int(val)
            except ValueError:
                tf.value = str(self.data["cells"].get(key, 0) or "")
                tf.update()
                return
        self.update_total()
        self.auto_save()

    def update_trial(self, value):
        self.data["trial"] = value
        self.update_total()
        self.auto_save()

    def update_eighty(self, tf):
        val = tf.value.strip()
        if val == "":
            self.data["eighty_min_count"] = 0
        else:
            try:
                self.data["eighty_min_count"] = int(val)
            except ValueError:
                tf.value = str(self.data["eighty_min_count"])
                tf.update()
                return
        self.update_total()
        self.auto_save()

    def update_total(self):
        course_total, eighty_fee = calc_total(self.data)
        self.eighty_fee_text.value = f"{eighty_fee:.0f} 元" if eighty_fee > 0 else ""
        discount = " (普通课程已打9折)" if self.data["trial"] else ""
        self.total_text.value = f"课时费合计：{course_total:.2f} 元{discount}"
        self.total_text.update()
        self.eighty_fee_text.update()

    def refresh_all(self, page):
        self.trial_switch.value = self.data["trial"]
        self.eighty_input.value = str(self.data["eighty_min_count"]) if self.data["eighty_min_count"] > 0 else ""
        for key, tf in self.inputs.items():
            count = self.data["cells"].get(key, 0)
            tf.value = str(count) if count > 0 else ""
        self.update_total()

if __name__ == "__main__":
    app = SalaryApp()
    ft.app(target=app.main)
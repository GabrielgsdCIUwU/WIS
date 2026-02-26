import tkinter as tk
from abc import ABC, abstractmethod

from core.config import C


class IChartWidget(ABC):
    @abstractmethod
    def update_data(self, data: list) -> None: ...


class BarChart(tk.Canvas, IChartWidget):
    def __init__(self, parent, data, color=None, bg=None, **kw):
        super().__init__(parent, bg=bg or C["bg2"], highlightthickness=0, **kw)
        self._data  = data
        self._color = color or C["accent"]
        self.bind("<Configure>", lambda e: self._draw())

    def update_data(self, data: list):
        self._data = data
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10 or not self._data:
            if not self._data:
                self.create_text(w // 2, h // 2, text="No data yet",
                                 fill=C["fg2"], font=("Segoe UI", 9))
            return
        pad_l, pad_r, pad_t, pad_b = 48, 16, 28, 52
        chart_w = w - pad_l - pad_r
        chart_h = h - pad_t - pad_b
        max_val = max((v for _, v in self._data), default=1) or 1
        n     = len(self._data)
        gap   = 6
        bar_w = max(6, min(60, (chart_w - gap * (n + 1)) // n))
        self.create_line(pad_l, pad_t, pad_l, pad_t + chart_h, fill=C["border"], width=1)
        self.create_line(pad_l, pad_t + chart_h, pad_l + chart_w, pad_t + chart_h,
                         fill=C["border"], width=1)
        for i in range(5):
            y  = pad_t + chart_h - int(chart_h * i / 4)
            yv = max_val * i / 4
            self.create_line(pad_l - 3, y, pad_l + chart_w, y,
                             fill=C["border"], dash=(2, 4), width=1)
            self.create_text(pad_l - 5, y, text=str(round(yv)),
                             fill=C["fg2"], font=("Segoe UI", 7), anchor="e")
        total_w = n * bar_w + (n + 1) * gap
        start_x = pad_l + max(0, (chart_w - total_w) // 2) + gap
        for i, (lbl, val) in enumerate(self._data):
            x0 = start_x + i * (bar_w + gap)
            x1 = x0 + bar_w
            bh = int(chart_h * val / max_val) if max_val else 0
            y0 = pad_t + chart_h - bh
            y1 = pad_t + chart_h
            self.create_rectangle(x0+2, y0+2, x1+2, y1+2, fill=C["bg"], outline="")
            self.create_rectangle(x0, y0, x1, y1, fill=self._color, outline="", width=0)
            if bh > 14:
                self.create_text((x0+x1)//2, y0+6, text=str(val),
                                 fill=C["bg"], font=("Segoe UI", 7, "bold"), anchor="n")
            else:
                self.create_text((x0+x1)//2, y0-6, text=str(val),
                                 fill=C["fg"], font=("Segoe UI", 7), anchor="s")
            short = lbl if len(lbl) <= 9 else lbl[:8] + "…"
            self.create_text((x0+x1)//2, y1 + 10, text=short,
                             fill=C["fg2"], font=("Segoe UI", 7), anchor="n", width=bar_w + gap)


class PieChart(tk.Canvas, IChartWidget):
    PALETTE = ["#4f8ef7", "#2ecc8f", "#f0a500", "#e05252",
               "#a78bfa", "#fb923c", "#34d399", "#f472b6"]

    def __init__(self, parent, data, bg=None, **kw):
        super().__init__(parent, bg=bg or C["bg2"], highlightthickness=0, **kw)
        self._data = data
        self.bind("<Configure>", lambda e: self._draw())

    def update_data(self, data: list):
        self._data = data
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10:
            return
        total = sum(v for _, v in self._data if v > 0) if self._data else 0
        if total == 0:
            self.create_text(w // 2, h // 2, text="No data yet",
                             fill=C["fg2"], font=("Segoe UI", 9))
            return
        legend_h = min(len(self._data) * 16 + 4, 100)
        pie_area = h - 24 - legend_h - 8
        r  = min(w // 2 - 30, pie_area // 2 - 8, 80)
        cx = w // 2
        cy = 24 + pie_area // 2
        start = -90.0
        for i, (_, val) in enumerate(self._data):
            if val <= 0:
                continue
            extent = 360.0 * val / total
            self.create_arc(cx - r, cy - r, cx + r, cy + r,
                            start=start, extent=extent,
                            fill=self.PALETTE[i % len(self.PALETTE)],
                            outline=C["bg2"], width=2)
            start += extent
        ir = int(r * 0.55)
        self.create_oval(cx-ir, cy-ir, cx+ir, cy+ir, fill=C["bg2"], outline="")
        self.create_text(cx, cy,    text=str(total), fill=C["fg"],  font=("Segoe UI", 11, "bold"))
        self.create_text(cx, cy+14, text="total",    fill=C["fg2"], font=("Segoe UI", 7))
        ly = cy + r + 12
        half_w = w // 2
        for i, (lbl, val) in enumerate(self._data):
            pct   = f"{100 * val / total:.0f}%"
            lx    = 16 + (i % 2) * half_w
            lyi   = ly + (i // 2) * 16
            color = self.PALETTE[i % len(self.PALETTE)]
            self.create_rectangle(lx, lyi+2, lx+10, lyi+12, fill=color, outline="")
            short = lbl if len(lbl) <= 14 else lbl[:13] + "…"
            self.create_text(lx+14, lyi+7, text=f"{short}  {val} ({pct})",
                             fill=C["fg2"], font=("Segoe UI", 7), anchor="w")

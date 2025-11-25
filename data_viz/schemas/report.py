import base64
from datetime import datetime

from pydantic import BaseModel, Field
import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go

from pathlib import Path
from typing import List, Optional
from io import BytesIO
from playwright.sync_api import sync_playwright
import logging


default_css_files = [
    Path()  / "static" / "css" / "report.css"
]

def generate_pdf(
        html_text: str, css_files: Optional[List[Path]] = None,
        output_path: Optional[str] = None
) -> BytesIO | None:
    """
    Generate a PDF from HTML + optional CSS using Playwright (headless Chromium).
    """
    print("Generating PDF...")
    # Inline CSS if provided
    css_files = css_files or default_css_files
    css_text = ""
    if css_files:
        for file in css_files:
            if Path(file).exists():
                print("CSS file exists")
                with open(file, "r", encoding="utf-8") as f:
                    css_text += f"<style>{f.read()}</style>\n"
            else:

                import os
                print(f"CSS file not found: {file} ; {os.getcwd()=}")

    # Wrap in full HTML document
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    {css_text}
    </head>
    <body>
    {html_text}
    </body>
    </html>
    """

    pdf_bytes = BytesIO()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(full_html)
        pdf_data = page.pdf(format="A4", print_background=True)
        browser.close()

    if output_path:
        with open(output_path, "wb") as f:
            f.write(pdf_data)
        return None
    else:
        return pdf_data
        # pdf_bytes.write(pdf_data)
        # pdf_bytes.seek(0)
        # return pdf_bytes


def build_chart(
        df: pd.DataFrame,
        chart_type: str,
        x: str = None,
        y1: list = None,
        y2: list = None,
        title: str = "",
        layout: dict = None
) -> str:
    fig = go.Figure()

    # __________ SETUP DEFAULTS ____________ #
    if layout is None: layout = {}

    y1 = y1 or []
    y2 = y2 or []

    y1 = [y1] if not isinstance(y1, list) else y1
    y2 = [y2] if not isinstance(y2, list) else y2

    # Add traces for primary Y-axis
    df_columns = df.columns
    for col in y1:
        if col not in df_columns:
            raise Exception(f"{col} not in {df_columns}")
        if chart_type == "line":
            fig.add_trace(go.Scatter(x=df[x], y=df[col], mode="lines+markers", name=col, yaxis="y1"))
        elif chart_type == "bar":
            fig.add_trace(go.Bar(x=df[x], y=df[col], name=col, yaxis="y1"))
        elif chart_type == "scatter":
            fig.add_trace(go.Scatter(x=df[x], y=df[col], mode="markers", name=col, yaxis="y1"))

    # Add traces for secondary Y-axis
    for col in y2:
        if chart_type == "line":
            fig.add_trace(go.Scatter(x=df[x], y=df[col], mode="lines+markers", name=col, yaxis="y2"))
        elif chart_type == "bar":
            fig.add_trace(go.Bar(x=df[x], y=df[col], name=col, yaxis="y2"))
        elif chart_type == "scatter":
            fig.add_trace(go.Scatter(x=df[x], y=df[col], mode="markers", name=col, yaxis="y2"))

    # Layout configuration
    default_layout = {
        "title": title,
        "width": 600,
        "height": 400,
        "yaxis": {"title": "Y1"},
        "yaxis2": {"title": "Y2", "overlaying": "y", "side": "right"} if y2 else None,
        "xaxis": {"title": x},
        "template": "plotly_white",
        "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        "margin": {"l": 40, "r": 40, "t": 40, "b": 40},
    }

    default_layout.update(**layout)
    layout = default_layout

    fig.update_layout(
        **layout
    )
    # return fig.to_html(full_html=False)

    image_bytes = pio.to_image(
        fig, format="png", height=layout.get("height", 400), width=layout.get("width", 600)
    )
    png = base64.b64encode(image_bytes).decode()
    html_chart = f'<img src="data:image/png;base64,{png}" />'
    return html_chart


class BaseComponent(BaseModel):
    # type: str = Field(default="component", description="Type of the component")
    children: List['BaseComponent'] = Field(default_factory=list, description="List of child components")
    class_name: str = Field(default="component", description="CSS class name for the component")

    def html(self, *args, **kwargs):
        logging.debug(f""" RENDERING HTML FOR {self.__class__}
        {self.children=}
        {args=}
        {kwargs=}
        """)
        try:
            content = "".join([child.html(*args, **kwargs) for child in self.children])
        except Exception as e:
            content = f"Error rendering content for {self.__class__}: {str(e)}"
        return f"""<div class="{self.class_name}">{content}</div>"""


class Component(BaseModel):
    component_type: str = Field(default="chart", description="Type of the component")
    chart_type: str = Field(default="bar", description="Type of the chart")
    x_axis: str = Field(default="X Axis", description="X axis of the chart")
    y_axis_1: str = Field(default="Y Axis 1", description="Y axis 1 of the chart")
    y_axis_2: str = Field(default="Y Axis 2", description="Y axis 2 of the chart")
    class_name: str = Field(default="card", description="CSS class name for the card")
    footer: Optional[str] = Field(default=None, description="Footer text for the card")
    title: Optional[str] = Field(default=None, description="Footer text for the card")

    def html(self, *args, **kwargs):
        df = kwargs.get("df", pd.DataFrame())
        ai_describe = kwargs.get("ai_describe", False)

        content = "NO CONTENT"
        if self.component_type == "chart":
            content = build_chart(
                df=df,
                chart_type=self.chart_type,
                x=self.x_axis,
                y1=[self.y_axis_1],
                y2=[self.y_axis_2] if self.y_axis_2 else [],
                title="Sample Chart"
            )

        if ai_describe:
            described_summary = "Not Available"
            try:
                from services.llm import summarize_chart
                described_summary = summarize_chart(
                    df=df,
                    chart_type=self.chart_type,
                    x=self.x_axis,
                    y1=[self.y_axis_1],
                    y2=[self.y_axis_2] if self.y_axis_2 else [],
                    title="Sample Chart"
                )
            except Exception as e:
                described_summary = f"Error generating AI summary: {str(e)}"
            self.footer = self.footer or "" + f"<br><b>AI Summary:</b> {described_summary}"

        return f"""
            <div class="{self.class_name}">
                {f'<div class="card-header">{self.title}</div>' if self.title else ''}
                <div class="card-body">
                    <div class="image-container">{content}</div>
                </div>
                {f'<div class="card-footer">{self.footer}</div>' if self.footer else ''}
            </div>
    """


# class Card(BaseModel):
#     children: List[Component] = Field(default_factory=list, description="List of child components in the card")
#     class_name: str = Field(default="card", description="CSS class name for the card")
#
#     def html(self):
#         content = "NO CONTENT"
#         try:
#             content = "".join([child.html() for child in self.children])
#         except Exception as e:
#             content = f"Error rendering content: {str(e)}"
#         return f"""<div class="{self.class_name}">{content}</div>"""


class Col(BaseComponent):
    class_name: str = Field(default="col", description="CSS class name for the card")
    children: List[Component] = Field(default_factory=list, description="List of child components in the row")


class Row(BaseComponent):
    class_name: str = Field(default="row", description="CSS class name for the card")
    children: List[Col] = Field(default_factory=list, description="List of child components in the row")

    def html(self, *args, **kwargs):
        return f"""<div class="container">
           {super().html(*args, **kwargs)}
           </div>
           """


class Tab(BaseComponent):
    title: Optional[str] = Field(default="Tab", description="Title of the report")
    class_name: str = Field(default="tab", description="CSS class name for the card")
    children: List[Row] = Field(default_factory=list, alias="rows", description="List of tabs in the report")

    def html(self, *args, **kwargs):
        return f"""<section class="section">
            <h2>{self.title}</h2>
           {super().html(*args, **kwargs)}
           </section>
           """


class Report(BaseComponent):
    class_name: str = Field(default="report", description="CSS class name for the card")
    children: List[Tab] = Field(default_factory=list, alias="tabs", description="List of tabs in the report")
    title: Optional[str] = Field(default="Report Title", description="Title of the report")

    def front_page(self, *args, **kwargs):
        logo_path = kwargs.get("logo_path")
        if logo_path:
            image_src = ""
            if logo_path.exists():
                data = logo_path.read_bytes()
                ext = logo_path.suffix.lower()
                mime = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".gif": "image/gif",
                    ".svg": "image/svg+xml"
                }.get(ext, "application/octet-stream")

                # For SVG you can embed as UTF-8 text (smaller) or base64; use base64 for consistency
                b64 = base64.b64encode(data).decode("ascii")
                image_src = f"data:{mime};base64,{b64}"
                logo_container = f"""
                <div class="logo-container">
                        <img src="{image_src}" alt="DataViz Tool Logo" class="logo-img"/>
                    </div>
                    """
        else:
            logo_container = ""
        return f"""
            <div class="header">
                <h1>{self.title}</h1>
                <div class="header-signature">
                    <div>Generated by DataViz Tool</div>
                    {logo_container}
                    <div class="report-date">{datetime.today().strftime("%Y-%m-%d")}</div>
                </div>
            </div>
        """

    def html(self, *args, **kwargs):
        return self.front_page() + super().html(*args, **kwargs)

    def pdf(self, *args, **kwargs):
        output_path = kwargs.pop("output_path", None)
        css_files = kwargs.pop("css_files", None)
        html_text = self.html(*args, **kwargs)

        # Render PDF

        return generate_pdf(
            html_text=html_text,
            css_files=css_files,
            output_path=output_path
        )
        # pdf_io = BytesIO()
        # HTML(string=html_text).write_pdf(target=pdf_io, stylesheets=css_objs)
        #
        # if output_path is not None:
        #     # Save to disk
        #     with open(output_path, "wb") as f:
        #         f.write(pdf_io.getvalue())
        #     return None
        # else:
        #     # Return in-memory PDF
        #     pdf_io.seek(0)
        #     return pdf_io


if __name__ == "__main__":

    logo_path = Path() / ".." / "static" / "images" / "logo.png"
    dashboard_sample_path = Path() / ".." / ".." / "samples" / "dashboard_1.json"
    with open(dashboard_sample_path, "r", encoding="utf-8") as f:
        sample_data = f.read()
        import json

        report = Report(**json.loads(sample_data))

    df = pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie", "David"],
        "Age": [25, 30, 35, 40],
        "Department": [5, 10, 15, 20]
    })
    # html = report.html(df=df)
    # with open("report.html", "w", encoding="utf-8") as f:
    #     f.write(html)
    #
    report.pdf(
        df=df, output_path="../../samples/report.pdf", css_files=default_css_files,
        logo_path=logo_path
    )

    print("Report generated:report.pdf")

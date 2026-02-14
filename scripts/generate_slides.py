"""Generate demo video slides as PPTX for DocuAlign AI."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
import os
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ── Constants ────────────────────────────────────────────────────
DARK_BG = RGBColor(0x0F, 0x17, 0x2A)       # Deep navy
ACCENT_GREEN = RGBColor(0x34, 0xD3, 0x99)  # Emerald green
ACCENT_BLUE = RGBColor(0x38, 0xBD, 0xF8)   # Sky blue
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xA0, 0xA0, 0xB0)
CARD_BG = RGBColor(0x1E, 0x29, 0x3B)       # Dark card
CRITICAL_RED = RGBColor(0xEF, 0x44, 0x44)
WARNING_YELLOW = RGBColor(0xFB, 0xBF, 0x24)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
LOGO_PATH = os.path.join(PROJECT_DIR, "assets", "logo.png")
ARCH_RUNTIME_PATH = os.path.join(PROJECT_DIR, "docs", "architecture_runtime.png")
ARCH_DEV_PATH = os.path.join(PROJECT_DIR, "docs", "architecture_development.png")
INFO_BLUE = RGBColor(0x60, 0xA5, 0xFA)

SLIDE_W = Inches(13.333)  # 16:9
SLIDE_H = Inches(7.5)


def set_slide_bg(slide, color):
    """Set solid background color for a slide."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_text_box(slide, left, top, width, height, text, font_size=18,
                 color=WHITE, bold=False, alignment=PP_ALIGN.LEFT,
                 font_name="Segoe UI"):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    return txBox


def add_rounded_rect(slide, left, top, width, height, fill_color,
                     text="", font_size=14, text_color=WHITE):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    if text:
        tf = shape.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(font_size)
        p.font.color.rgb = text_color
        p.font.name = "Segoe UI"
        p.alignment = PP_ALIGN.CENTER
    return shape


def build_presentation():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank_layout = prs.slide_layouts[6]  # Blank

    # =====================================================================
    # SLIDE 1: Title Card
    # =====================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide1, DARK_BG)

    # Accent bar at top
    bar = slide1.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), SLIDE_W, Inches(0.08)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT_GREEN
    bar.line.fill.background()

    # Logo image
    if os.path.exists(LOGO_PATH):
        slide1.shapes.add_picture(
            LOGO_PATH, Inches(9.0), Inches(1.2), Inches(3.5), Inches(3.5)
        )
    else:
        circle = slide1.shapes.add_shape(
            MSO_SHAPE.OVAL, Inches(9.0), Inches(1.2), Inches(3.5), Inches(3.5)
        )
        circle.fill.solid()
        circle.fill.fore_color.rgb = ACCENT_GREEN
        circle.line.fill.background()


    # Main title
    add_text_box(slide1, Inches(1), Inches(2.0), Inches(11), Inches(1.2),
                 "DocuAlign AI", font_size=60, color=WHITE, bold=True)

    # Subtitle
    add_text_box(slide1, Inches(1), Inches(3.3), Inches(8), Inches(0.8),
                 "AI-Powered Document Integrity Agent", font_size=28,
                 color=ACCENT_GREEN)

    # Description
    add_text_box(slide1, Inches(1), Inches(4.5), Inches(10), Inches(1.0),
                 "Gemini 2.0 Flash × LangGraph × Google Cloud",
                 font_size=20, color=LIGHT_GRAY)

    # Bottom tagline
    add_text_box(slide1, Inches(1), Inches(6.0), Inches(11), Inches(0.6),
                 "ドキュメントの「サイレント劣化」をAIが自動検知", font_size=18,
                 color=LIGHT_GRAY, alignment=PP_ALIGN.LEFT)

    # =====================================================================
    # SLIDE 2: Problem Statement
    # =====================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide2, DARK_BG)

    add_text_box(slide2, Inches(0.8), Inches(0.5), Inches(10), Inches(0.8),
                 "📊 ドキュメントの「サイレント劣化」問題", font_size=36,
                 color=WHITE, bold=True)

    add_text_box(slide2, Inches(0.8), Inches(1.4), Inches(11), Inches(0.5),
                 "企業のドキュメントは作成後、静かに劣化し続けています",
                 font_size=18, color=LIGHT_GRAY)

    # 3 stat cards
    stats = [
        ("60%", "のドキュメントが\n作成6ヶ月後には\n情報が古くなっている", "📄", CRITICAL_RED),
        ("73%", "のユーザーが\n古い手順書で\n作業ミスを経験", "⚠️", WARNING_YELLOW),
        ("¥480万/年", "の損失が\nドキュメント劣化による\n業務ロスで発生", "💰", INFO_BLUE),
    ]

    for i, (number, desc, icon, accent) in enumerate(stats):
        x = Inches(0.8 + i * 4.0)
        y = Inches(2.3)

        # Card
        card = add_rounded_rect(slide2, x, y, Inches(3.5), Inches(4.2), CARD_BG)

        # Icon
        add_text_box(slide2, x + Inches(0.3), y + Inches(0.3),
                     Inches(1), Inches(0.8), icon, font_size=40)

        # Big number
        add_text_box(slide2, x + Inches(0.3), y + Inches(1.2),
                     Inches(3), Inches(1.0), number, font_size=44,
                     color=accent, bold=True)

        # Description
        add_text_box(slide2, x + Inches(0.3), y + Inches(2.5),
                     Inches(3), Inches(1.5), desc, font_size=16,
                     color=LIGHT_GRAY)

    # =====================================================================
    # SLIDE 3: Runtime Architecture (image)
    # =====================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide3, DARK_BG)

    add_text_box(slide3, Inches(0.8), Inches(0.3), Inches(10), Inches(0.8),
                 "Runtime Architecture", font_size=36,
                 color=WHITE, bold=True)

    add_text_box(slide3, Inches(0.8), Inches(1.0), Inches(11), Inches(0.4),
                 "100% Google Cloud - Serverless & Fully Managed",
                 font_size=16, color=ACCENT_GREEN)

    # Embed runtime architecture diagram
    if os.path.exists(ARCH_RUNTIME_PATH):
        # White background card for the diagram
        img_bg = slide3.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(0.5), Inches(1.5), Inches(12.3), Inches(5.7)
        )
        img_bg.fill.solid()
        img_bg.fill.fore_color.rgb = WHITE
        img_bg.line.fill.background()

        slide3.shapes.add_picture(
            ARCH_RUNTIME_PATH,
            Inches(0.8), Inches(1.7), Inches(11.7), Inches(5.3)
        )
    else:
        add_text_box(slide3, Inches(2), Inches(3), Inches(9), Inches(1),
                     "[architecture_runtime.png not found]",
                     font_size=20, color=CRITICAL_RED,
                     alignment=PP_ALIGN.CENTER)

    # =====================================================================
    # SLIDE 4: Development Architecture / Google AntiGravity
    # =====================================================================
    slide4_dev = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide4_dev, DARK_BG)

    add_text_box(slide4_dev, Inches(0.8), Inches(0.3), Inches(10), Inches(0.8),
                 "Development with Google AntiGravity",
                 font_size=36, color=WHITE, bold=True)

    add_text_box(slide4_dev, Inches(0.8), Inches(1.0), Inches(11), Inches(0.4),
                 "AI-Assisted Coding for Rapid Prototyping & Production",
                 font_size=16, color=ACCENT_GREEN)

    # Embed development architecture diagram
    if os.path.exists(ARCH_DEV_PATH):
        # White background card for the diagram
        img_bg2 = slide4_dev.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(0.3), Inches(1.5), Inches(8.0), Inches(5.7)
        )
        img_bg2.fill.solid()
        img_bg2.fill.fore_color.rgb = WHITE
        img_bg2.line.fill.background()

        slide4_dev.shapes.add_picture(
            ARCH_DEV_PATH,
            Inches(0.5), Inches(1.7), Inches(7.5), Inches(5.3)
        )
    else:
        add_text_box(slide4_dev, Inches(1), Inches(3), Inches(7), Inches(1),
                     "[architecture_development.png not found]",
                     font_size=20, color=CRITICAL_RED,
                     alignment=PP_ALIGN.CENTER)

    # AntiGravity highlights on the right side
    highlights = [
        ("AI-Assisted Coding", "AntiGravityがアーキテクチャ設計\nから実装まで支援"),
        ("LangGraph Pipeline", "エージェントパイプラインの\n設計・実装を加速"),
        ("Dashboard UI", "Streamlitダッシュボードの\nUI/UX構築を支援"),
        ("Test Generation", "ユニット&E2Eテストの\n自動生成で品質確保"),
        ("CI/CD Pipeline", "GitHub Actions →\nCloud Build → Cloud Run"),
    ]

    for i, (title, desc) in enumerate(highlights):
        x = Inches(8.8)
        y = Inches(1.5 + i * 1.1)
        card = add_rounded_rect(slide4_dev, x, y, Inches(4.2), Inches(0.95),
                                CARD_BG)
        add_text_box(slide4_dev, x + Inches(0.2), y + Inches(0.05),
                     Inches(3.8), Inches(0.35), title, font_size=13,
                     color=ACCENT_BLUE, bold=True)
        add_text_box(slide4_dev, x + Inches(0.2), y + Inches(0.4),
                     Inches(3.8), Inches(0.5), desc, font_size=11,
                     color=LIGHT_GRAY)

    # Bottom bar
    dev_bar = add_rounded_rect(
        slide4_dev, Inches(0.3), Inches(7.1), Inches(12.7), Inches(0.25),
        ACCENT_GREEN
    )

    # =====================================================================
    # SLIDE 5: Architecture & Core Tech (pipeline detail)
    # =====================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide3, DARK_BG)

    add_text_box(slide3, Inches(0.8), Inches(0.5), Inches(10), Inches(0.8),
                 "🤖 アーキテクチャ & コア技術", font_size=36,
                 color=WHITE, bold=True)

    # Pipeline flow
    steps = [
        ("1. 取得", "Google Drive\nから文書取得", ACCENT_BLUE),
        ("2. 検索", "Agent Builder\nで関連文書検索", ACCENT_BLUE),
        ("3. 分析", "Gemini 2.0\nテキスト矛盾検出", ACCENT_GREEN),
        ("4. 画像", "Gemini 2.0\nスクショ劣化検出", ACCENT_GREEN),
        ("5. 提案", "修正提案\n自動生成", ACCENT_BLUE),
    ]

    for i, (title, desc, color) in enumerate(steps):
        x = Inches(0.5 + i * 2.5)
        y = Inches(1.8)

        box = add_rounded_rect(slide3, x, y, Inches(2.2), Inches(2.0), CARD_BG)
        add_text_box(slide3, x + Inches(0.15), y + Inches(0.2),
                     Inches(1.9), Inches(0.5), title, font_size=16,
                     color=color, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide3, x + Inches(0.15), y + Inches(0.8),
                     Inches(1.9), Inches(1.0), desc, font_size=13,
                     color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

        # Arrow between steps
        if i < len(steps) - 1:
            add_text_box(slide3, x + Inches(2.2), y + Inches(0.7),
                         Inches(0.3), Inches(0.5), "→", font_size=24,
                         color=ACCENT_GREEN, alignment=PP_ALIGN.CENTER)

    # GCP Services row
    services = [
        ("Cloud Run", "サーバーレス\nホスティング"),
        ("Firestore", "スキャン結果\n保存"),
        ("GCS", "ドキュメント\nストレージ"),
        ("Eventarc", "イベント\nトリガー"),
        ("Pub/Sub", "リアルタイム\n通知"),
    ]

    add_text_box(slide3, Inches(0.8), Inches(4.2), Inches(5), Inches(0.5),
                 "☁️ Google Cloud サービス", font_size=18,
                 color=ACCENT_BLUE, bold=True)

    for i, (name, desc) in enumerate(services):
        x = Inches(0.5 + i * 2.5)
        y = Inches(4.8)
        box = add_rounded_rect(slide3, x, y, Inches(2.2), Inches(1.5), CARD_BG)
        add_text_box(slide3, x + Inches(0.15), y + Inches(0.15),
                     Inches(1.9), Inches(0.4), name, font_size=15,
                     color=ACCENT_BLUE, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide3, x + Inches(0.15), y + Inches(0.6),
                     Inches(1.9), Inches(0.8), desc, font_size=12,
                     color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

    # Key differentiator
    diff_box = add_rounded_rect(
        slide3, Inches(0.5), Inches(6.5), Inches(12.3), Inches(0.7),
        ACCENT_GREEN
    )
    add_text_box(slide3, Inches(0.8), Inches(6.55), Inches(11.8), Inches(0.6),
                 "💡 差別化: テキスト意味矛盾 + 画像劣化のマルチモーダル検出 — "
                 "LangGraphエージェントが自律実行",
                 font_size=16, color=DARK_BG, bold=True,
                 alignment=PP_ALIGN.CENTER)

    # =====================================================================
    # SLIDE 4: Business Value / ROI
    # =====================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide4, DARK_BG)

    add_text_box(slide4, Inches(0.8), Inches(0.5), Inches(10), Inches(0.8),
                 "📈 ビジネス価値 & 導入効果", font_size=36,
                 color=WHITE, bold=True)

    # ROI metrics
    metrics = [
        ("95%", "削減", "ドキュメント矛盾\n検出時間", ACCENT_GREEN),
        ("73%", "減少", "古いドキュメントによる\n顧客問い合わせ", WARNING_YELLOW),
        ("65→95%", "向上", "ドキュメント\n品質スコア", ACCENT_BLUE),
    ]

    for i, (number, action, desc, accent) in enumerate(metrics):
        x = Inches(0.8 + i * 4.0)
        y = Inches(1.8)

        card = add_rounded_rect(slide4, x, y, Inches(3.5), Inches(3.0), CARD_BG)
        add_text_box(slide4, x + Inches(0.3), y + Inches(0.3),
                     Inches(3), Inches(1.0), number, font_size=52,
                     color=accent, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide4, x + Inches(0.3), y + Inches(1.3),
                     Inches(3), Inches(0.5), action, font_size=22,
                     color=accent, alignment=PP_ALIGN.CENTER)
        add_text_box(slide4, x + Inches(0.3), y + Inches(1.9),
                     Inches(3), Inches(1.0), desc, font_size=15,
                     color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

    # Cost saving highlight
    cost_box = add_rounded_rect(
        slide4, Inches(0.8), Inches(5.2), Inches(11.5), Inches(1.8),
        CARD_BG
    )
    add_text_box(slide4, Inches(1.2), Inches(5.4), Inches(5), Inches(0.7),
                 "💰 年間コスト削減効果", font_size=22, color=WHITE, bold=True)

    add_text_box(slide4, Inches(1.2), Inches(6.0), Inches(5), Inches(0.8),
                 "50人規模の組織で", font_size=18, color=LIGHT_GRAY)

    add_text_box(slide4, Inches(6.5), Inches(5.3), Inches(5), Inches(1.5),
                 "約480万円/年", font_size=54,
                 color=ACCENT_GREEN, bold=True, alignment=PP_ALIGN.RIGHT)

    # =====================================================================
    # SLIDE 5: Closing
    # =====================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide5, DARK_BG)

    # Accent bar
    bar = slide5.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), SLIDE_W, Inches(0.08)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT_GREEN
    bar.line.fill.background()

    # Logo image on closing slide
    if os.path.exists(LOGO_PATH):
        slide5.shapes.add_picture(
            LOGO_PATH, Inches(5.4), Inches(0.5), Inches(2.5), Inches(2.5)
        )

    add_text_box(slide5, Inches(1), Inches(3.2), Inches(11), Inches(1.2),
                 "DocuAlign AI", font_size=60, color=WHITE, bold=True,
                 alignment=PP_ALIGN.CENTER)

    add_text_box(slide5, Inches(1), Inches(2.8), Inches(11), Inches(0.8),
                 "ドキュメントの「サイレント劣化」を\nAIが自動で検知・修正提案する世界へ",
                 font_size=24, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

    # GitHub card
    gh_box = add_rounded_rect(
        slide5, Inches(3), Inches(4.0), Inches(7.3), Inches(1.6), CARD_BG
    )
    add_text_box(slide5, Inches(3.5), Inches(4.15), Inches(6.3), Inches(0.5),
                 "🔗 GitHub Repository", font_size=18, color=ACCENT_BLUE,
                 bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(slide5, Inches(3.5), Inches(4.7), Inches(6.3), Inches(0.7),
                 "github.com/Koki0812/docugardener-agent",
                 font_size=22, color=ACCENT_GREEN, alignment=PP_ALIGN.CENTER)

    # Thank you
    add_text_box(slide5, Inches(1), Inches(6.2), Inches(11), Inches(0.6),
                 "ありがとうございました", font_size=28,
                 color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

    return prs


if __name__ == "__main__":
    prs = build_presentation()
    output_path = "docs/demo_slides.pptx"
    prs.save(output_path)
    print(f"Saved: {output_path}")

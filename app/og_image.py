"""服务端 OG 图片生成 — 使用 Pillow 渲染 1200x630 PNG"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CACHE_DIR = Path(os.environ.get("CLAWSCHOOL_DATA_DIR", "/opt/clawschool/data")) / "og_cache"

# 称号对应的主色
TITLE_COLORS = {
    "虾皮": "#999999",
    "冻虾仁": "#6B9BD2",
    "麻辣小龙虾": "#E85D3A",
    "蒜蓉大虾": "#F5A623",
    "澳洲大龙虾": "#D4380D",
    "波士顿龙虾": "#FF2D55",
}

def _get_font(size: int) -> ImageFont.FreeTypeFont:
    # 尝试常见中文字体路径
    font_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()

def generate_og_image(token: str, name: str, score: int, title: str, rank=None) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{token}.png"
    if cache_path.exists():
        return cache_path

    W, H = 1200, 630
    bg_color = "#1a1a2e"
    img = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    accent = TITLE_COLORS.get(title, "#FF2D55")

    # 顶部标题
    font_header = _get_font(36)
    draw.text((60, 40), "龙虾学校 · 智力测试", fill="#ffffff", font=font_header)

    # 龙虾名
    font_name = _get_font(48)
    draw.text((60, 120), name, fill="#ffffff", font=font_name)

    # 分数（大字）
    font_score = _get_font(160)
    score_text = str(score)
    draw.text((60, 220), score_text, fill=accent, font=font_score)

    # 分数标注
    font_label = _get_font(36)
    draw.text((60 + len(score_text) * 100, 340), "/ 100", fill="#888888", font=font_label)

    # 称号
    font_title = _get_font(56)
    draw.text((60, 430), title, fill=accent, font=font_title)

    # 排名
    if rank:
        font_rank = _get_font(32)
        draw.text((60, 520), f"排名 #{rank}", fill="#888888", font=font_rank)

    # 底部 URL
    font_url = _get_font(24)
    draw.text((60, 580), f"school.teamolab.com/r/{token}", fill="#666666", font=font_url)

    # 右侧装饰圆
    draw.ellipse([W - 280, 180, W - 40, 440], fill=accent, outline=None)
    emoji_font = _get_font(120)
    draw.text((W - 220, 240), "🦞", fill="#ffffff", font=emoji_font)

    img.save(str(cache_path), "PNG")
    return cache_path

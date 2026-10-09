"""Generate the LinkedIn post image (1200x627) for the Permission-Aware Company Brain."""
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 627
S = 2  # supersample for smooth edges
R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

BG = (13, 17, 28)
CARD = (24, 31, 48)
LINE = (52, 63, 89)
TXT = (234, 238, 247)
MUTED = (140, 152, 178)
BLUE = (90, 150, 255)
GREEN = (62, 207, 142)
AMBER = (255, 184, 77)
RED = (255, 107, 107)

img = Image.new("RGB", (W * S, H * S), BG)
d = ImageDraw.Draw(img)


def f(path, size):
    return ImageFont.truetype(path, size * S)


def box(x0, y0, x1, y1, fill=CARD, outline=LINE, r=14, w=2):
    d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], r * S, fill=fill, outline=outline, width=w * S)


def text(x, y, s, font, fill=TXT, anchor="la"):
    d.text((x * S, y * S), s, font=font, fill=fill, anchor=anchor)


def arrow(x0, y, x1, color=MUTED):
    d.line([x0 * S, y * S, (x1 - 6) * S, y * S], fill=color, width=3 * S)
    d.polygon([(x1 * S, y * S), ((x1 - 12) * S, (y - 7) * S), ((x1 - 12) * S, (y + 7) * S)], fill=color)


# Title
text(48, 36, "Same question. Different user.", f(B, 36), TXT)
text(48, 82, "Different answer.", f(B, 36), BLUE)
text(48, 134, "A permission-aware Company Brain for an engineering team", f(R, 18), MUTED)

# Pipeline
stages = [
    ("PULL", "Scalekit", "per-user OAuth\nNotion pages", BLUE),
    ("REMEMBER", "Cognee", "one knowledge graph\nper user", GREEN),
    ("ACT", "Agent", "answers only from\nthe user's graph", AMBER),
    ("EVALUATE", "Respan", "gateway logs +\nleak eval", RED),
]
bx, by, bw, bh, gap = 48, 182, 246, 112, 52
for i, (tag, name, sub, col) in enumerate(stages):
    x = bx + i * (bw + gap)
    box(x, by, x + bw, by + bh)
    text(x + 18, by + 14, tag, f(B, 13), col)
    text(x + 18, by + 36, name, f(B, 24), TXT)
    text(x + 18, by + 72, sub, f(R, 14), MUTED)
    if i < len(stages) - 1:
        arrow(x + bw + 8, by + bh // 2, x + bw + gap - 6)

# Access contrast
text(48, 330, "Q: What caused the Sept billing outage? How much is the Series B?", f(B, 17), TXT)

cy, ch = 368, 196
# Leadership
box(48, cy, 580, cy + ch, outline=GREEN)
text(68, cy + 16, "LEADERSHIP VIEW", f(B, 14), GREEN)
text(68, cy + 42, "6 documents", f(B, 26), TXT)
text(68, cy + 86, "RFCs · decision log · onboarding", f(R, 15), MUTED)
text(68, cy + 108, "+ postmortem · leadership priorities", f(R, 15), MUTED)
text(68, cy + 148, "Gets the root cause and the raise", f(B, 16), GREEN)
# New engineer
box(620, cy, 1152, cy + ch, outline=RED)
text(640, cy + 16, "NEW ENGINEER VIEW", f(B, 14), RED)
text(640, cy + 42, "4 documents", f(B, 26), TXT)
text(640, cy + 86, "RFCs · decision log · onboarding", f(R, 15), MUTED)
text(640, cy + 108, "No postmortem, no financing, no hiring", f(R, 15), MUTED)
text(640, cy + 148, "Gets nothing confidential", f(B, 16), RED)

# Footer
text(48, 590, "Scalekit  ×  Cognee  ×  Respan", f(B, 15), MUTED)
text(1152, 590, "Access is measured, not just shown", f(R, 15), MUTED, anchor="ra")

img = img.resize((W, H), Image.LANCZOS)
img.save("/sessions/gifted-vibrant-sagan/mnt/cognee-scalekit-example/linkedin_post.png")
print("ok")

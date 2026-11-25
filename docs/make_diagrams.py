"""Generates the five SVG figures used in the article."""
import os

OUT = os.path.join(os.path.dirname(__file__), "diagrams")
INK, MUTED = "#1f2933", "#52606d"
C = {  # fill, stroke
    "blue": ("#e3f0ff", "#2f6fba"), "green": ("#e5f6e8", "#2f855a"), "amber": ("#fff4d6", "#b7791f"),
    "rose": ("#fde8ec", "#c0392b"), "grey": ("#f1f3f5", "#7b8794"), "violet": ("#efe9fb", "#6b46c1"),
}


def head(w, h):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'font-family="Helvetica, Arial, sans-serif">\n<rect width="{w}" height="{h}" fill="#ffffff"/>\n'
            '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" '
            f'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{MUTED}"/></marker></defs>\n')


def text(x, y, s, size=15, weight="normal", fill=INK, anchor="middle"):
    s = s.replace("&", "&amp;")
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{s}</text>\n'


def box(x, y, w, h, lines, color="blue", size=15, title=True, rx=12):
    fill, stroke = C[color]
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>\n'
    n = len(lines)
    line_h = size + 6
    y0 = y + h / 2 - (n - 1) * line_h / 2 + size / 3
    for i, s in enumerate(lines):
        bold = "bold" if (i == 0 and title) else "normal"
        out += text(x + w / 2, y0 + i * line_h, s, size, bold, INK if i == 0 else INK)
    return out


def arrow(x1, y1, x2, y2, label=None, lx=0, ly=-8, dashed=False):
    d = ' stroke-dasharray="6 5"' if dashed else ""
    out = (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{MUTED}" stroke-width="2.2"{d} marker-end="url(#a)"/>\n')
    if label:
        out += text((x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly, label, 13, "normal", MUTED)
    return out


def path_arrow(d, label=None, lx=0, ly=0):
    out = f'<path d="{d}" fill="none" stroke="{MUTED}" stroke-width="2.2" marker-end="url(#a)"/>\n'
    if label:
        out += text(lx, ly, label, 13, "normal", MUTED)
    return out


def save(name, w, h, body):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(head(w, h) + body + "</svg>\n")


# Figure 1: the SMM loop
b = text(450, 38, "The social media manager loop", 22, "bold")
cards = [
    (40, 70, "Research", "blue", ["Human: reads feeds, follows peers,", "keeps a list of ideas", "Agent: fetches sources, ranks topics"]),
    (500, 70, "Create", "green", ["Human: drafts, edits, matches voice", "Agent: drafts from examples,", "checks length and banned words"]),
    (500, 300, "Engage", "amber", ["Human: comments, replies, builds ties", "Agent: drafts comment options,", "human sends and replies"]),
    (40, 300, "Measure", "violet", ["Human: reads analytics, spots patterns", "Agent: logs results, summarizes", "what worked, writes lessons"]),
]
for x, y, title, col, rows in cards:
    b += box(x, y, 360, 150, [title] + rows, col, 14)
b += arrow(400, 145, 500, 145) + arrow(680, 220, 680, 300) + arrow(500, 375, 400, 375) + arrow(220, 300, 220, 220)
b += text(450, 252, "repeat weekly", 13, "normal", MUTED)
save("fig1_smm_loop.svg", 900, 500, b)

# Figure 2: delegation map
b = text(450, 38, "What to delegate", 22, "bold")
cols = [
    (30, "Automate", "green", ["Fetch trends and news", "Skip topics already covered", "Check length and banned words", "Log and tabulate metrics"]),
    (320, "Assist: human decides", "amber", ["Shortlist of topics", "Post drafts", "Comment drafts", "Lessons from results"]),
    (610, "Keep human", "rose", ["Positioning and goals", "Personal stories and opinions", "Conversations with people", "Final approval and posting"]),
]
for x, title, col, items in cols:
    b += box(x, 70, 260, 50, [title], col, 17)
    for i, it in enumerate(items):
        b += box(x, 135 + i * 68, 260, 52, [it], col, 14, title=False, rx=8)
save("fig2_delegation_map.svg", 900, 430, b)

# Figure 3: architecture
b = text(500, 36, "Architecture of the agent", 22, "bold")
b += box(20, 80, 200, 70, ["LinkedIn export", "Profile, Shares, Comments"], "grey", 13)
b += box(20, 170, 200, 70, ["Your own text files", "posts, notes, drafts"], "grey", 13)
b += box(20, 260, 200, 70, ["Hacker News and RSS", "live trend sources"], "grey", 13)
b += box(290, 80, 200, 70, ["Style learner", "profile + embeddings"], "blue", 13)
b += box(290, 260, 200, 70, ["Researcher", "tool calling loop"], "blue", 13)
b += box(290, 380, 200, 70, ["Tools", "HN, RSS, past topics"], "grey", 13)
b += box(560, 140, 200, 70, ["Post writer", "write, check, revise"], "green", 13)
b += box(560, 260, 200, 70, ["Comment writer", "three options"], "green", 13)
b += box(830, 200, 150, 90, ["Approval queue", "you approve", "or edit"], "rose", 13)
b += box(560, 400, 420, 70, ["Memory (JSON files you can read)", "style, corpus, drafts, feedback, metrics, lessons"], "violet", 13)
b += arrow(220, 115, 290, 115) + arrow(220, 205, 290, 130) + arrow(220, 295, 290, 295)
b += arrow(390, 380, 390, 330, dashed=True) + arrow(490, 295, 560, 190) + arrow(490, 115, 560, 175)
b += arrow(490, 125, 560, 290, dashed=True)
b += arrow(760, 175, 830, 225) + arrow(760, 295, 830, 265)
b += arrow(905, 290, 905, 400, "results, edits", 4, 0)
b += text(500, 500, "Dashed arrows are reads from memory or tools. Solid arrows move data forward.", 12, "normal", MUTED)
save("fig3_architecture.svg", 1000, 520, b)

# Figure 4: tool-calling loop
b = text(450, 36, "The tool calling loop", 22, "bold")
b += box(30, 80, 190, 70, ["Messages", "plus tool specs"], "grey", 14)
b += box(290, 80, 190, 70, ["Model call", "chat.completions"], "blue", 14)
b += (f'<polygon points="660,70 780,115 660,160 540,115" fill="{C["amber"][0]}" stroke="{C["amber"][1]}" stroke-width="2"/>\n'
      + text(660, 112, "Did the model", 13) + text(660, 130, "request tools?", 13))
b += box(540, 250, 240, 70, ["Run the tool in Python", "errors become text"], "green", 14)
b += box(240, 250, 240, 70, ["Append results", 'as role "tool" messages'], "green", 14)
b += box(710, 380, 160, 60, ["Final answer", "JSON topics"], "rose", 14)
b += arrow(220, 115, 290, 115) + arrow(480, 115, 540, 115)
b += arrow(660, 160, 660, 250, "yes", 18, 0)
b += arrow(540, 285, 480, 285)
b += path_arrow("M 360 250 L 360 150", None)
b += path_arrow("M 780 115 L 800 115 L 800 380", "no", 822, 250)
b += text(450, 480, "Repeat up to max_steps times. The loop ends when the model answers without tool calls.", 13, "normal", MUTED)
save("fig4_tool_loop.svg", 900, 500, b)

# Figure 5: improvement loop
b = text(500, 36, "How the agent improves", 22, "bold")
steps = [
    (20, "Agent drafts", ["post or comment"], "blue"),
    (215, "You review", ["approve, edit, reject"], "rose"),
    (410, "You publish", ["copy to LinkedIn"], "amber"),
    (605, "Log results", ["impressions, reactions"], "violet"),
    (800, "Learn", ["lessons from edits", "and results"], "green"),
]
for x, t, rows, col in steps:
    b += box(x, 90, 175, 90, [t] + rows, col, 14)
for x in (195, 390, 585, 780):
    b += arrow(x, 135, x + 20, 135)
b += box(300, 280, 400, 70, ["Memory", "lessons and feedback feed the next draft"], "violet", 14)
b += path_arrow("M 887 180 L 887 315 L 700 315")
b += path_arrow("M 300 315 L 107 315 L 107 180")
save("fig5_improvement_loop.svg", 1000, 380, b)
print("ok")

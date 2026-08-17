#!/usr/bin/env python3
"""生成 Shotcut 练习素材、成品参考、操作演示视频。"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "素材"
OUT = ROOT / "输出"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
W, H, FPS = 1280, 720, 25

# Shotcut Fusion Dark 近似色
BG = "0x1C1C1C"
ACCENT = "0xC33636"
PANEL = "0x2A2A2A"
MUTED = "0x9A9A9A"


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({r.returncode}):\n{r.stderr[-2500:]}")


def drawtext(text: str, *, x: str, y: str, size: int, color: str = "white", bold: bool = False) -> str:
    font = BOLD if bold and Path(BOLD).exists() else FONT
    escaped = (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\u2019")
    )
    return (
        f"drawtext=fontfile={font}:text='{escaped}':fontsize={size}:"
        f"fontcolor={color}:x={x}:y={y}"
    )


def color_clip(path: Path, color: str, seconds: float, title: str, badge: str) -> None:
    vf = ",".join(
        [
            f"drawbox=x=0:y=0:w=iw:h=72:color=black@0.35:t=fill",
            drawtext("EasyAIoT  ·  Shotcut 练习素材", x="32", y="22", size=22, color="white@0.9"),
            drawtext(title, x="(w-text_w)/2", y="(h-text_h)/2-24", size=52, bold=True),
            drawtext(badge, x="(w-text_w)/2", y="(h-text_h)/2+40", size=26, color="white@0.85"),
            f"drawbox=x=0:y=ih-10:w=iw*t/{seconds}:h=10:color={ACCENT}:t=fill",
        ]
    )
    run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c={color}:s={W}x{H}:d={seconds}:r={FPS}",
            "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
            "-vf", vf,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
            str(path),
        ]
    )


def make_sources() -> None:
    SRC.mkdir(parents=True, exist_ok=True)
    color_clip(SRC / "镜头A_开场.mp4", "0x0B3D5C", 4, "镜头 A  开场介绍", "原片 4 秒  ·  练习时裁到 3 秒")
    color_clip(SRC / "镜头B_主体.mp4", "0x1B5E20", 6, "镜头 B  主体内容", "原片 6 秒  ·  练习时裁到 4 秒")
    color_clip(SRC / "镜头C_结尾.mp4", "0xE65100", 4, "镜头 C  结尾总结", "原片 4 秒  ·  练习时裁到 3 秒")


def make_finished() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    srt = ROOT / "字幕.srt"
    finished = OUT / "成品参考_已剪辑配字幕.mp4"
    a, b, c = SRC / "镜头A_开场.mp4", SRC / "镜头B_主体.mp4", SRC / "镜头C_结尾.mp4"
    # A 0-3s + B 1-5s + C 0.5-3.5s，两段 0.5s 溶解 → 9s
    fc = (
        "[0:v]trim=0:3,setpts=PTS-STARTPTS[v0];"
        "[1:v]trim=1:5,setpts=PTS-STARTPTS[v1];"
        "[2:v]trim=0.5:3.5,setpts=PTS-STARTPTS[v2];"
        "[0:a]atrim=0:3,asetpts=PTS-STARTPTS[a0];"
        "[1:a]atrim=1:5,asetpts=PTS-STARTPTS[a1];"
        "[2:a]atrim=0.5:3.5,asetpts=PTS-STARTPTS[a2];"
        "[v0][v1]xfade=transition=fade:duration=0.5:offset=2.5[v01];"
        "[a0][a1]acrossfade=d=0.5[a01];"
        "[v01][v2]xfade=transition=fade:duration=0.5:offset=6[vout];"
        "[a01][a2]acrossfade=d=0.5[aout]"
    )
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw.mp4"
        run(
            [
                "ffmpeg", "-y", "-i", str(a), "-i", str(b), "-i", str(c),
                "-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                str(raw),
            ]
        )
        style = (
            "FontName=Noto Sans CJK SC,FontSize=28,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H80000000,BorderStyle=3,Outline=1,Shadow=0,"
            "Alignment=2,MarginV=48"
        )
        run(
            [
                "ffmpeg", "-y", "-i", str(raw),
                "-vf", f"subtitles={srt}:force_style='{style}'",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy",
                str(finished),
            ]
        )
    return finished


def slide(path: Path, seconds: float, filters: list[str]) -> None:
    vf = ",".join(
        [
            f"drawbox=x=0:y=0:w=iw:h=56:color={ACCENT}:t=fill",
            drawtext("SHOTCUT  上手 Demo", x="24", y="16", size=22, bold=True),
            drawtext("剪辑  ·  转场  ·  字幕  ·  导出", x="w-text_w-24", y="18", size=18, color="white@0.9"),
            *filters,
        ]
    )
    run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c={BG}:s={W}x{H}:d={seconds}:r={FPS}",
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-vf", vf,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest", str(path),
        ]
    )


def kbd(label: str, x: int, y: int) -> list[str]:
    w = 28 + 14 * len(label)
    return [
        f"drawbox=x={x}:y={y}:w={w}:h=36:color=0x3A3A3A:t=fill",
        f"drawbox=x={x}:y={y}:w={w}:h=36:color=white@0.25:t=2",
        drawtext(label, x=str(x + 10), y=str(y + 7), size=18),
    ]


def make_tutorial(finished: Path) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        tdir = Path(tmp)

        def add(name: str, sec: float, filters: list[str]) -> None:
            p = tdir / f"{len(clips):02d}_{name}.mp4"
            slide(p, sec, filters)
            clips.append(p)

        add(
            "title",
            7,
            [
                drawtext("10 分钟学会 Shotcut", x="(w-text_w)/2", y="260", size=56, bold=True),
                drawtext("导入 → 裁剪 → 转场 → 字幕 → 导出", x="(w-text_w)/2", y="350", size=30, color="0xE8E8E8"),
                drawtext("打开同目录「素材」三支片子，对着成品参考跟做一遍即可", x="(w-text_w)/2", y="430", size=22, color=MUTED),
            ],
        )
        add(
            "ui",
            11,
            [
                drawtext("第一步   认界面（四块）", x="48", y="88", size=36, bold=True),
                f"drawbox=x=48:y=160:w=360:h=220:color={PANEL}:t=fill",
                drawtext("播放列表 Playlist", x="68", y="180", size=22, bold=True),
                drawtext("素材仓库，拖文件进来", x="68", y="220", size=20, color=MUTED),
                f"drawbox=x=428:y=160:w=804:h=220:color={PANEL}:t=fill",
                drawtext("预览监视器", x="448", y="180", size=22, bold=True),
                drawtext("看画面、打 I / O 点", x="448", y="220", size=20, color=MUTED),
                f"drawbox=x=48:y=400:w=1184:h=140:color={PANEL}:t=fill",
                drawtext("时间线 Timeline  =  真正剪的地方（V1 视频 / A1 音频）", x="68", y="424", size=22, bold=True),
                drawtext("滤镜 / 字幕 / 导出 在右侧或底部面板，视图菜单里可开关", x="68", y="468", size=20, color=MUTED),
            ],
        )
        add(
            "import",
            10,
            [
                drawtext("第二步   导入三支练习片", x="48", y="88", size=36, bold=True),
                drawtext("文件 → 打开   或   直接把 mp4 拖进播放列表", x="48", y="160", size=26),
                drawtext("demo/素材/镜头A_开场.mp4", x="48", y="230", size=24, color="0x8EC8FF"),
                drawtext("demo/素材/镜头B_主体.mp4", x="48", y="278", size=24, color="0x8EC8FF"),
                drawtext("demo/素材/镜头C_结尾.mp4", x="48", y="326", size=24, color="0x8EC8FF"),
                drawtext("验收：播放列表里能看到 3 条，点一下能在监视器里播", x="48", y="420", size=22, color=MUTED),
            ],
        )
        add(
            "timeline",
            10,
            [
                drawtext("第三步   拖上时间线 V1", x="48", y="88", size=36, bold=True),
                drawtext("从播放列表按 A → B → C 依次拖到视频轨 V1，首尾相接。", x="48", y="160", size=24),
                f"drawbox=x=48:y=250:w=1184:h=90:color={PANEL}:t=fill",
                f"drawbox=x=64:y=268:w=280:h=54:color=0x0B3D5C:t=fill",
                drawtext("A 开场", x="140", y="282", size=20),
                f"drawbox=x=352:y=268:w=420:h=54:color=0x1B5E20:t=fill",
                drawtext("B 主体", x="500", y="282", size=20),
                f"drawbox=x=780:y=268:w=280:h=54:color=0xE65100:t=fill",
                drawtext("C 结尾", x="870", y="282", size=20),
                drawtext("还没裁：现在总时长约 14 秒（4+6+4）", x="48", y="380", size=22, color=MUTED),
                *kbd("Space", 48, 460),
                drawtext("播放 / 暂停", x="150", y="468", size=20, color=MUTED),
            ],
        )
        add(
            "trim",
            12,
            [
                drawtext("第四步   裁剪（本练习的核心）", x="48", y="88", size=36, bold=True),
                drawtext("A 留前 3 秒    B 去掉开头 1 秒留 4 秒    C 留中间 3 秒", x="48", y="150", size=24),
                drawtext("三种裁法，会一种就够：", x="48", y="210", size=22, color=MUTED),
                *kbd("I", 48, 260),
                drawtext("入点（从这里开始）", x="100", y="268", size=22),
                *kbd("O", 400, 260),
                drawtext("出点（到这里结束）", x="452", y="268", size=22),
                *kbd("S", 48, 320),
                drawtext("在播放头切开，选中多余段按 Delete", x="100", y="328", size=22),
                drawtext("第三种：鼠标拖片段左右边缘，直接缩短。", x="48", y="400", size=22),
                drawtext("验收：时间线总长大约 10 秒（3+4+3）", x="48", y="460", size=22, color=MUTED),
            ],
        )
        add(
            "xfade",
            10,
            [
                drawtext("第五步   溶解转场（可选，30 秒搞定）", x="48", y="88", size=36, bold=True),
                drawtext("把后一段往前拖，让两段重叠大约 0.5 秒。", x="48", y="160", size=26),
                drawtext("重叠处会出现转场块，默认就是溶解 dissolve。", x="48", y="210", size=24, color=MUTED),
                f"drawbox=x=48:y=280:w=1184:h=90:color={PANEL}:t=fill",
                f"drawbox=x=64:y=298:w=360:h=54:color=0x0B3D5C:t=fill",
                f"drawbox=x=380:y=298:w=80:h=54:color={ACCENT}@0.85:t=fill",
                drawtext("叠", x="400", y="312", size=20),
                f"drawbox=x=420:y=298:w=400:h=54:color=0x1B5E20:t=fill",
                drawtext("不要用「追加」模式：要能重叠，先关掉时间线的吸附/插入锁定，或直接拖。", x="48", y="410", size=20, color=MUTED),
                drawtext("本参考片两处溶解各 0.5 秒，成片约 9 秒。", x="48", y="460", size=20, color=MUTED),
            ],
        )
        add(
            "subs",
            14,
            [
                drawtext("第六步   配字幕（跟做必做）", x="48", y="88", size=36, bold=True),
                drawtext("视图 → 字幕", x="48", y="150", size=26, bold=True),
                drawtext("1. 点 + 新建一条字幕轨", x="48", y="210", size=24),
                drawtext("2. 菜单「导入」选  demo/字幕.srt", x="48", y="258", size=24),
                drawtext("3. 时间线上方会出现字幕条，可拖时长、双击改字", x="48", y="306", size=24),
                drawtext("4. 预览要看见字、导出要烧进画面：", x="48", y="368", size=24),
                drawtext("   时间线选中轨道 → 滤镜 → + → 搜索 Subtitle Burn In / 字幕烧录", x="48", y="416", size=22, color="0x8EC8FF"),
                drawtext("验收：监视器底部能看到三句中文字幕，和 srt 时间轴对齐", x="48", y="480", size=20, color=MUTED),
            ],
        )
        add(
            "export",
            10,
            [
                drawtext("第七步   导出 MP4", x="48", y="88", size=36, bold=True),
                drawtext("视图 → 导出   （或窗口右侧 Export）", x="48", y="160", size=26),
                drawtext("预设保持默认即可：H.264 / MP4 / AAC", x="48", y="220", size=24),
                drawtext("点「导出文件」→ 存到  demo/输出/我的练习.mp4", x="48", y="276", size=24),
                drawtext("等进度条走完，用播放器打开，对照「成品参考」看三件事：", x="48", y="350", size=22, color=MUTED),
                drawtext("① 三段顺序对    ② 总长约 9–10 秒    ③ 底部有中文字幕", x="48", y="410", size=24),
            ],
        )
        add(
            "keys",
            9,
            [
                drawtext("常用快捷键（先记这 7 个）", x="48", y="88", size=36, bold=True),
                *kbd("Space", 48, 170),
                drawtext("播放 / 暂停", x="170", y="178", size=24),
                *kbd("I", 48, 230),
                *kbd("O", 110, 230),
                drawtext("入点 / 出点", x="180", y="238", size=24),
                *kbd("S", 48, 290),
                drawtext("切开", x="110", y="298", size=24),
                *kbd("Delete", 48, 350),
                drawtext("删掉选中段", x="180", y="358", size=24),
                *kbd("Ctrl+S", 48, 410),
                drawtext("保存工程 .mlt", x="190", y="418", size=24),
                *kbd("Ctrl+Z", 480, 410),
                drawtext("撤销", x="620", y="418", size=24),
                drawtext("J / K / L = 倒放 / 停 / 正放（老剪辑师习惯）", x="48", y="490", size=20, color=MUTED),
            ],
        )

        # 成品回放：加片头条
        outro = tdir / "99_finished.mp4"
        run(
            [
                "ffmpeg", "-y", "-i", str(finished),
                "-vf",
                ",".join(
                    [
                        f"drawbox=x=0:y=0:w=iw:h=48:color={ACCENT}:t=fill",
                        drawtext("对照看：这就是你跟做完应得到的成片", x="24", y="12", size=22, bold=True),
                    ]
                ),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy",
                str(outro),
            ]
        )
        clips.append(outro)

        lst = tdir / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in clips), encoding="utf-8")
        tutorial = OUT / "操作演示_跟着做.mp4"
        run(
            [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                str(tutorial),
            ]
        )
    return tutorial


def main() -> None:
    print("生成练习素材…")
    make_sources()
    print("生成成品参考…")
    finished = make_finished()
    print("生成操作演示…")
    tutorial = make_tutorial(finished)
    print("完成：")
    for p in [finished, tutorial]:
        print(f"  {p}  ({p.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()

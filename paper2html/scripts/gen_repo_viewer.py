#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a single-file offline source browser for thu-nics/C2C with hover footnotes."""
import sys, os, re, json, html, keyword, tokenize, io
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"C:\Users\computer\AppData\Local\Temp\opencode\C2C_repo\C2C"
OUT  = r"C:\Users\computer\Documents\notes\C2C-源码浏览器.html"

SKIP_DIRS = {".git", "resource", "__pycache__", ".ipynb_checkpoints"}
EXTS = {".py", ".json", ".yaml", ".yml", ".toml", ".sh", ".md", ".jinja", ".txt", ".ipynb"}
SPECIAL_NAMES = {".gitignore", "LICENSE"}

KEYWORDS = set(keyword.kwlist) | set(getattr(keyword, "softkwlist", []))

# ---------------------------------------------------------------- collection
def collect_files():
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for fn in sorted(filenames):
            ext = os.path.splitext(fn)[1].lower()
            if fn in SPECIAL_NAMES or ext in EXTS:
                rel = os.path.relpath(os.path.join(dirpath, fn), ROOT).replace("\\", "/")
                out.append(rel)
    return out

# ---------------------------------------------------------------- highlight
def build_char_classes(src):
    lines = src.split("\n")
    classes = [dict() for _ in lines]
    toks = tokenize.generate_tokens(io.StringIO(src if src.endswith("\n") else src + "\n").readline)
    for tok in toks:
        t = tok.type
        if t == tokenize.COMMENT:
            cls = "cm"
        elif t == tokenize.STRING:
            cls = "st"
        elif t == tokenize.NUMBER:
            cls = "nu"
        elif t == tokenize.NAME:
            s = tok.string
            cls = "kw" if s in KEYWORDS else None
        else:
            cls = None
        if not cls:
            continue
        (sr, sc), (er, ec) = tok.start, tok.end
        for r in range(sr - 1, er):
            if r >= len(lines):
                break
            line = lines[r]
            start = sc if r == sr - 1 else 0
            end = ec if r == er - 1 else len(line)
            d = classes[r]
            for c in range(start, min(end, len(line))):
                d[c] = cls
    return lines, classes

def spans_html(line, cmap):
    out, buf, cur = [], [], None
    for c, ch in enumerate(line):
        k = cmap.get(c)
        if k != cur:
            if buf:
                out.append((cur, "".join(buf)))
            buf, cur = [], k
        buf.append(ch)
    if buf:
        out.append((cur, "".join(buf)))
    return "".join(
        html.escape(s) if k is None else '<span class="%s">%s</span>' % (k, html.escape(s))
        for k, s in out
    )

def highlight_python(src):
    try:
        lines, classes = build_char_classes(src)
        return [spans_html(ln, classes[i]) for i, ln in enumerate(lines)]
    except Exception:
        return [html.escape(l) for l in src.split("\n")]

JSON_STR = re.compile(r'(&quot;(?:\\.|[^&\\])*?&quot;)(\s*:)?')
JSON_NUM = re.compile(r'(?<![\w;&])(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)(?![\w;])')

def highlight_json(src):
    out = []
    for line in src.split("\n"):
        h = html.escape(line)
        h = JSON_STR.sub(lambda m: ('<span class="jk">%s</span>%s' % (m.group(1), m.group(2))) if m.group(2) else ('<span class="st">%s</span>' % m.group(1)), h)
        h = JSON_NUM.sub(lambda m: '<span class="nu">%s</span>' % m.group(1), h)
        out.append(h)
    return out

def highlight_comment_lines(src):
    out = []
    for line in src.split("\n"):
        e = html.escape(line)
        if line.lstrip().startswith("#"):
            e = '<span class="cm">%s</span>' % e
        out.append(e)
    return out

def highlight_plain(src):
    return [html.escape(l) for l in src.split("\n")]

def highlight(path, src):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".py":
        return highlight_python(src)
    if ext in (".json", ".ipynb"):
        return highlight_json(src)
    if ext in (".yaml", ".yml", ".toml", ".sh"):
        return highlight_comment_lines(src)
    return highlight_plain(src)

# ---------------------------------------------------------------- footnotes
NOTES = {
"rosetta/model/projector.py": [
 ("class Projector(nn.Module):", "抽象基类：forward(source_kv, target_kv) 定义投影+融合；cache_project 负责把 DynamicCache 逐层送进 forward。"),
 ("class AllInOneProjector(Projector):", "通用研究版融合器：门控/权重粒度可选 scalar·token·head·head_merged·value，且可输入依赖；论文最终配置只是它的一个特例。"),
 ("self.gate_logit = nn.Parameter(torch.zeros(gate_shape, dtype=dtype))", "参数式门控（不依赖输入）：按粒度展开成标量/逐 token/逐头张量。"),
 ("class C2CProjector(Projector):", "论文最终配置的固化版：标量门、head_merged 动态权重、add_self 残差、preserve_target_weight=False。"),
 ("assert num_layers >= 3", "结构要求：1 层共用嵌入 + 1 层权重分支 + (num_layers-2) 层投影分支，最少 3 层。"),
 ("self.key_in = nn.Linear(in_dim + out_dim, hidden_dim, bias=True, dtype=dtype)", "入口：把「源缓存 + 目标缓存」拼接后投影到 hidden_dim。"),
 ("self.key_scalar_head = nn.Linear(hidden_dim, target_num_heads, dtype=dtype)", "动态权重分支：为每个注意力头产出一个标量权重。"),
 ("self.key_proj_out = nn.Linear(hidden_dim, out_dim, bias=True, dtype=dtype)", "投影分支：输出目标模型的 (头数 × 头维)。"),
 ("if zero_init:", "可选零初始化：训练起点等价于「输出 = 接收方自身」，外部信息从零开始学。"),
 ("self.key_gate_logit = nn.Parameter(torch.tensor(0.0, dtype=dtype))", "标量门：初始 logit=0（sigmoid 后 0.5），训练中移动，退火后固化成通/断。"),
 ("key_gate = torch.sigmoid((key_gate_logit + g1) / self.gate_temperature)", "训练：Gumbel-sigmoid 软开关，温度随步数从 1.0 退火到 0.001。"),
 ("key_gate = (key_gate_logit > 0).float()", "推理：直接取符号二值化（温度不再参与）。"),
 ("norm_key_scalar = torch.sigmoid(key_scalar)", "动态权重归一化到 (0,1)：逐 token、逐头调制外部信息的强度。"),
 ("output_key = target_key + key_gate * norm_key_scalar * projected_key", "全仓库最关键的一行：残差注入——target 原样保留，外部信息以「门 × 权重」调制后的增量相加，不是覆盖。"),
 ("self.last_norm_key_scalar = norm_key_scalar.detach().cpu()", "留存每步的门控/权重快照，供 script/analysis/gate_weight 分析脚本取用。"),
 ("def create_projector(projector_type: str, **kwargs)", "工厂函数：按注册类型名（如 \"C2CProjector\"）构建实例。"),
],
"rosetta/model/wrapper.py": [
 ("class RosettaModel(nn.Module):", "双模型编排器：类注释自述为「对标准 transformers 模型（如 Qwen3ForCausalLM）的无缝替换」。"),
 ('multi_source_fusion_mode: str = "parallel"', "多 Sharer 融合模式：sequential = 逐个更新 base；parallel = 所有源从干净 base 出发后求和。注释写的是 sequential (default)，实际默认值是 parallel。"),
 ("def _monkeypatch_qwen3_attention_forward(attn_module, new_k_cache, new_v_cache):", "运行时热补丁 Qwen3 attention：让注入的融合 KV 在「同一次前向」内生效，无需改 transformers 源码。"),
 ("def register_hooks(self, input_ids, attention_mask, position_ids, base_kv_cache, source_model_idx, source_kv_cache):", "prefill 阶段逐层挂钩子：把投影后的缓存替换进目标模型的注意力路径。"),
 ("kv_cache_index: List of tensors with shape (B, sec_seq_len, 2).", "逐位置路由表：-1 = 不投影；0 = 自身；>0 = 比特掩码选 Sharer（1=1号，3=两个，7=三个）——多 Sharer 融合就靠这一位掩码。"),
 ("New generation loop without using the base model's generate.", "自定义生成循环：本模块 forward 负责 prefill 与逐 token 解码，采样走 rosetta.model.sampling.sample_token。"),
],
"rosetta/model/aligner.py": [
 ("class AlignmentStrategy(Enum):", "一对多映射的两种策略：FIRST（取第一个）与 LONGEST（取字符串最长者）；论文采纳的是最大覆盖思路。"),
 ("class TokenAligner:", "以接收方（SLM）分词的 token 为基准，为每个 token 在提供方（LLM）分词器中找对应 token。"),
 ("def align_chat_messages(", "对话级对齐入口：模板段按长度 padding，消息段逐 token 重编码——对应论文 A.1.2 的两段式处理。"),
],
"rosetta/model/oracle.py": [
 ("class OracleRosettaModel(nn.Module):", "先导实验专用编排器：缓存增强 / 跨模型变换两条 oracle 线的载体，与主线 RosettaModel 分开维护。"),
],
"rosetta/train/dataset_adapters.py": [
 ("def generate_kv_cache_index(instruction_length: int, full_length: int)", "生成逐位置路由：前 instruction_length-1 个位置标 [1,0]（走 Sharer），其余 [-1,0]。训练即让模型学会在提示段接收外部缓存。"),
 ("@register_dataset", "数据集注册机制：新增数据集 = 继承 + 注册 + 在配方里写类型名。"),
],
"script/train/SFT_train.py": [
 ("def freeze_model(model: nn.Module):", "冻结/解冻工具：C2C 训练只解冻投影器，双方模型权重全部冻结。"),
 ('if "baseline" in freeze_config or "base" in freeze_config:', "配方 freeze 字段的落点：含 \"base\" 即走 C2C（冻结接收方）；baseline 模式则训练整个接收方作对照。"),
],
"script/playground/inference_example.py": [
 ("instruction_index = torch.tensor([1, 0], dtype=torch.long).repeat(inputs['input_ids'].shape[1] - 1, 1).unsqueeze(0).to(device)", "提示段：每个位置标 [1,0]——从 1 号模型（Sharer）投影。"),
 ("label_index = torch.tensor([-1, 0], dtype=torch.long).repeat(1, 1).unsqueeze(0).to(device)", "生成段：[-1,0]——不投影，答案在接收方自己的语义里生成。"),
 ('num_projectors = len([f for f in os.listdir(checkpoint_dir) if re.match(r"projector_\\d+\\.pt", f)])', "每层一个投影器：checkpoint 内 projector_{t}.json 与 projector_{t}.pt 成对存放，按编号加载。"),
 ("slm_model = rosetta_model.model_list[0]", "model_list[0] = 接收方 base，[1] = 提供方 teacher；示例依次跑 Rosetta / 接收方单独 / 提供方单独，三方对比输出。"),
],
"script/playground/live_chat_example.py": [
 ('parser.add_argument("--checkpoint_dir", type=str, nargs="+", required=True, help="Checkpoint directory(s)")', "nargs=\"+\"：传一个目录 = 单 Sharer；传多个 = 多 Sharer 融合聊天。"),
],
"recipe/train_recipe/C2C_0.6+0.5.json": [
 ('"mapping": "last_aligned"', "末端对齐：最后一层先配对、反向回推（论文 §3.3.3）。"),
 ('"anneal_steps": 1929', "与 C2CProjector 默认值、论文最终 checkpoint 步数一致。"),
 ('"freeze": ["teacher","base"]', "冻结双方模型：本配方只训练投影器。"),
 ('"type": "OpenHermesChatDataset"', "训练数据：OpenHermes 前 50 万条（论文 §4.1）。"),
],
}

# paper back-references: (label, anchor) per note, same order as NOTES
REFS = {
"rosetta/model/projector.py": [
 ("§3.3", "s04"), ("§3.3.2", "s04"), ("§3.3.2", "s04"), ("§3.3.2", "s04"), None,
 ("§3.3.2", "s04"), ("§3.3.2", "s04"), None, None, ("§3.3.2", "s04"),
 ("§3.3.2", "s04"), ("§3.3.2", "s04"), ("§3.3.2", "s04"),
 ("§4.4 消融", "s08"), ("§4.5 · §A.4.2", "s08"), None,
],
"rosetta/model/wrapper.py": [
 ("§3.3", "s04"), ("§A.5 扩展", "s09"), ("§3.3", "s04"),
 ("§3.3", "s04"), ("§3.3.1", "s04"), ("§4.2 效率", "s07"),
],
"rosetta/model/aligner.py": [
 ("§3.3.3 · A.1", "s05"), ("§3.3.3 · A.1", "s05"), ("§A.1.2", "s05"),
],
"rosetta/model/oracle.py": [
 ("§3.2", "s03"),
],
"rosetta/train/dataset_adapters.py": [
 ("§3.3.4", "s04"), None,
],
"script/train/SFT_train.py": [
 ("§3.3.4", "s04"), ("§4.4", "s08"),
],
"script/playground/inference_example.py": [
 ("§3.3.1", "s04"), ("§3.3.1", "s04"), ("§3.3.2", "s04"), ("§4.2", "s06"),
],
"script/playground/live_chat_example.py": [
 ("§A.5.1", "s09"),
],
"recipe/train_recipe/C2C_0.6+0.5.json": [
 ("§3.3.3", "s05"), ("§3.3.2", "s04"), ("§3.3.4", "s04"), ("§4.1", "s06"),
],
}

# ---------------------------------------------------------------- build data
def build_data():
    paths = collect_files()
    data = {"repo": "thu-nics/C2C", "commit": "113c3a9", "files": {}, "order": paths}
    total_notes = 0
    for rel in paths:
        full = os.path.join(ROOT, rel.replace("/", os.sep))
        try:
            with open(full, "r", encoding="utf-8") as fh:
                src = fh.read()
        except UnicodeDecodeError:
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                src = fh.read()
        size = os.path.getsize(full)
        lines_html = highlight(rel, src)
        plain = src.split("\n")
        disp = [l.replace("\t", "    ") for l in plain]
        # re-highlight display lines if tabs were expanded: simplest is re-run on expanded when tabs exist
        if "\t" in src:
            lines_html = highlight(rel, "\n".join(disp))
        notes = []
        refs = REFS.get(rel, [])
        for ni, (anchor, text) in enumerate(NOTES.get(rel, [])):
            idx = next((i for i, l in enumerate(plain) if anchor in l), None)
            if idx is not None:
                note = {"l": idx + 1, "t": text}
                if ni < len(refs) and refs[ni]:
                    note["r"] = list(refs[ni])
                notes.append(note)
                lines_html[idx] = lines_html[idx] + '<sup class="fn" data-n="%d" tabindex="0">%d</sup>' % (len(notes), len(notes))
                total_notes += 1
        data["files"][rel] = {
            "size": size,
            "lines": lines_html,
            "raw": src,
            "notes": notes,
        }
    return data, total_notes


def main():
    data, total_notes = build_data()
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    tpl = TEMPLATE.replace("__DATA__", blob)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(tpl)
    print("files:", len(data["order"]), "| notes:", total_notes, "| out:", OUT, "| size:", round(len(tpl.encode("utf-8"))/1024), "KB")

TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cache-to-Cache 源码浏览器</title>
<style>
:root{
  --paper:#F6F5F0; --paper-deep:#EDECE5; --ink:#1C1B17; --ink-soft:#565349;
  --hairline:rgba(28,27,23,.28); --hairline-soft:rgba(28,27,23,.14);
  --vermilion:#A6341F; --navy:#1D2E4E;
  --serif:Georgia,"Times New Roman","STSong","SimSun",serif;
  --sans:"Microsoft YaHei","微软雅黑","PingFang SC",sans-serif;
  --mono:Consolas,"Courier New",monospace;
}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:13px;overflow:hidden}
a{color:var(--navy)}
::selection{background:var(--vermilion);color:var(--paper)}
.topbar{height:40px;display:flex;align-items:center;gap:14px;background:var(--paper);border-bottom:1px solid var(--hairline);padding:0 16px;font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-soft)}
.topbar .ttl{color:var(--ink);white-space:nowrap}
.topbar .hint{color:var(--ink-soft);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-transform:none;letter-spacing:.02em}
.spacer{flex:1}
.tbtn{font-family:var(--mono);font-size:10.5px;letter-spacing:.08em;background:none;border:1px solid var(--hairline);color:var(--ink-soft);padding:3px 10px;cursor:pointer;white-space:nowrap}
.tbtn:hover{border-color:var(--ink);color:var(--ink)}
.tbtn[aria-pressed="true"]{border-color:var(--vermilion);color:var(--vermilion)}
a.tbtn{text-decoration:none;display:inline-block;line-height:1.6}
.fh-ref{font-family:var(--mono);font-size:10.5px;color:var(--vermilion);text-decoration:none;white-space:nowrap;border:1px dotted var(--vermilion);padding:1px 7px}
.fh-ref:hover{background:var(--vermilion);color:var(--paper)}
.layout{display:flex;height:calc(100vh - 40px)}
#sidebar{width:302px;flex:none;border-right:1px solid var(--hairline);overflow-y:auto;padding:12px 10px 40px;background:var(--paper)}
#sidebar .sb-search{margin-bottom:10px}
#search{width:100%;font-family:var(--mono);font-size:12px;padding:6px 9px;border:1px solid var(--hairline);background:transparent;color:var(--ink)}
#search:focus{outline:2px solid var(--vermilion);outline-offset:-1px}
.sb-group{font-family:var(--mono);font-size:9.5px;letter-spacing:.16em;color:var(--ink-soft);text-transform:uppercase;margin:14px 8px 5px;border-bottom:1px dotted var(--hairline);padding-bottom:4px}
.sb-file{display:flex;align-items:baseline;justify-content:space-between;gap:8px;font-family:var(--mono);font-size:11.5px;padding:3px 8px;cursor:pointer;border-left:2px solid transparent;color:var(--ink)}
.sb-file:hover{background:var(--paper-deep)}
.sb-file.active{border-left-color:var(--vermilion);color:var(--vermilion)}
.sb-size{font-size:9.5px;color:var(--ink-soft);flex:none}
.badge{font-size:9.5px;color:var(--vermilion);border:1px solid currentColor;padding:0 4px;line-height:1.5;flex:none}
#results{display:none;padding-bottom:30px}
.res-count{font-family:var(--mono);font-size:10px;color:var(--ink-soft);margin:6px 8px 8px;letter-spacing:.1em}
.res{font-family:var(--mono);font-size:11px;padding:5px 8px;cursor:pointer;border-bottom:1px dotted var(--hairline-soft);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.res:hover{background:var(--paper-deep)}
.res .rl{color:var(--vermilion)}
.res .rs{color:var(--ink-soft)}
#main{flex:1;overflow-y:auto;position:relative;background:var(--paper)}
.file-head{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:14px;background:var(--paper);border-bottom:1px solid var(--hairline);padding:9px 18px;font-family:var(--mono);font-size:11px}
.fh-path{color:var(--ink);letter-spacing:.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fh-meta{color:var(--ink-soft);white-space:nowrap}
.fh-notes{color:var(--vermilion)}
.fh-spacer{flex:1}
#code{padding:12px 0 60px;font-family:var(--mono);font-size:12.5px}
.ln-row{display:flex;line-height:1.72;min-height:1.72em}
.ln-row:hover{background:rgba(166,52,31,.05)}
.ln-row.flash{background:rgba(166,52,31,.14)}
.ln-no{width:62px;flex:none;text-align:right;padding-right:16px;color:var(--ink-soft);opacity:.5;user-select:none;font-size:11px}
.ln-code{white-space:pre;padding-right:26px}
.cm{color:var(--ink-soft);font-style:italic}
.st{color:var(--navy)}
.kw{color:var(--vermilion)}
.nu{color:var(--ink-soft)}
.jk{color:var(--navy);font-weight:700}
sup.fn{color:var(--vermilion);cursor:help;font-weight:700;margin-left:7px;font-family:var(--mono);font-size:10px;border-bottom:1px solid currentColor;line-height:1}
sup.fn:hover{background:var(--vermilion);color:var(--paper)}
#notes-panel{display:none;border-top:1px solid var(--hairline);padding:14px 20px 30px;background:var(--paper-deep)}
.note-item{font-size:12.5px;line-height:1.85;margin:7px 0;cursor:pointer;font-family:var(--sans)}
.note-item:hover{color:var(--vermilion)}
.note-item b{font-family:var(--mono);color:var(--vermilion);font-weight:700}
.note-item .nl{font-family:var(--mono);color:var(--ink-soft);font-size:11px}
#tt{position:fixed;max-width:430px;background:var(--ink);color:var(--paper);font-family:var(--sans);font-size:12px;line-height:1.75;padding:10px 13px;z-index:100;display:none;border-left:2px solid var(--vermilion)}
#tt a{color:#F2CFC5;text-decoration:none;font-family:var(--mono);font-size:11px}
#tt a:hover{color:#fff;text-decoration:underline}
.tt-ref{margin-top:8px;border-top:1px solid rgba(246,245,240,.3);padding-top:6px}
.nl-ref{font-family:var(--mono);font-size:11px;text-decoration:none}
@media(max-width:820px){#sidebar{width:220px}.topbar .hint{display:none}}
</style>
</head>
<body>
<header class="topbar">
  <span class="ttl">Cache-to-Cache 源码浏览器 · thu-nics/C2C @113c3a9</span>
  <span class="hint">悬停行尾红色脚标查看注释 · 点击「脚注」列出全部 · 侧栏搜索全仓库</span>
  <span class="spacer"></span>
  <a class="tbtn" href="C2C-缓存到缓存-深读.html">论文深读</a>
  <a class="tbtn" href="C2C-代码仓库-投射.html">仓库投射</a>
  <button class="tbtn" id="btn-notes" aria-pressed="false">脚注</button>
</header>
<div class="layout">
  <aside id="sidebar">
    <div class="sb-search"><input id="search" type="search" placeholder="搜索代码…（≥2字符）" autocomplete="off"></div>
    <div id="sb-list"></div>
    <div id="results"></div>
  </aside>
  <main id="main">
    <div class="file-head" id="file-head"></div>
    <div id="code"></div>
    <div id="notes-panel"></div>
  </main>
</div>
<div id="tt" role="tooltip"></div>
<script type="application/json" id="repodata">__DATA__</script>
<script>
(function(){
  "use strict";
  var DATA = JSON.parse(document.getElementById('repodata').textContent);
  var files = DATA.files, order = DATA.order;
  var sb = document.getElementById('sb-list');
  var resultsEl = document.getElementById('results');
  var searchEl = document.getElementById('search');
  var codeEl = document.getElementById('code');
  var headEl = document.getElementById('file-head');
  var notesPanel = document.getElementById('notes-panel');
  var noteBtn = document.getElementById('btn-notes');
  var mainEl = document.getElementById('main');
  var tt = document.getElementById('tt');
  var curPath = null, curNotes = [], notesOpen = false;

  function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function fmtSize(b){ return b >= 1024 ? (b/1024).toFixed(1)+' KB' : b+' B'; }

  function renderSidebar(){
    var groups = {};
    order.forEach(function(p){
      var parts = p.split('/');
      var g = parts.length > 1 ? parts.slice(0,-1).join('/') : '（根目录）';
      (groups[g] = groups[g] || []).push(p);
    });
    var out = '';
    Object.keys(groups).sort().forEach(function(g){
      out += '<div class="sb-group">'+esc(g)+'</div>';
      groups[g].forEach(function(p){
        var f = files[p], n = f.notes.length;
        out += '<div class="sb-file" data-p="'+esc(p)+'" title="'+esc(p)+'"><span>'+esc(p.split('/').pop())+'</span>'+(n?'<span class="badge">'+n+'</span>':'<span class="sb-size">'+fmtSize(f.size)+'</span>')+'</div>';
      });
    });
    sb.innerHTML = out;
    Array.prototype.forEach.call(sb.querySelectorAll('.sb-file'), function(el){
      el.addEventListener('click', function(){ openFile(el.getAttribute('data-p'), 0); });
    });
  }

  function noteLabel(){
    noteBtn.textContent = curNotes.length ? '脚注（'+curNotes.length+'）' : '脚注';
    noteBtn.setAttribute('aria-pressed', String(notesOpen));
  }

  function renderNotesPanel(){
    if(!notesOpen || !curNotes.length){ notesPanel.style.display = 'none'; return; }
    var out = '<div style="font-family:var(--mono);font-size:10px;letter-spacing:.16em;color:var(--ink-soft);text-transform:uppercase;margin-bottom:8px">FOOTNOTES · '+esc(curPath)+'</div>';
    curNotes.forEach(function(n, i){
      var ref = n.r ? (' · <a class="nl-ref" href="C2C-缓存到缓存-深读.html#'+n.r[1]+'">论文 '+esc(n.r[0])+' ↗</a>') : '';
      out += '<div class="note-item" data-l="'+n.l+'"><b>['+(i+1)+']</b> <span class="nl">L'+n.l+'</span> — '+n.t+ref+'</div>';
    });
    notesPanel.innerHTML = out;
    notesPanel.style.display = 'block';
    Array.prototype.forEach.call(notesPanel.querySelectorAll('.note-item'), function(el){
      el.addEventListener('click', function(e){
        if(e.target.tagName === 'A') return;
        jumpTo(parseInt(el.getAttribute('data-l'),10));
      });
    });
  }

  function jumpTo(line){
    var el = document.getElementById('L'+line);
    if(!el) return;
    el.scrollIntoView({block:'center'});
    el.classList.add('flash');
    setTimeout(function(){ el.classList.remove('flash'); }, 1400);
  }

  function openFile(path, line){
    if(!files[path]) return;
    curPath = path;
    var f = files[path];
    curNotes = f.notes;
    var out = '';
    for(var i=0;i<f.lines.length;i++){
      out += '<div class="ln-row" id="L'+(i+1)+'"><span class="ln-no">'+(i+1)+'</span><span class="ln-code">'+f.lines[i]+'</span></div>';
    }
    codeEl.innerHTML = out;
    var seen = {}, refHtml = '';
    curNotes.forEach(function(n){
      if(n.r && !seen[n.r[1]]){
        seen[n.r[1]] = 1;
        refHtml += '<a class="fh-ref" href="C2C-缓存到缓存-深读.html#'+n.r[1]+'">论文 '+esc(n.r[0])+' ↗</a> ';
      }
    });
    headEl.innerHTML = '<span class="fh-path">'+esc(path)+'</span>'
      + '<span class="fh-meta">'+f.lines.length+' 行 · '+fmtSize(f.size)+'</span>'
      + (curNotes.length ? '<span class="fh-meta fh-notes">脚注 '+curNotes.length+'</span>' : '')
      + refHtml
      + '<span class="fh-spacer"></span><button class="tbtn" id="btn-copy">复制源码</button>';
    document.getElementById('btn-copy').addEventListener('click', function(){ copyCur(this); });
    Array.prototype.forEach.call(sb.querySelectorAll('.sb-file'), function(el){
      el.classList.toggle('active', el.getAttribute('data-p') === path);
    });
    noteLabel();
    renderNotesPanel();
    hideTip();
    if(line > 0){ jumpTo(line); } else { mainEl.scrollTop = 0; }
    try{ history.replaceState(null, '', '#f='+encodeURIComponent(path)+(line>0?('&l='+line):'')); }catch(e){}
  }

  function copyCur(btn){
    var raw = files[curPath].raw;
    function done(){ btn.textContent = '已复制'; setTimeout(function(){ btn.textContent = '复制源码'; }, 1200); }
    function fallback(){
      var ta = document.createElement('textarea');
      ta.value = raw; ta.style.position = 'fixed'; ta.style.left = '-9999px';
      document.body.appendChild(ta); ta.select();
      try{ document.execCommand('copy'); done(); }catch(e){}
      document.body.removeChild(ta);
    }
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(raw).then(done, fallback);
    } else { fallback(); }
  }

  var hideTimer = null;
  function showTip(el){
    var idx = parseInt(el.getAttribute('data-n'),10);
    var note = curNotes[idx-1];
    if(!note) return;
    var body = esc(note.t);
    if(note.r){
      body += '<div class="tt-ref"><a href="C2C-缓存到缓存-深读.html#'+note.r[1]+'">论文 '+esc(note.r[0])+' ↗</a></div>';
    }
    tt.innerHTML = body;
    tt.style.display = 'block';
    var r = el.getBoundingClientRect();
    var tw = tt.offsetWidth, th = tt.offsetHeight;
    var left = Math.min(Math.max(8, r.left - 24), window.innerWidth - tw - 12);
    var top = r.bottom + 10;
    if(top + th > window.innerHeight - 8){ top = Math.max(8, r.top - th - 10); }
    tt.style.left = left+'px'; tt.style.top = top+'px';
  }
  function hideTip(){ tt.style.display = 'none'; }
  function showTipFor(el){ clearTimeout(hideTimer); showTip(el); }
  function scheduleHide(){ clearTimeout(hideTimer); hideTimer = setTimeout(hideTip, 200); }

  codeEl.addEventListener('mouseover', function(e){
    var t = e.target;
    if(t && t.classList && t.classList.contains('fn')){ showTipFor(t); }
  });
  codeEl.addEventListener('mouseout', function(e){
    var t = e.target;
    if(t && t.classList && t.classList.contains('fn')){ scheduleHide(); }
  });
  codeEl.addEventListener('focusin', function(e){
    var t = e.target;
    if(t && t.classList && t.classList.contains('fn')){ showTipFor(t); }
  });
  codeEl.addEventListener('focusout', scheduleHide);
  tt.addEventListener('mouseenter', function(){ clearTimeout(hideTimer); });
  tt.addEventListener('mouseleave', scheduleHide);
  mainEl.addEventListener('scroll', hideTip, {passive:true});
  window.addEventListener('resize', hideTip);

  noteBtn.addEventListener('click', function(){
    notesOpen = !notesOpen;
    noteLabel();
    renderNotesPanel();
  });

  var tId = null;
  searchEl.addEventListener('input', function(){
    clearTimeout(tId);
    tId = setTimeout(doSearch, 180);
  });
  function doSearch(){
    var q = searchEl.value.trim();
    if(q.length < 2){ resultsEl.style.display='none'; sb.style.display=''; return; }
    var ql = q.toLowerCase(), out = [], total = 0;
    for(var i=0;i<order.length && total<200;i++){
      var p = order[i];
      if(p.toLowerCase().indexOf(ql) >= 0){ out.push({p:p,l:0,s:'（文件名匹配）'}); total++; }
      var raw = files[p].raw, lower = raw.toLowerCase();
      var pos = 0, count = 0;
      while(count < 20 && total < 200){
        pos = lower.indexOf(ql, pos);
        if(pos < 0) break;
        var lineNo = raw.slice(0,pos).split('\n').length;
        var ls = raw.lastIndexOf('\n',pos)+1, le = raw.indexOf('\n',pos);
        if(le < 0) le = raw.length;
        out.push({p:p, l:lineNo, s:raw.slice(ls,le).trim()});
        pos += ql.length; count++; total++;
      }
    }
    var html = '<div class="res-count">'+out.length+' 条结果'+(total>=200?'（已截断）':'')+'</div>';
    out.forEach(function(r){
      html += '<div class="res" data-p="'+esc(r.p)+'" data-l="'+r.l+'"><span class="rl">'+esc(r.p.split('/').pop())+(r.l?(':'+r.l):'')+'</span> <span class="rs">'+esc(r.s.slice(0,80))+'</span></div>';
    });
    resultsEl.innerHTML = html;
    resultsEl.style.display = 'block';
    sb.style.display = 'none';
    Array.prototype.forEach.call(resultsEl.querySelectorAll('.res'), function(el){
      el.addEventListener('click', function(){
        openFile(el.getAttribute('data-p'), parseInt(el.getAttribute('data-l'),10) || 0);
      });
    });
  }

  renderSidebar();
  var mF = location.hash.match(/f=([^&]+)/), mL = location.hash.match(/l=(\d+)/);
  var startPath = mF ? decodeURIComponent(mF[1]) : 'rosetta/model/projector.py';
  openFile(files[startPath] ? startPath : 'rosetta/model/projector.py', mL ? parseInt(mL[1],10) : 0);
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Build the reconciliation edition: paper claims x source-code facts, audited unit by unit.
One single flow: claim -> code (with margin glosses) -> reconciliation verdict."""
import sys, os, re, html as H
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\computer\AppData\Local\Temp\opencode")
import gen_repo_viewer as g

ROOT = g.ROOT
OUT  = r"C:\Users\computer\Documents\notes\C2C-对账式详解.html"
BROWSER = "C2C-源码浏览器.html"

def read(rel):
    with open(os.path.join(ROOT, rel.replace("/", os.sep)), encoding="utf-8") as fh:
        return fh.read()

_cache = {}
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"
UNCOVERED = []
COV_STAT = [0, 0]

def _load(rel):
    if rel not in _cache:
        src = read(rel)
        _cache[rel] = (src.split("\n"), g.highlight(rel, src))
    return _cache[rel]

def _trivial(line):
    s = line.strip()
    return s == "" or all(c in "{}[](),;:'\"" for c in s)

def _find(plain, sub, start, end, occ=1):
    cnt = 0
    for j in range(start, end + 1):
        if sub in plain[j]:
            cnt += 1
            if cnt == occ:
                return j
    return None

def code_block(rel, a, b=None, anns=None, occ=1):
    plain, hl = _load(rel)
    s = _find(plain, a, 0, len(plain) - 1, occ)
    if s is None:
        raise SystemExit("start anchor not found: %s @ %s" % (a, rel))
    e = s if b is None else _find(plain, b, s, len(plain) - 1, 1)
    if e is None:
        raise SystemExit("end anchor not found: %s @ %s" % (b, rel))

    resolved = []
    for an in (anns or []):
        if an.get("free"):
            resolved.append([None, None, an["t"]])
            continue
        if "a" in an:
            as_ = next((j for j in range(s, e + 1) if an["a"] in plain[j]), None)
            if as_ is None:
                raise SystemExit("ann start not found: %s @ %s" % (an["a"], rel))
            if "b" in an:
                ae = next((j for j in range(as_, e + 1) if an["b"] in plain[j]), None)
                if ae is None:
                    raise SystemExit("ann end not found: %s @ %s" % (an["b"], rel))
            else:
                ae = as_
        else:
            as_, ae = s, e
        resolved.append([as_, ae, an["t"]])

    numbered = [r for r in resolved if r[0] is not None]
    covered = set()
    badges = {}
    gmap = {}
    for idx, (as_, ae, t) in enumerate(numbered):
        badges[as_] = badges.get(as_, "") + CIRCLED[idx]
        for j in range(as_, ae + 1):
            covered.add(j)
            gmap[j] = idx + 1
    total = e - s + 1
    for j in range(s, e + 1):
        if _trivial(plain[j]):
            covered.add(j)
    gaps = [j + 1 for j in range(s, e + 1) if j not in covered]
    if gaps:
        UNCOVERED.append((rel, gaps))
    COV_STAT[0] += len(covered)
    COV_STAT[1] += total

    rows = []
    for j in range(s, e + 1):
        cls = "cl" if _trivial(plain[j]) else ("cl ann" if j in covered else "cl gap")
        gattr = ' data-g="%d"' % gmap[j] if j in gmap else ""
        line = hl[j]
        if j in badges:
            line += '<sup class="mk">%s</sup>' % badges[j]
        rows.append('<div class="%s"%s><span class="cln">%d</span><span class="clc">%s</span></div>' % (cls, gattr, j + 1, line))
    rows = "".join(rows)

    notes_html = ""
    n_idx = 0
    for r in resolved:
        if r[0] is None:
            notes_html += '<div class="pt free"><span class="nl">注</span>%s</div>' % H.escape(r[2])
        else:
            label = CIRCLED[n_idx]
            n_idx += 1
            rng = "L%d" % (r[0] + 1) if r[0] == r[1] else "L%d–L%d" % (r[0] + 1, r[1] + 1)
            notes_html += '<div class="pt zoomable" data-g="%d"><b>%s</b><span class="nl">%s</span>%s</div>' % (n_idx, label, rng, H.escape(r[2]))

    cap = "L%d" % (s + 1) if s == e else "L%d<span class=\"dash\">–</span>L%d" % (s + 1, e + 1)
    link = "%s#f=%s&l=%d" % (BROWSER, rel, s + 1)
    figure = ('<figure class="codebox"><figcaption><span class="fpath">%s</span>'
              '<span class="frange">%s</span> · %d 行 · 注解 %d/%d'
              '<a class="flink" href="%s" target="_blank">完整文件 ⤴</a></figcaption>'
              '<div class="code">%s</div></figure>') % (H.escape(rel), cap, total, len(covered), total, link, rows)
    return figure, notes_html

Q = lambda en, zh, src: {"en": en, "zh": zh, "src": src}

# ---------------------------------------------------------------- figures & reused assets
DEEPD = r"C:\Users\computer\Documents\notes\C2C-缓存到缓存-深读.html"
_deep = open(DEEPD, encoding="utf-8").read()
def _svg(vb):
    m = re.search(r'<svg viewBox="%s".*?</svg>' % re.escape(vb), _deep, re.S)
    if not m:
        raise SystemExit("svg not found: " + vb)
    return m.group(0)
SVG_T2T = _svg("0 0 900 250")
SVG_FUSER = _svg("0 0 900 270")
SVG_LADDER = _svg("0 0 900 260")

def fig(cap, inner, note=""):
    return '<div class="fig"><div class="fig-cap">%s</div>%s%s</div>' % (cap, inner, ('<div class="fig-note">%s</div>' % note) if note else "")

FIG_T2T = fig("FIG. 01 — T2T 与 C2C 的信息流对比", SVG_T2T,
    "上：T2T 被迫穿过「文本」这一线性瓶颈，且需要两次编解码。下：C2C 把缓存直接投影融合，提供方输出 token 数为 0；融合本身有 90ms 并行开销。")

FIG_FUSER = fig("FIG. 03 — Fuser 结构（残差整合）", SVG_FUSER,
    "接收方缓存走虚线旁路，最终与「投影—加权—门控」后的外部信息相加：外部知识是增量注入，而非覆盖写入。消融显示这个设计值 24.18 个百分点。")

ORACLE_BARS = fig("FIG. 02 — 缓存增强实验（同长度对照）",
    '<div class="bar-row"><span class="bar-label">Direct（仅问题）</span><div class="bar-track"><div class="bar-fill" style="width:58.42%"></div></div><span class="bar-val">58.42</span></div>'
    '<div class="bar-row"><span class="bar-label">Few-shot（长缓存）</span><div class="bar-track"><div class="bar-fill" style="width:63.39%"></div></div><span class="bar-val">63.39</span></div>'
    '<div class="bar-row"><span class="bar-label">Oracle（同长度增强）</span><div class="bar-track"><div class="bar-fill v" style="width:62.34%"></div></div><span class="bar-val">62.34</span></div>',
    "关键对照是 Direct 58.42 → Oracle 62.34：缓存长度不变、仅语义被示例「富化」，精度 +3.92；Few-shot 63.39 是「真的多看几个例子」的参考线——Oracle 尚未超过它，但已逼近。数据：Table 1。")

def _dots(n):
    on = [1]*n + [0]*(100-n)
    seed = 20260919
    for i in range(99, 0, -1):
        seed = (seed*1664525 + 1013904223) % 4294967296
        j = int((seed/4294967296) * (i+1))
        on[i], on[j] = on[j], on[i]
    return "".join('<div class="dot' + (" on" if v else "") + '"></div>' for v in on)

GATE_DOTS = fig("FIG. 04 — 门控开启比例（每格 1%）",
    '<div class="dots-wrap">'
    '<div class="dots-block"><h4>通用训练 · OpenHermes2.5</h4><div class="dots">' + _dots(98) + '</div>'
    '<div class="pct">98.21%</div><div class="sub">门控几乎全开，真正的调制交给动态权重</div></div>'
    '<div class="dots-block"><h4>任务专训 · MMLU 训练集</h4><div class="dots">' + _dots(53) + '</div>'
    '<div class="pct">52.67%</div><div class="sub">稀疏开启：约一半层持续有用，开启层权重普遍高于 0.4</div></div>'
    '</div>',
    "数据：A.4.2。实心=门开启。")

ABLATION_CHAIN = fig("FIG. 05 — Fuser 组件消融（四基准平均精度）",
    '<div class="chain">'
    '<div class="chain-box"><div class="cb-title">Project · 覆盖替换</div><div class="cb-num">20.70</div><div class="cb-note">直接拿投影后的外部缓存顶替接收方</div></div>'
    '<div class="chain-arrow"><span class="arr">→</span><span class="arr-note">残差保真 +24.18</span></div>'
    '<div class="chain-box"><div class="cb-title">+ Fuse · 残差融合</div><div class="cb-num">44.88</div><div class="cb-note">双缓存融合后经残差加回</div></div>'
    '<div class="chain-arrow"><span class="arr">→</span><span class="arr-note">逐层门控 +3.07</span></div>'
    '<div class="chain-box" style="border-color:var(--vermilion)"><div class="cb-title">+ Gate · 完整 C2C</div><div class="cb-num" style="color:var(--vermilion)">47.95</div><div class="cb-note">每层可学习开关</div></div>'
    '</div>',
    "「覆盖式替换」的灾难性掉分说明：外部语义再强，抹掉接收方自身理解就是自毁。箭头上的差值即净收益：24.18 = 44.88 − 20.70；3.07 = 47.95 − 44.88（均为四基准 MMLU / ARC-C / OpenBook / C-Eval 的平均，Table 8）。")

TIME_STACK = fig("FIG. 07 — 单次查询时间账目（MMLU-Redux，Qwen2.5-0.5B → Qwen3-0.6B）",
    '<div class="tstack-row"><div class="tstack-title">T2T · 文字通信</div><div class="tstack">'
    '<span class="seg-prefill" style="width:2.6%"></span><span class="seg-decode" style="width:64.3%">逐字解码 1312ms</span><span class="seg-prefill" style="width:11.3%">231ms</span></div></div>'
    '<div class="tstack-row"><div class="tstack-title">C2C · 缓存融合</div><div class="tstack">'
    '<span class="seg-fusion" style="width:4.4%"></span><span class="seg-prefill" style="width:2.3%"></span><span class="seg-decode" style="width:15.1%">接收方解码 308ms</span></div></div>',
    "同一比例尺；朱红=缓存融合（90ms），深色=解码，灰=预填充。T2T 总计约 1596ms，C2C 约 445ms——90ms 融合是新增开销，不是免费午餐。数据：Table 3。")

ROUTE_STRIP = fig("FIG. 06 — kv_cache_index 逐位置路由",
    '<div class="strip">' + "".join('<span class="rsc on">[1,0]</span>' for _ in range(14)) + "".join('<span class="rsc off">[-1,0]</span>' for _ in range(8)) + '</div>',
    "前 n-1 个位置（提示段）标 [1,0]，走 1 号 Sharer 的缓存融合；其余标 [-1,0]，完全不投影——答案在接收方自己的语义里生成。示意基于 inference_example.py L100–101。")

FIG_LADDER = fig("FIG. 08 — GSM8K：单模型 → 多智能体流程 → C2C → 混合通道", SVG_LADDER,
    "纯 C2C（62.55）略高于多智能体 T2T（61.18）；真正拉满的是 T-C2C——文字解释 + 缓存融合的混合通道，78.01。数据：A.5.3。")

CLAIM_BOTTLENECK = Q("In existing designs, LLMs communicate through text, forcing internal representations to be transformed into output token sequences. This process both loses rich semantic information and incurs token-by-token generation latency.",
    "现有设计中，大模型通过文字交流，迫使内部表示被转换成输出词元序列；这一过程既丢失丰富的语义信息，又带来逐词元生成的延迟。","§1 Introduction")
CLAIM_QUESTION = Q("Can LLMs communicate beyond text?",
    "语言模型能否超越文字进行交流？","§1（全文核心提问）")
CLAIM_ORACLE = Q("Oracle experiments show that enriching the KV-Cache semantics can improve response quality without increasing cache size, supporting KV-Cache as an effective medium for inter-model communication.",
    "神谕实验表明，不增大缓存即可通过丰富其语义提升回答质量——KV-Cache 因此可作为模型间通信的有效介质。","Abstract")
CLAIM_PROJ = Q("Projection module concatenates the Receiver's KV-Cache with the Sharer's KV-Cache, then processes the concatenated features through a projection layer followed by a feature fusion layer.",
    "投影模块把接收方与提供方的 KV 缓存拼接，再经过投影层与特征融合层处理。","§3.3.2")
CLAIM_WEIGHT = Q("Dynamic weighting module applies an input-aware head modulation layer to dynamically reweight the projected information.",
    "动态加权模块用输入感知的头级调制层，动态调整投影信息的权重。","§3.3.2")
CLAIM_GUMBEL = Q("The gate applies a Gumbel-sigmoid with temperature annealing to smoothly transition from differentiable during training to binary at inference.",
    "门控采用带温度退火的 Gumbel-sigmoid，从训练时的可微状态平滑过渡到推理时的二值状态。","§3.3.2")
CLAIM_RESIDUAL = Q("To enhance the Receiver's KV-Cache without destructive overwriting of its information, the fuser is designed under a residual integration principle.",
    "为了增强接收方的缓存而不破坏性地覆盖其信息，融合器按「残差整合」原则设计。","§3.3.2")
CLAIM_FREEZE = Q("During training, we freeze both the Sharer and Receiver models, training only the C2C module for KV-Cache fusion.",
    "训练期间冻结提供方与接收方两个模型，只训练负责缓存融合的 C2C 模块。","§3.3.4")
CLAIM_PREFILL = Q("During the prefill stage, fuser Fn takes the nth layer cache of the Receiver Model Cn(X) and the corresponding G(n)th layer cache of the Sharer Model and generates the corresponding fused cache with residual connection.",
    "在预填充阶段，融合器取接收方第 n 层的缓存，与提供方对应层的缓存一起，生成带残差连接的融合缓存。","§3.3.1 Overview")
CLAIM_EFF = Q("T2T requires the Sharer to decode 80 output tokens, incurring 1312ms of decoding overhead, whereas C2C replaces this sequential decoding with parallel cache fusion in 90ms.",
    "T2T 需要提供方逐字解码 80 个 token、产生 1312ms 开销；C2C 用 90ms 的并行缓存融合替代这一顺序解码。","§4.2 Efficiency")
CLAIM_SPEED = Q("C2C achieves significant speedups of 3.46x, 1.51x, and 14.41x over T2T by eliminating intermediate text generation.",
    "通过消灭中间文本生成，C2C 相比 T2T 取得 3.46×、1.51×、14.41× 的显著加速。","§4.2")
CLAIM_RANK = Q("After cache-to-cache fusing, the effective ranks of K and V increased from 388 to 395 and from 532 to 560, respectively.",
    "缓存融合后，K 与 V 的有效秩分别从 388 升至 395、从 532 升至 560。","§4.5")
CLAIM_ALIGN = Q("We observed that the two selection strategies generally produce very similar results, with more than 80% of sequences yielding identical alignments across strategies.",
    "我们观察到两种选择策略通常给出非常接近的结果：超过 80% 的序列在两种策略下对齐完全一致。","§A.1.2")
CLAIM_TERM = Q("the final layers of both models are aligned first, then the penultimate layers, and so on in reverse order",
    "两个模型的最后一层先对齐，然后倒数第二层，如此反向回推。","§3.3.3")
CLAIM_MAIN = Q("After applying C2C, accuracy increases by an average of 11.00%, 9.64%, and 11.88% across the three Sharers. Compared with text-to-text communication, C2C achieves an average accuracy increase of 5.36%, 4.15%, and 3.06%.",
    "应用 C2C 后，三组 Sharer 下精度平均提升 11.00%、9.64%、11.88%；相比文字通信，C2C 平均再提升 5.36%、4.15%、3.06%。","§4.2")
CLAIM_WEAK = Q("Multi-LLM systems experience performance degradation when a much weaker Sharer provides noisy information to a stronger Receiver.",
    "当远弱于接收方的提供者输出噪声信息时，多模型系统性能会退化。","§5 Limitations")
CLAIM_ON = Q("scaling up the number of communicating LLMs with O(N) training cost remains an open problem.",
    "以 O(N) 训练成本扩展通信模型数量仍是一个开放问题。","§5 Limitations")
CLAIM_FAIL = Q("C2C may fail as the contextual understanding from the Sharer model is not always accurate and can mislead the Receiver into generating the wrong answer.",
    "C2C 可能失败：提供方的上下文理解并不总是准确的，可能误导接收方生成错误答案。","§4.5 / A.4.6")
CLAIM_TC2C = Q("The performance can be further elevated to 78.01 by using T-C2C, which lets the math interpreter generate the interpretation and use C2C on both the question and the interpretation.",
    "使用 T-C2C（让数学解释器先生成解释、再对问题与解释做缓存融合）可把表现进一步提升到 78.01。","§A.5.3")

# ---------------------------------------------------------------- units
UNITS = [
{"no":"01","id":"u01",
 "title":"先导实验：先证明「值不值得」","en":"The oracles — evidence before the product",
 "claim":"在给出系统之前，论文先做了两个「神谕」实验：其一，缓存长度不变、仅被示例「富化」，精度就上升；其二，一个模型的缓存经一个 3 层 MLP 变换后，落进另一个模型的表示空间。它们的正确读法是上界实验——回答「如果打通了，值不值得」，而不是演示怎么打通。",
 "cq":[CLAIM_ORACLE],
 "figtop":ORACLE_BARS,
 "pairs":[
   {"code":dict(rel="rosetta/model/oracle.py", a="class OracleRosettaModel(nn.Module):", b="projector_list: List[Projector] = []):"),
    "anns":[
      {"a":"class OracleRosettaModel", "b":"Drop in replacement for the standard transformers",
       "t":"独立的 oracle 编排器：先导实验的证据与主线产品分居——有自己的编排器与训练脚本（oracle_train.py + oracle.json），不侵入主线；写法与 RosettaModel 同构。"},
      {"a":"def __init__", "b":"projector_list: List[Projector] = []):",
       "t":"与主线相同的构造签名：模型列表 + 基座索引 + 逐层投影器。缓存增强与跨模型变换两条先导实验都从这套编排出发。一个冷静的备注：Oracle 62.34 并未超过 Few-shot 63.39——它的价值是「同长度、零额外 token」逼近多示例提示。"},
    ]},
 ],
 "recon":{"paper":"两个 oracle 支撑「KV-Cache 可作通信介质」的判断。","code":"oracle 线在源码里同样独立成套，与主线分开维护。",
          "tag":"吻合","verdict":"论证顺序在目录结构里被复刻：先验证，再实现。"}},

{"no":"02","id":"u02",
 "title":"融合器全貌与合流","en":"The fuser and the merge point",
 "claim":"论文把融合器描述为三个模块：投影、动态加权、可学习门控，且整体遵守「残差整合」。代码开头的类注释把这三件事写成了五条约束——投影用标准 MLP、拼接而非覆盖、标量门 + Gumbel、输入依赖的头级权重、target 保留。先读注释，再读实现，论文与代码在这里几乎逐句对齐。",
 "cq":[CLAIM_PROJ, CLAIM_WEIGHT],
 "figtop":FIG_FUSER,
 "pairs":[
   {"code":dict(rel="rosetta/model/projector.py", a="class C2CProjector(Projector):", b="over 1929 steps)"),
    "anns":[
      {"a":"class C2CProjector", "b":"Concise projector specialized",
       "t":"类注释即规格书：这是论文最终配置的固化版（精简投影器）——研究版 AllInOneProjector 的一个特例。"},
      {"a":"- Projections:", "b":"- Concat:",
       "t":"前两条约束：投影用标准 MLP（pre-RMSNorm + SwiGLU + 残差）；启用拼接并用线性层融合——对应论文「投影模块」。"},
      {"a":"- Gate:", "b":"- Weights:",
       "t":"门控与权重：标量门 + 训练期 Gumbel-sigmoid；权重是输入依赖的头级（head_merged）粒度——对应论文「动态加权 + 可学习门控」。"},
      {"a":"- Target preservation:", "b":"- Temperatures:",
       "t":"残差保留与温度：add_self=True、preserve_target_weight=False（只加不减）；门温度从 1.0 退火到 0.001、1929 步——对应论文「残差整合」与训练方案。"},
    ]},
   {"code":dict(rel="rosetta/model/projector.py", a="# Flatten heads", b="value_hidden = self.value_mlp1(value_hidden)"),
    "anns":[
      {"a":"# Flatten heads", "b":"target_value_flat =",
       "t":"flatten：把 (头数, 头维) 摊平成 H×Dh——不同头数、头维的模型才能放进同一长度拼接，对齐交给投影层学习。"},
      {"a":"# 1) concat", "b":"value_cat = torch.cat",
       "t":"拼接沿通道（dim=-1）而非相加：源与目标的信息一条不丢，由后续网络决定怎么用。"},
      {"a":"# 2) project to hidden dim", "b":"value_hidden = self.value_in",
       "t":"投影到 hidden_dim=1024：为两个模型的表示空间准备一张共同的「工作台」。"},
      {"a":"# 3) one-layer common embedding", "b":"value_hidden = self.value_mlp1",
       "t":"共享嵌入层：让源与目标的信息在分叉前先混合一次，再各奔投影与权重两条路。"},
    ]},
 ],
 "recon":{"paper":"「拼接 → 投影层 → 特征融合层」，外加输入感知的头级调制。","code":"flatten → torch.cat → key_in → RegularMLP；权重分支单独出（下一项核对）。",
          "tag":"吻合","verdict":"论文的模块描述即代码的调用链，无额外装置。"}},

{"no":"03","id":"u03",
 "title":"分叉与门控：论文没说完的那一半","en":"Two branches and a scalar switch",
 "claim":"论文强调门控「挑选受益的层」并「训练时软、推理时硬」。代码补足了论文没展开的部分：门是每层一个标量 logit；权重是每 token 每头一个标量、经 sigmoid 归一化后逐点调制。也就是说，「逐查询自适应」发生在权重路径，而「挑层」是训练后退火定型的二值开关。至于权重具体如何从输入算出，论文未展开——答案在下方 4a 路径的注解里。",
 "cq":[CLAIM_GUMBEL],
 "figbot":GATE_DOTS,
 "pairs":[
   {"code":dict(rel="rosetta/model/projector.py", a="# 4b) intermediate representation -> projected feature path", b="value_scalar = value_scalar.permute(0, 2, 1).unsqueeze(-1)"),
    "anns":[
      {"a":"# 4b)", "b":"projected_value = value_proj_hidden",
       "t":"投影路径（4b）：中间表示 → (L-2) 层 MLP → 线性层，产出目标模型的 (头数 × 头维)——候选的注入内容。"},
      {"a":"# 4a)", "b":"value_scalar = self.value_scalar_head",
       "t":"权重路径（4a）——「权重」怎么算：key_hidden（源+目标拼接后的共享嵌入）→ key_scalar_mlp2（1 层 MLP）→ key_scalar_head（线性层），得到每 token、每头一个标量 logit（形状 B×N×Ht）。权重是随输入实时算出的，不是固定参数。"},
      {"a":"key_scalar = key_scalar.permute", "b":"value_scalar = value_scalar.permute",
       "t":"形状对齐：把 (B, N, Ht) 转成 (B, Ht, N, 1)，便于与 key/value 张量逐元素相乘时广播；下一步的 sigmoid 在残差块（下一项）。"},
    ]},
   {"code":dict(rel="rosetta/model/projector.py", a="self.key_gate_logit = nn.Parameter(torch.tensor(0.0, dtype=dtype))"),
    "anns":[{"t":"初始 logit = 0：sigmoid 后 0.5，起手「一半怀疑」；每层一个标量门，训练后退火定型。"}]},
   {"code":dict(rel="rosetta/model/projector.py", a="# Key/value gates: element-wise Gumbel noise with scalar logits", b="value_gate = (value_gate_logit > 0).float()"),
    "anns":[
      {"a":"# Key/value gates", "b":"value_gate_logit = self.value_gate_logit.view",
       "t":"门 logit 广播成 (1,1,1,1)：标量门在这一步均匀作用于每个 token、每个头。"},
      {"a":"if self.training", "b":"value_gate = torch.sigmoid",
       "t":"训练分支：logit 加 Gumbel 噪声、除以温度再 sigmoid——可微的随机采样，梯度能穿过开合决策。"},
      {"a":"else:", "b":"value_gate = (value_gate_logit > 0).float()",
       "t":"推理分支：直接 (logit > 0) 二值化，温度不再参与——开关在训练结束时就定型。训练完成后：通用数据门控 98.21% 常开、任务专训 52.67% 稀疏（A.4.2）。"},
    ]},
   {"code":dict(rel="rosetta/model/projector.py", a="def update_temperature(self, step: int):", occ=2, b="self.gate_temperature.fill_(temp)"),
    "anns":[
      {"a":"def update_temperature", "b":"ratio = min",
       "t":"每步调用一次：按训练步推进退火进度（此处为 C2CProjector 版本；AllInOneProjector 另有一份带注释的同类实现）。"},
      {"a":"ratio = min", "b":"self.gate_temperature.fill_",
       "t":"指数退火：T = 1.0 × (0.001/1.0)^ratio，1929 步走完——与论文最终 checkpoint 步数一致。"},
    ]},
 ],
 "recon":{"paper":"门控「选择受益的目标层」；Gumbel-sigmoid 退火到二值。","code":"每层 1 个标量 logit；动态配比实际由 head 级权重承担；通用训练下门几乎全开。",
          "tag":"修正","verdict":"「毫秒级逐查询挑层」是传播口径；论文与代码实况是：挑层稀疏与否取决于训练数据，逐查询调节的是权重。"}},

{"no":"04","id":"u04",
 "title":"残差：一个加号写进消融里","en":"The plus sign, backed by the ablation",
 "claim":"「残差整合」不是修辞：代码里接收方缓存原样保留，外部信息以「门 × 权重」调制后的增量相加。论文的消融给这个加号标了价——覆盖式替换四基准平均 20.70，改为残差融合 44.88，再加门控 47.95；融合后 K/V 有效秩上升。设计决策与证据闭环。",
 "cq":[CLAIM_RESIDUAL, CLAIM_RANK],
 "figbot":ABLATION_CHAIN,
 "pairs":[
   {"code":dict(rel="rosetta/model/projector.py", a="# Normalize scalars (scalar_temperature=1.0)", b="output_value = target_value + value_gate * norm_value_scalar * projected_value"),
    "anns":[
      {"a":"# Normalize scalars", "b":"norm_value_scalar = torch.sigmoid",
       "t":"权重归一化：sigmoid 把 4a 算出的标量 logit 压到 (0,1)，成为「保留多少外部信息」的系数，随输入实时变化（注释写 scalar_temperature=1.0，除以 1.0 等价于直接 sigmoid）。"},
      {"a":"# Combine", "b":"output_value = target_value +",
       "t":"全仓库最重的一行：输出 = 接收方原缓存 +（层门 × 动态权重 × 投影特征）。三个乘数各司其职：门=整层通断（训练后定型）；权重=逐 token、逐头由输入实时算出；投影特征=外部内容本身。target 从未被写掉。"},
      {"free":True, "t":"证据 · 24.18 怎么来的：Table 8 四基准平均——Project（20.01/19.57/21.80/21.41）→ 20.70；+Fuse（43.36/51.65/47.60/36.91）→ 44.88；+Gate（42.92/54.52/52.60/41.77）→ 47.95。于是 24.18 = 44.88 − 20.70（换成残差融合的净收益）；3.07 = 47.95 − 44.88（再加门控的净收益）。"},
      {"free":True, "t":"证据 · 有效秩：K 388→395、V 532→560，增幅不大（约 2–5%）但方向一致（§4.5）。"},
    ]},
 ],
 "recon":{"paper":"残差整合原则；消融显示融合 > 投影替换。","code":"一行加法就是原则本身，且被论文消融独立验证。",
          "tag":"吻合","verdict":"全仓库最贵的标点符号：这个加号值 24.18 个百分点。"}},

{"no":"05","id":"u05",
 "title":"编排与路由：融合只发生在提示段","en":"Orchestration and the routing table",
 "claim":"论文描述融合发生在 prefill（一次并行投影），路由与多源细节主要在附录。代码把机制说得更直白：RosettaModel 靠一张逐位置路由表指挥——-1 不融合、0 自身、正数位掩码选 Sharer；训练与推理共用同一套表：前 n-1 个位置走融合，其余不投影。",
 "cq":[CLAIM_PREFILL],
 "figbot":ROUTE_STRIP,
 "pairs":[
   {"code":dict(rel="rosetta/model/wrapper.py", a="kv_cache_index: List of tensors with shape (B, sec_seq_len, 2).", b="bit i selects sharer at model_list[i+1]."),
    "anns":[
      {"a":"kv_cache_index: List of tensors", "b":"controls sharer selection",
       "t":"逐位置路由表：每个 token 一个 [源编号, 通道] 指令。"},
      {"a":"- -1: No projection", "t":"-1：不投影，只用接收方自己。"},
      {"a":"- 0: Self projection", "t":"0：自身投影（预留，未启用）。"},
      {"a":">0: Bitmask selecting sharers", "b":"bit i selects sharer",
       "t":"正数 = 位掩码：1/2 选 1、2 号 Sharer，3 = 两个都选，7 = 三个全选——多源融合靠位运算。"},
    ]},
   {"code":dict(rel="rosetta/train/dataset_adapters.py", a="def generate_kv_cache_index", b="return kv_cache_index"),
    "anns":[
      {"a":"def generate_kv_cache_index", "b":"Tensor with KV cache index",
       "t":"接口：给出指令段长度与全长，返回整条序列的逐位置路由。"},
      {"a":"assert instruction_length", "t":"校验：指令段不能长于全长。"},
      {"a":"instruction_index = torch.tensor", "b":"label_index = torch.tensor",
       "t":"前 instruction_length-1 个位置标 [1,0]（走 1 号 Sharer）；其余标 [-1,0]（不投影）——答案在接收方自己的语义里生长。"},
      {"a":"kv_cache_index = torch.cat", "b":"return kv_cache_index",
       "t":"拼成 (seq_len, 2) 返回——训练与推理共用同一份构造逻辑。"},
    ]},
   {"code":dict(rel="script/playground/inference_example.py", a="instruction_index = torch.tensor([1, 0]", b="kv_cache_index = [instruction_index, label_index]"),
    "anns":[
      {"a":"instruction_index = torch.tensor", "b":"label_index = torch.tensor",
       "t":"推理示例里同一套构造：指令段 [1,0] 走 1 号 Sharer，其余 [-1,0] 不投影。"},
      {"a":"kv_cache_index = [instruction_index, label_index]",
       "t":"拼成生成调用所需的 kv_cache_index（论文 §A.5.1：双 Sharer 无需额外训练即可再提升）。"},
    ]},
 ],
 "recon":{"paper":"融合在 prefill 阶段一次完成，可扩展多 Sharer。","code":"逐位置 [源编号, 通道] 表；融合只发生在提示段，生成段回归单模型。",
          "tag":"补充","verdict":"「答案在接收方自己的语义里生长」这一设计取舍，论文未强调，代码写在构造函数里。"}},

{"no":"06","id":"u06",
 "title":"效率：90ms 的来路与代价","en":"Where the 90ms comes from",
 "claim":"论文的效率主张有明确机制：提供方不再逐字生成，改由一次并行融合替代。但读数字要完整：1312ms→90ms 是「提供方解码 vs 融合开销」；端到端加速逐项为 3.46×、1.51×、14.41×，其中 14.41× 来自基座模型 T2T 失控的极端基线。90ms 本身是新增开销，不是免费。",
 "cq":[CLAIM_EFF, CLAIM_SPEED],
 "figbot":TIME_STACK,
 "pairs":[
   {"code":dict(rel="rosetta/model/wrapper.py", a="def generate(", b="for the base model stream."),
    "anns":[
      {"a":"def generate(", "b":"**kwargs,",
       "t":"自写生成循环的入口：参数列表与 HuggingFace generate 对齐（温度、采样、缓存开关……），但内部逻辑完全自持——为的是每一步都能精确控制缓存注入。"},
      {"a":"New generation loop", "b":"for the base model stream.",
       "t":"注释直述分工：prefill 与前向由本模块接管，采样走 rosetta.model.sampling.sample_token。提供方全程不解码（输出 token = 0）——90ms 融合替代 1312ms 解码的系统基础。测量条件：单卡 A100、batch 1、零样本。"},
    ]},
 ],
 "recon":{"paper":"平均 2.5× 加速（v2 摘要）；区间 3.46/1.51/14.41×。","code":"Sharers 不解码 + 一次性并行融合；融合本身消耗 90ms。",
          "tag":"修正","verdict":"「消灭延迟」指消灭中间文本延迟；总量级改善但非零成本，区间下限 1.51× 也应当被记住。"}},

{"no":"07","id":"u07",
 "title":"对齐：两套词表之间的桥","en":"Token and layer alignment",
 "claim":"跨模型拼缓存的前提是「口径」对齐：分词与层数。论文给的做法是分词逐 token 重编码（一对多取最大覆盖）、层数末端对齐；并给出一个值得信任的细节——两种一对多策略在超过 80% 的序列上结果一致。代码把这两个决策分别落在策略枚举与映射字段上。",
 "cq":[CLAIM_ALIGN, CLAIM_TERM],
 "pairs":[
   {"code":dict(rel="rosetta/model/aligner.py", a="class AlignmentStrategy(Enum):", b="corresponding LLM tokens for each SLM token."),
    "anns":[
      {"a":"class AlignmentStrategy", "b":"Strategies for handling",
       "t":"一对多映射的两种选择被定义为枚举——论文采纳的是 LONGEST 思路（最大覆盖）。"},
      {"a":'FIRST = "first"', "t":"FIRST：永远取第一个候选 token。"},
      {"a":'LONGEST = "longest"', "t":"LONGEST：取字符串最长者，保住最多表面信息。"},
      {"a":"class TokenAligner:", "b":"corresponding LLM tokens",
       "t":"桥梁本体：以接收方（SLM）分词为基准，为每个 token 找到提供方（LLM）的对应 token。两个策略在超过 80% 的序列上结果完全一致（A.1.2）；模板段 padding 与消息段重编码在 align_chat_messages（L531）；层对齐是配方字段 last_aligned。"},
    ]},
 ],
 "recon":{"paper":"词表对齐有损但稳健；层对齐取末端方案。","code":"TokenAligner + 配方字段 last_aligned，与论文 §3.3.3 / A.1 一一对应。",
          "tag":"吻合","verdict":"工程上最不性感、却决定各模型对能否接线的一层。"}},

{"no":"08","id":"u08",
 "title":"训练：只教投影器","en":"Freeze everything, train the fuser",
 "claim":"论文的训练方案极其克制：双方模型冻结，只训练融合模块；因此成本可以低到「300 步、不足 9 GPU 小时即接近最终效果」。代码与配方把这句话拆成可执行的三件套：冻结工具、freeze 字段、一份 1.6KB 的 JSON。",
 "cq":[CLAIM_FREEZE],
 "pairs":[
   {"code":dict(rel="script/train/SFT_train.py", a="def freeze_model(model: nn.Module):", b="Unfreeze only the projector parameters"),
    "anns":[
      {"a":"def freeze_model", "b":"param.requires_grad = False",
       "t":"冻结：把模型全部参数的 requires_grad 置 False——C2C 训练中双方模型的归宿。"},
      {"a":"def unfreeze_model", "b":"param.requires_grad = True",
       "t":"解冻：反向操作，供 baseline 训练模式使用。"},
      {"a":"def unfreeze_projectors", "b":"Unfreeze only the projector parameters",
       "t":"只暴露「解冻投影器」入口——C2C 训练时唯一被打开的参数组。"},
    ]},
   {"code":dict(rel="recipe/train_recipe/C2C_0.6+0.5.json", a='"model": {', b='"mapping": "last_aligned"'),
    "anns":[
      {"a":'"model": {', "b":'"teacher_model"',
       "t":"模型对声明：base = 接收方（Qwen3-0.6B），teacher = 提供方（Qwen2.5-0.5B-Instruct）。"},
      {"a":'"is_do_alignment"', "b":'"alignment_strategy"',
       "t":"对齐开关与策略字段（本配方走默认对齐流程）。"},
      {"a":'"projector": {', "b":'"anneal_steps"',
       "t":"投影器类型与参数：C2CProjector、hidden 1024、1929 步退火——与代码默认值一致，投影器是本配方唯一被训练的对象。"},
      {"a":'"mapping"', "t":"末端对齐：末层先配对、反向回推（论文 §3.3.3）。"},
      {"free":True, "t":"注 · training 段的 freeze 含 \"base\" 即 C2C 模式；8 卡 × batch 4 × 累积 8；OpenHermes 50 万条 1 epoch；论文 A.4.5：300 步（<9 GPU 小时）即可接近最终效果。"},
    ]},
 ],
 "recon":{"paper":"冻结双模型、只训融合模块；训练成本以 GPU 小时计。","code":"freeze_model() + 配方字段做到「配置即论文」；换模型对只需改 JSON。",
          "tag":"吻合","verdict":"旁挂模块的红利：复现门槛从「重训两个模型」降到「训一个小网络」。"}},
]

# ---------------------------------------------------------------- paper-only chapters
def qbox(q):
    return ('<div class="quote"><div class="en">"%s"</div><div class="zh">%s</div><div class="src">arXiv:2510.03215v2 · %s</div></div>'
            % (H.escape(q["en"]), H.escape(q["zh"]), H.escape(q["src"])))

BYPASS_Q = Q("C2C bypasses this issue, highlighting an interesting use case in which a weaker instruction-tuned Receiver can leverage a stronger base model's knowledge via C2C, even when base model cannot follow instructions.",
    "C2C 绕过了这一问题，展示了一个有意思的用例：较弱的指令微调接收方可以通过 C2C 利用更强基座模型的知识——哪怕后者根本不会听指令。","§4.2")
ECO_NAMED = Q("The Python package is named after the Rosetta Stone ... C2C translates KV-cache representations between otherwise independent LLMs, allowing them to speak a common language in a richer and more direct way.",
    "软件包以罗塞塔石碑命名……C2C 在相互独立的模型之间翻译 KV 缓存表示，让它们以更丰富、更直接的方式说上同一种语言。","官方 README")
ECO_COST = Q("With 300 training steps (less than 9 GPU hours), C2C achieves a comparable result to the final checkpoint.",
    "仅 300 个训练步（不足 9 GPU 小时），C2C 即可达到与最终检查点相当的效果。","§A.4.5 Training Cost")

INTRO = """
<section class="pch" id="intro"><div class="phead"><span class="pno">序</span>
  <div><h2>为什么需要 C2C：文字是条低速单行道</h2><div class="pen">The problem — text as a low-bandwidth channel</div></div></div>
<p>论文把「文字到文字」（T2T）通信的代价拆成三条：<b>信息瓶颈</b>——高维内部表示必须反复压缩成线性字符串、再由接收方解压，模型知识不同步时部分信号不可恢复（论文举例：Coder 想表达「&lt;p&gt; 在这里是段落分隔符」，输出成文字后，Writer 把它当成了别的东西）；<b>语言歧义</b>——习语、指代与模糊表达天然存在，MCP、A2A 等文本协议被点名「刚性模板不足以覆盖开放域协作」；<b>逐字延迟</b>——每次交换都要把上下文完整解码成 token 序列，这是顺序操作。</p>
__QB1__
__QB2__
<p>围绕这个问题，论文选择了一个更大胆的介质：KV-Cache——模型在预填充阶段为每个 token 算出的注意力键值记忆。它维度更高、信息更密，且「传输」可以并行完成，不必经过解码循环。下面这张图是全文的出发点：两条信息流的对照。</p>
__FIG_T2T__
<p class="pnote">本页结构：八项机制逐项「论文主张 × 代码实况」核对（每项附核对结论），随后是证据链、开源生态与时间线、边界与传播版本校验。所有数字与代码行号均可回查。</p>
</section>
"""

PAPER_ECO = """
<section class="pch" id="peco"><div class="phead"><span class="pno">生</span>
  <div><h2>开源生态：发布物与时间线</h2><div class="pen">What is actually released, and when</div></div></div>
<p><b>代码</b>：thu-nics/C2C（Apache-2.0，截至 2026-09-19 约 596 stars / 76 forks）；Python 包名 <b>rosetta</b>——取自罗塞塔石碑，一个把同一段文本写成多种文字的古老器物。命名本身就是方法论：C2C 是模型空间之间的翻译层。</p>
__QECO__
<p><b>权重与演示</b>：Hugging Face nics-efc/C2C_Fuser 放出 7 组预训练 Fuser，覆盖多条模型对；另有在线 Live Demo（并排对照）与 gradio 本地演示。多 Sharer 融合自 2025-12 起可用。</p>
<p><b>成本</b>：训练只更新投影器，官方实测 300 步即可接近最终效果——这也是「旁挂模块」设计的直接红利。</p>
__QCOST__
<div class="tl">
2025-10-03&nbsp;&nbsp;v1 上线 arXiv；代码开源；当日当选 Hugging Face Daily Papers #1<br>
2025-11&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Live Demo 上线 Hugging Face Spaces<br>
2025-12&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;多 Sharer 融合支持（初步）<br>
2026-01&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;论文被 ICLR 2026 接收<br>
2026-03-02&nbsp;&nbsp;&nbsp;v2 修订（本页引用版本）<br>
2026-09-19&nbsp;&nbsp;&nbsp;仓库约 596 stars · 76 forks（统计日）
</div>
<p class="pnote">社区也出现了第三方「中间件」与插件类早期项目（2026-09 新建，星标极少），使用前需自行甄别，不代表官方实现。</p>
</section>
"""

PAPER_EVIDENCE = """
<section class="pch" id="pev"><div class="phead"><span class="pno">证</span>
  <div><h2>证据链：数字都说了什么</h2><div class="pen">Reading the numbers — main results, efficiency, generalization</div></div></div>
<p>主结果（接收方固定 Qwen3-0.6B）：三组提供方下，C2C 比单模型平均高 11.00%、9.64%、11.88%，比文字通信再高 5.36%、4.15%、3.06%。数字的正确读法是两层对照：不融合有多差、用文字融合又有多差。</p>
__MAINQUOTE__
<table class="ptab">
  <thead><tr><th>基准</th><th>接收方单独</th><th>T2T 文字通信</th><th>C2C（Qwen2.5-0.5B / Llama3.2-1B / 4B-Base）</th></tr></thead>
  <tbody>
    <tr><td>MMLU-Redux</td><td class="n">35.53</td><td class="n">41.03</td><td class="n h1">42.92 <span class="dim">/</span> 44.42 <span class="dim">/</span> 43.95</td></tr>
    <tr><td>OpenBookQA</td><td class="n">39.20</td><td class="n">44.00</td><td class="n h2">52.60 <span class="dim">/</span> 47.80 <span class="dim">/</span> 53.20</td></tr>
    <tr><td>ARC-C</td><td class="n">41.04</td><td class="n">49.48</td><td class="n h2">54.52 <span class="dim">/</span> 53.39 <span class="dim">/</span> 55.39</td></tr>
    <tr><td>C-Eval</td><td class="n">32.04</td><td class="n">35.88</td><td class="n h1">41.77 <span class="dim">/</span> 40.77 <span class="dim">/</span> 42.79</td></tr>
  </tbody>
</table>
<p class="pnote">底色深浅对应增益幅度（朱红，仅供速览）。最戏剧性的单点：Qwen3-4B-Base 单独使用几乎不可用（MMLU-Redux 1.03%），T2T 要 7.54s 才能救回，C2C 用 0.45s 拿到 43.95%。</p>
__BYPASS__
<p><b>泛化侧</b>：五组异构模型对（Gemma3-1B、Qwen2.5-Math-1.5B、Qwen2.5-Coder-0.5B、以及角色互换）平均比 T2T 高 8.59%；角色互换后 C2C 仍 +5.05%（T2T 反而 −6.30%）。LongBench 随长度优势扩大：0–4k 37.31 vs 33.46；4–8k 34.01 vs 29.70；8k+ 30.72 vs 25.64。双 Sharer 融合无需额外训练即可叠加（59.17 → 59.81）。</p>
<p><b>Agent 流程</b>（GSM8K 案例研究，按 Cognify 工作流）：纯 C2C 62.55、略高于多智能体 T2T 61.18；真正拉满的是混合通道。</p>
__TC2CQUOTE__
__LADDER__
<p class="pnote">测量条件必须一起记住：全部为 0.5B–14B 小模型、单张 A100、batch size 1、零样本、选择题为主的基准。这是可信的「机制验证」，不是生产吞吐的承诺。</p>
</section>
"""

PAPER_BOUNDS = """
<section class="pch" id="pbd"><div class="phead"><span class="pno">界</span>
  <div><h2>边界：论文自己划的线</h2><div class="pen">Limitations, failure modes, and what is left open</div></div></div>
<p>论文没有把 C2C 说成万灵药，边界写得相当直白：弱提供方会把强接收方带偏；多模型扩展的 O(N) 训练成本仍是开放问题；缓存传播的不只是知识，还有错误。</p>
__WEAKQUOTE__
__FAILQUOTE__
<p><b>一个具体的失败案例</b>（A.4.6）：一道会计题，Qwen3-0.6B 本来答对；Qwen2.5-0.5B 的解题过程算错，通过 T2T 与 C2C 都被带偏——错误在缓存层面同样「直达」，没有校验层拦截。</p>
__ONQUOTE__
<p><b>规模外推</b>：实验上限 14B；对 70B+ 与真实生产 A/B 没有数据。论文把「隐私感知协作」「跨模态融合」「token 级路由」列为未来方向——它们目前是方向，不是结论。</p>
</section>
"""

CHECK_ROWS = [
 ("已收录 ICLR 2026，代码开源","arXiv 注释「Published in ICLR'26」；仓库 Apache-2.0，含权重与 Demo","属实"),
 ("推理速度飙升 2.0–2.5 倍","v2 摘要：平均 2.5×；README：2.0×；逐项 1.51×–14.41×","大体属实"),
 ("准确率最高暴涨 14.2%","「6.4–14.2% higher average accuracy」——14.2% 为区间上限；官方 README 另写 8.5–10.5% 与 3.0–5.0%（v1 时代口径）","属实（上限口径）"),
 ("比文字协作高整整 5%","「approximately 3.1–5.4%」——区间中值约 4%","基本属实"),
 ("彻底消灭中间文本、思维投影直连","提供方输出 token=0 属实；融合有 90ms 开销，信息以残差增量注入而非覆盖","方向对，机制有出入"),
 ("毫秒级自适应挑选关键层","门控推理时是定型二值开关；通用训练 98.21% 常开，任务专训 52.67%","夸大"),
 ("清华 + 无问芯穹等团队","机构含清华、无问芯穹、上海交大、港中文、SLAI、上海 AI Lab","属实（不止两家）"),
 ("注定载入史册","论文不含此类表述；可核实的是 HF 当日 #1、约 600 stars、ICLR 收录","观点，非论据"),
]

PAPER_CHECK = """
<section class="pch" id="pck"><div class="phead"><span class="pno">校</span>
  <div><h2>校验：传播版本 vs 论文原文</h2><div class="pen">Fact-checking the viral summary against the source</div></div></div>
<table class="ptab check">
  <thead><tr><th style="width:26%">传播说法</th><th style="width:52%">论文原文</th><th>核对</th></tr></thead>
  <tbody>__ROWS__</tbody>
</table>
<p class="pnote">论文尚未验证的部分：生产环境 A/B、70B+ 规模、开放式生成任务、多轮 Agent 工具调用、弱提供方带偏的系统性防御。C2C 证明的是「缓存比文字是更好的信道」，而不是「模型可以不要语言」。</p>
</section>
"""

# ---------------------------------------------------------------- style
STYLE = r"""
:root{--paper:#F6F5F0;--paper-deep:#EDECE5;--ink:#1C1B17;--ink-soft:#565349;--hairline:rgba(28,27,23,.28);--hairline-soft:rgba(28,27,23,.14);--vermilion:#A6341F;--navy:#1D2E4E;
--serif:Georgia,"Times New Roman","STSong","SimSun",serif;--sans:"Microsoft YaHei","微软雅黑","PingFang SC",sans-serif;--mono:Consolas,"Courier New",monospace}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{background:var(--paper);color:var(--ink);font-family:var(--serif);font-size:16px;line-height:1.95}
a{color:var(--navy);text-decoration:underline;text-decoration-style:dotted;text-underline-offset:3px}
a:hover{color:var(--vermilion)}
::selection{background:var(--vermilion);color:var(--paper)}
#progress{position:fixed;top:0;left:0;height:2px;width:100%;background:var(--vermilion);transform:scaleX(0);transform-origin:0 0;z-index:70}
.vframe{position:fixed;inset:12px;border:1px solid var(--hairline);pointer-events:none;z-index:55}
.vframe::after{content:"";position:absolute;inset:4px;border:1px solid var(--hairline-soft)}
.topbar{position:sticky;top:0;z-index:50;display:flex;align-items:center;gap:14px;background:var(--paper);border-bottom:1px solid var(--hairline);padding:8px 24px;font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-soft)}
.topbar .doc{color:var(--ink);white-space:nowrap}
.topbar .spacer{flex:1}
.nav-link{font-family:var(--mono);font-size:10.5px;border:1px solid var(--hairline);color:var(--ink-soft);padding:3px 10px;text-decoration:none;white-space:nowrap;text-transform:none}
.nav-link:hover{border-color:var(--ink);color:var(--ink)}
.mbtn{font-family:var(--mono);font-size:10.5px;border:1px solid var(--hairline);color:var(--ink-soft);padding:3px 10px;background:none;cursor:pointer;text-transform:none;letter-spacing:.04em}
.mbtn:hover{border-color:var(--ink);color:var(--ink)}
.mbtn[aria-pressed="true"]{border-color:var(--vermilion);color:var(--vermilion)}
.ctl{display:flex;gap:6px;align-items:center}
.ctl-lab{font-family:var(--mono);font-size:9.5px;letter-spacing:.16em;color:var(--ink-soft);text-transform:uppercase;margin-right:2px}
body.mode-skim .pair{display:none}
body.mode-skim .recon .rrow,body.mode-read .recon .rrow{display:none}
body.mode-skim .recon{padding-top:12px;padding-bottom:12px}
main{max-width:1220px;margin:0 auto;padding:0 26px 130px}
.letterhead{position:relative;padding:52px 0 6px}
.rule-double{border-top:3px solid var(--ink);border-bottom:1px solid var(--ink);height:5px;margin-bottom:36px}
.kicker{font-family:var(--mono);font-size:10.5px;letter-spacing:.26em;text-transform:uppercase;color:var(--vermilion);margin-bottom:16px}
h1{font-size:clamp(34px,4.6vw,56px);line-height:1.2}
h1 .q{color:var(--vermilion)}
.lede{font-size:18px;max-width:920px;margin-top:18px}
.subtitle-en{font-style:italic;font-size:15px;color:var(--ink-soft);margin-top:12px;max-width:920px}
.seal{position:absolute;right:4px;top:56px;width:60px;padding:11px 0;border:2px solid var(--vermilion);color:var(--vermilion);font-size:21px;font-weight:700;text-align:center;writing-mode:vertical-rl;letter-spacing:.4em;opacity:0;transform:rotate(-4deg)}
.seal.stamped{animation:stamp .5s cubic-bezier(.2,1.4,.4,1) forwards}
@keyframes stamp{0%{opacity:0;transform:rotate(-4deg) scale(1.5)}70%{opacity:1;transform:rotate(-4deg) scale(.96)}100%{opacity:.92;transform:rotate(-4deg) scale(1)}}
.auditband{display:grid;grid-template-columns:repeat(5,1fr);border:1px solid var(--hairline);margin:46px 0 0}
.auditband div{border-right:1px solid var(--hairline);padding:16px 18px}
.auditband div:last-child{border-right:0}
.auditband .an{font-size:clamp(24px,2.6vw,36px);line-height:1.1;font-variant-numeric:tabular-nums}
.auditband .al{font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;color:var(--ink-soft);margin-top:8px;text-transform:uppercase}
.toc{margin:44px 0 0;border-top:1px solid var(--hairline);padding-top:20px}
.toc-title{font-family:var(--mono);font-size:10px;letter-spacing:.24em;color:var(--ink-soft);text-transform:uppercase;margin-bottom:12px}
.toc ol{list-style:none;columns:2;column-gap:56px}
.toc li{break-inside:avoid;border-bottom:1px dotted var(--hairline);padding:5px 0;font-size:14px}
.toc .tno{font-family:var(--mono);font-size:10.5px;color:var(--vermilion);margin-right:10px}
.toc a{color:var(--ink);text-decoration:none}
.toc a:hover{color:var(--vermilion)}
.unit{margin:88px 0 0;padding-top:34px;border-top:1px solid var(--hairline)}
.uhead{display:flex;gap:16px;align-items:baseline;margin-bottom:14px}
.uno{font-family:var(--mono);font-size:13px;color:var(--vermilion);letter-spacing:.12em}
.uhead h2{font-size:clamp(23px,2.5vw,30px);line-height:1.4}
.uen{font-family:var(--mono);font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-soft);margin-top:8px}
.claim{border:1px solid var(--hairline);border-top:3px solid var(--vermilion);padding:16px 20px 18px;margin:0 0 22px;background:var(--paper)}
.claim .clabel{font-family:var(--mono);font-size:10px;letter-spacing:.2em;color:var(--vermilion);text-transform:uppercase;margin-bottom:10px}
.claim p{font-size:15.5px;line-height:1.95;max-width:980px}
.quote{margin-top:12px;border-left:2px solid var(--vermilion);background:var(--paper-deep);padding:10px 14px}
.quote .en{font-style:italic;font-size:13.5px;line-height:1.8}
.quote .zh{font-weight:700;font-size:13.5px;margin-top:5px;line-height:1.8}
.quote .src{font-family:var(--mono);font-size:9.5px;letter-spacing:.12em;color:var(--ink-soft);margin-top:7px;text-transform:uppercase}
.codewrap{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:6px 44px;align-items:start}
.stack{min-width:0}
.pair{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:0 44px;align-items:start;margin:16px 0 20px}
.pair-code{min-width:0}
.pair + .pair{border-top:1px dashed var(--hairline-soft);padding-top:18px}
.pair .marg{border-top:0}
.pair .marg .pt{font-size:13px}
sup.mk{color:var(--vermilion);font-weight:700;font-size:10px;margin-left:6px;border-bottom:1px solid currentColor}
.pt .nl{font-family:var(--mono);font-size:10px;color:var(--ink-soft);margin-right:6px;letter-spacing:.04em}
.pt.free .nl{color:var(--ink-soft);border:1px solid var(--hairline);padding:0 4px;line-height:1.4}
.cl.ann .clc{box-shadow:inset 2px 0 0 rgba(166,52,31,.28)}
.cl.gap .clc{box-shadow:inset 2px 0 0 rgba(28,27,23,.55);background:rgba(166,52,31,.08)}
.marg{min-width:0;font-family:var(--sans);font-size:13px;line-height:1.9}
.marg .pt{border-top:1px dotted var(--hairline);padding:10px 0 12px}
.marg .pt:first-child{border-top:0}
.marg .pt b{color:var(--vermilion);font-weight:400;font-family:var(--mono);font-size:10px;letter-spacing:.14em}
.recon{border:1px dashed var(--hairline);padding:14px 18px 16px;margin:22px 0 0;background:var(--paper-deep)}
.recon .rlabel{font-family:var(--mono);font-size:10px;letter-spacing:.2em;color:var(--vermilion);text-transform:uppercase;margin-bottom:10px}
.rrow{display:grid;grid-template-columns:86px 1fr;gap:12px;padding:7px 0;border-top:1px dotted var(--hairline);font-size:14px;font-family:var(--sans);line-height:1.85}
.rrow:first-of-type{border-top:0}
.rrow b{font-family:var(--mono);font-size:10px;letter-spacing:.1em;color:var(--ink-soft);text-transform:uppercase;font-weight:400;padding-top:4px}
.rverdict{margin-top:8px;padding-top:10px;border-top:1px solid var(--hairline);font-size:14.5px;font-family:var(--sans);line-height:1.85}
.rverdict b{color:var(--vermilion);font-family:var(--mono);font-size:10px;letter-spacing:.18em;text-transform:uppercase;margin-right:8px;font-weight:400}
.tag-ok{color:var(--navy)}
.tag-fix{color:var(--vermilion)}
.tag-add{color:var(--navy)}
.codebox{border:1px solid var(--hairline);background:var(--paper);margin:14px 0 18px}
.codebox figcaption{display:flex;align-items:center;gap:10px;border-bottom:1px solid var(--hairline);padding:7px 12px;font-family:var(--mono);font-size:10.5px;color:var(--ink-soft);flex-wrap:wrap}
.codebox .fpath{color:var(--ink)}
.codebox .frange{color:var(--vermilion)}
.codebox .flink{margin-left:auto;font-size:10px;text-decoration:none;white-space:nowrap}
.code{overflow-x:auto;padding:8px 0;position:relative;font-family:var(--mono);font-size:12.5px;line-height:1.72}
.cl{display:flex;height:22px;line-height:22px;position:relative;z-index:1;transition:background .24s cubic-bezier(.25,.8,.3,1)}
.cl:hover{background:rgba(166,52,31,.045)}
.cl[data-g]{cursor:zoom-in}
.cln{width:52px;flex:none;text-align:right;padding-right:14px;color:var(--ink-soft);opacity:.5;user-select:none;font-size:11px;transition:opacity .24s cubic-bezier(.25,.8,.3,1),color .24s cubic-bezier(.25,.8,.3,1)}
.clc{white-space:pre;padding-right:20px;transition:font-size .26s cubic-bezier(.25,.8,.3,1),opacity .26s cubic-bezier(.25,.8,.3,1),filter .26s cubic-bezier(.25,.8,.3,1)}
.codebox:hover .cln{opacity:.85;color:var(--vermilion)}
.code{background-image:repeating-linear-gradient(135deg, rgba(28,27,23,.012) 0 1px, transparent 1px 6px),linear-gradient(180deg, rgba(28,27,23,.02), transparent 16px, transparent calc(100% - 16px), rgba(28,27,23,.02))}
.codebox.focused .cl .clc{opacity:.3;font-size:11px;filter:blur(.6px)}
.codebox.focused .cl .cln{opacity:.2}
.codebox.focused .cl:hover{background:transparent}
.codebox.focused .cl.zoom .clc{opacity:1;font-size:15.5px;filter:none}
.codebox.focused .cl.zoom .cln{opacity:1;color:var(--vermilion)}
.codebox.focused .cl.zoom{cursor:zoom-out}
.glass-lens{position:absolute;z-index:0;height:0;border-radius:14px;pointer-events:none;opacity:0;
  background:rgba(255,255,255,.52);
  -webkit-backdrop-filter:blur(14px) saturate(170%);
  backdrop-filter:blur(14px) saturate(170%);
  box-shadow:0 10px 34px rgba(28,27,23,.13), inset 0 0 0 1px rgba(255,255,255,.65);
  transition:opacity .24s cubic-bezier(.25,.8,.3,1), top .28s cubic-bezier(.25,.8,.3,1), height .28s cubic-bezier(.25,.8,.3,1);
  will-change:top,height,opacity}
.glass-lens.on{opacity:1}
.marg .pt{transition:opacity .26s cubic-bezier(.25,.8,.3,1),filter .26s cubic-bezier(.25,.8,.3,1)}
.marg .pt.zoomable{cursor:zoom-in}
.marg.focused .pt{opacity:.4;filter:blur(.3px)}
.marg.focused .pt.zoom{opacity:1;filter:none;border-radius:12px;padding:10px 12px;
  background:rgba(255,255,255,.6);
  -webkit-backdrop-filter:blur(10px) saturate(160%);
  backdrop-filter:blur(10px) saturate(160%);
  box-shadow:0 6px 22px rgba(28,27,23,.12), inset 0 0 0 1px rgba(255,255,255,.6);
  border-left:2px solid var(--vermilion)}
.toc-note{margin-top:14px;font-size:12.5px;color:var(--ink-soft)}
.cm{color:var(--ink-soft);font-style:italic}
.st{color:var(--navy)}
.kw{color:var(--vermilion)}
.nu{color:var(--ink-soft)}
.jk{color:var(--navy);font-weight:700}
.pch{margin:96px 0 0;padding-top:36px;border-top:3px solid var(--ink)}
.phead{display:flex;gap:18px;align-items:baseline;margin-bottom:18px}
.pno{font-size:44px;line-height:1;color:var(--vermilion);font-weight:700}
.phead h2{font-size:clamp(24px,2.8vw,32px);line-height:1.4}
.pen{font-family:var(--mono);font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-soft);margin-top:8px}
.pch p{max-width:940px;margin:16px 0}
.ptab{width:100%;border-collapse:collapse;font-size:13px;margin:18px 0}
.ptab th,.ptab td{border:1px solid var(--hairline);padding:8px 11px;text-align:left;vertical-align:top;line-height:1.8}
.ptab thead th{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-soft);font-weight:400}
.ptab td.n{font-family:var(--mono);font-variant-numeric:tabular-nums}
.pnote{font-size:13.5px;color:var(--ink-soft)}
.finale{margin-top:96px;border-top:3px solid var(--ink);border-bottom:1px solid var(--ink);padding:36px 0 40px}
.finale h2{font-size:clamp(26px,3vw,34px);margin-bottom:26px}
.checktab{width:100%;border-collapse:collapse;font-size:13.5px;margin:10px 0 6px}
.checktab th,.checktab td{border:1px solid var(--hairline);padding:10px 12px;text-align:left;vertical-align:top;line-height:1.8}
.checktab thead th{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-soft);font-weight:400}
.checktab td.v{font-family:var(--mono);font-size:11.5px;white-space:nowrap}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:0;margin:26px 0 6px}
.card{border:1px solid var(--hairline);border-right:0;padding:18px 20px}
.card:last-child{border-right:1px solid var(--hairline)}
.card .ct{font-family:var(--mono);font-size:10px;letter-spacing:.18em;color:var(--vermilion);text-transform:uppercase;margin-bottom:10px}
.card .cc{font-family:var(--mono);font-size:12px;background:var(--paper-deep);border:1px solid var(--hairline-soft);padding:8px 10px;margin-bottom:10px;line-height:1.7}
.card p{font-size:13px;line-height:1.85}
.archive{margin-top:36px;font-size:13.5px;color:var(--ink-soft);line-height:2.1}
.archive b{font-family:var(--mono);font-size:10px;letter-spacing:.16em;color:var(--vermilion);text-transform:uppercase;margin-right:10px;font-weight:400}
.colophon{margin-top:40px;border:1px solid var(--hairline);padding:24px 28px;position:relative;font-size:13px;line-height:1.9}
.colophon::after{content:"";position:absolute;inset:5px;border:1px solid var(--hairline-soft);pointer-events:none}
@media(max-width:1120px){
  .codewrap{grid-template-columns:1fr}
  .pair{grid-template-columns:1fr}
  .cards{grid-template-columns:1fr}
  .card{border-right:1px solid var(--hairline);border-bottom:0}
  .card:last-child{border-bottom:1px solid var(--hairline)}
  .auditband{grid-template-columns:1fr 1fr}
  .auditband div{border-bottom:1px solid var(--hairline)}
  .stat-band{grid-template-columns:1fr 1fr}
  .stat-cell{border-bottom:1px solid var(--hairline)}
  .stat-cell:nth-child(2n){border-right:0}
  .seal{display:none}.vframe{display:none}.toc ol{columns:1}
}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}.seal.stamped{animation:none;opacity:.92}.codebox.focused .cl .clc,.marg.focused .pt{filter:none!important}}
:focus-visible{outline:2px solid var(--vermilion);outline-offset:2px}
.fig{border:1px solid var(--hairline);padding:18px 22px 16px;margin:22px 0;background:var(--paper)}
.fig-cap{font-family:var(--mono);font-size:10px;letter-spacing:.2em;color:var(--vermilion);text-transform:uppercase;margin-bottom:16px}
.fig-note{font-size:12.5px;line-height:1.85;color:var(--ink-soft);border-top:1px dotted var(--hairline);margin-top:14px;padding-top:10px}
.fig svg{display:block;width:100%;height:auto}
.bar-row{display:flex;align-items:center;gap:12px;margin:10px 0}
.bar-label{width:150px;flex:none;font-size:13px;text-align:right}
.bar-track{flex:1;height:15px;background:var(--paper-deep);border:1px solid var(--hairline-soft)}
.bar-fill{height:100%;background:var(--ink)}
.bar-fill.v{background:var(--vermilion)}
.bar-val{width:60px;flex:none;font-family:var(--mono);font-size:12.5px;font-variant-numeric:tabular-nums}
.dots-wrap{display:flex;gap:56px;flex-wrap:wrap}
.dots-block h4{font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-soft);font-weight:400;margin-bottom:12px}
.dots{display:grid;grid-template-columns:repeat(10,15px);gap:4px}
.dot{width:15px;height:15px;border:1px solid var(--hairline)}
.dot.on{background:var(--ink);border-color:var(--ink)}
.dots-block .pct{font-size:24px;font-variant-numeric:tabular-nums;margin-top:12px;line-height:1}
.dots-block .sub{font-size:11.5px;color:var(--ink-soft);margin-top:6px;line-height:1.7}
.chain{display:flex;flex-wrap:wrap;gap:0}
.chain-box{border:1px solid var(--ink);padding:14px 16px;min-width:150px;flex:1}
.chain-box .cb-title{font-family:var(--mono);font-size:10px;letter-spacing:.14em;color:var(--ink-soft);text-transform:uppercase;margin-bottom:8px}
.chain-box .cb-num{font-size:24px;font-variant-numeric:tabular-nums;line-height:1}
.chain-box .cb-note{font-size:11.5px;color:var(--ink-soft);margin-top:8px;line-height:1.7}
.chain-arrow{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 10px;gap:6px;flex:none}
.chain-arrow .arr{font-family:var(--mono);font-size:16px;color:var(--vermilion)}
.chain-arrow .arr-note{font-family:var(--mono);font-size:9px;color:var(--ink-soft);writing-mode:vertical-rl}
.tstack-row{margin:14px 0 20px}
.tstack-title{font-family:var(--mono);font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-soft);margin-bottom:8px}
.tstack{display:flex;height:28px;border:1px solid var(--hairline)}
.tstack span{display:flex;align-items:center;justify-content:center;font-family:var(--mono);font-size:10px;color:var(--paper);overflow:hidden;white-space:nowrap}
.seg-prefill{background:var(--ink-soft)}
.seg-decode{background:var(--ink)}
.seg-fusion{background:var(--vermilion)}
.strip{display:flex;gap:4px;flex-wrap:wrap}
.rsc{font-family:var(--mono);font-size:10px;padding:3px 6px;border:1px solid var(--hairline)}
.rsc.on{background:var(--paper-deep);border-color:var(--ink);color:var(--ink)}
.rsc.off{color:var(--ink-soft);border-style:dashed}
.tl{font-family:var(--mono);font-size:12.5px;line-height:2.1;border:1px solid var(--hairline);padding:14px 18px;background:var(--paper-deep);margin:18px 0}
.h1{background:rgba(166,52,31,.05)}
.h2{background:rgba(166,52,31,.10)}
.h3{background:rgba(166,52,31,.16)}
.dim{color:var(--ink-soft)}
.stat-band{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--hairline);margin:34px 0 0}
.stat-cell{border-right:1px solid var(--hairline);padding:18px 18px 16px}
.stat-cell:last-child{border-right:0}
.stat-num{font-size:clamp(30px,3.2vw,46px);line-height:1.05;font-variant-numeric:tabular-nums}
.stat-num em{font-style:normal;color:var(--vermilion)}
.stat-label{font-family:var(--mono);font-size:10px;letter-spacing:.12em;color:var(--ink-soft);margin-top:10px;line-height:1.8}
"""

# ---------------------------------------------------------------- build
def build():
    toc = '<li><span class="tno">序</span><a href="#intro">为什么需要 C2C</a></li>'
    toc += "".join('<li><span class="tno">%s</span><a href="#%s">%s</a></li>' % (u["no"], u["id"], H.escape(u["title"])) for u in UNITS)
    toc += '<li><span class="tno">证</span><a href="#pev">证据链：数字都说了什么</a></li>'
    toc += '<li><span class="tno">生</span><a href="#peco">开源生态与时间线</a></li>'
    toc += '<li><span class="tno">界</span><a href="#pbd">边界：论文自己划的线</a></li>'
    toc += '<li><span class="tno">校</span><a href="#pck">校验：传播版本 vs 论文原文</a></li>'

    body = []
    for u in UNITS:
        cq = "".join(qbox(q) for q in u["cq"])
        pairs = ""
        for pr in u["pairs"]:
            block_html, notes_html = code_block(pr["code"]["rel"], pr["code"]["a"], pr["code"].get("b"), pr.get("anns"), pr["code"].get("occ", 1))
            pairs += '<div class="pair"><div class="pair-code">%s</div><aside class="marg">%s</aside></div>' % (block_html, notes_html)
        r = u["recon"]
        tagcls = {"吻合":"tag-ok","修正":"tag-fix","补充":"tag-add"}.get(r["tag"],"tag-ok")
        body.append(
            '<section class="unit" id="%s">'
            '<div class="uhead"><span class="uno">%s</span><div><h2>%s</h2><div class="uen">%s</div></div></div>'
            '<div class="claim"><div class="clabel">论文 · 主张（解读）</div><p>%s</p>%s</div>'
            '%s'
            '%s'
            '%s'
            '<div class="recon"><div class="rlabel">核对 · Reconciliation</div>'
            '<div class="rrow"><b>论文口径</b><span>%s</span></div>'
            '<div class="rrow"><b>代码实况</b><span>%s</span></div>'
            '<div class="rverdict"><b class="%s">%s</b>%s</div></div>'
            '</section>' % (u["id"], u["no"], H.escape(u["title"]), H.escape(u["en"]),
                            H.escape(u["claim"]), cq, u.get("figtop",""), pairs, u.get("figbot",""),
                            H.escape(r["paper"]), H.escape(r["code"]), tagcls, H.escape(r["tag"]), H.escape(r["verdict"])))

    pev = (PAPER_EVIDENCE.replace("__MAINQUOTE__", qbox(CLAIM_MAIN))
                        .replace("__TC2CQUOTE__", qbox(CLAIM_TC2C))
                        .replace("__BYPASS__", qbox(BYPASS_Q))
                        .replace("__LADDER__", FIG_LADDER))
    intro = (INTRO.replace("__QB1__", qbox(CLAIM_BOTTLENECK))
                  .replace("__QB2__", qbox(CLAIM_QUESTION))
                  .replace("__FIG_T2T__", FIG_T2T))
    peco = (PAPER_ECO.replace("__QECO__", qbox(ECO_NAMED))
                     .replace("__QCOST__", qbox(ECO_COST)))
    pbd = (PAPER_BOUNDS.replace("__WEAKQUOTE__", qbox(CLAIM_WEAK))
                      .replace("__FAILQUOTE__", qbox(CLAIM_FAIL))
                      .replace("__ONQUOTE__", qbox(CLAIM_ON)))
    rows = "".join('<tr><td>%s</td><td>%s</td><td class="v">%s</td></tr>' % (H.escape(a), H.escape(b), H.escape(c)) for a, b, c in CHECK_ROWS)
    pck = PAPER_CHECK.replace("__ROWS__", rows)

    checklist = "".join(
        '<tr><td>%s</td><td>%s</td><td>%s</td><td class="v">%s</td></tr>' % (u["no"], H.escape(u["title"]), H.escape(u["recon"]["code"]), H.escape(u["recon"]["tag"]))
        for u in UNITS)

    cards = "".join('<div class="card"><div class="ct">%s</div><div class="cc">%s</div><p>%s</p></div>' % (a, b, c) for a, b, c in [
        ("一个加号","output = target + gate · σ(weight) · projected","projector.py L1009 —— 覆盖式替换平均 20.70；残差融合 44.88；加门控 47.95。"),
        ("一个开关","σ((logit + Gumbel) / T) 训练 →（logit > 0）推理","projector.py L998 / L1001 —— 每层一个标量门；退火 1.0→0.001、1929 步。"),
        ("一张路由表","[-1,0] 不融合 · [1,0] 走 1 号 · 位掩码选多源","dataset_adapters.py L493 —— 融合只发生在提示段。"),
    ])

    page = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cache-to-Cache：论文与源码解读</title>
<style>__STYLE__</style>
</head>
<body class="mode-read">
<div id="progress"></div>
<div class="vframe" aria-hidden="true"></div>
<header class="topbar">
  <span class="doc">Cache-to-Cache · 论文与源码解读 · thu-nics/C2C @113c3a9</span>
  <span class="ctl"><span class="ctl-lab">阅读</span>
    <button class="mbtn" id="m-skim" aria-pressed="false">速读</button>
    <button class="mbtn" id="m-read" aria-pressed="true">精读</button>
    <button class="mbtn" id="m-full" aria-pressed="false">全量</button>
  </span>
  <span class="spacer"></span>
  <a class="nav-link" href="C2C-缓存到缓存-深读.html">论文深读</a>
  <a class="nav-link" href="C2C-源码浏览器.html" target="_blank">源码浏览器</a>
  <a class="nav-link" href="C2C-代码仓库-投射.html">代码仓库</a>
</header>
<main>
  <section class="letterhead">
    <div class="rule-double"></div>
    <div class="kicker">Cache-to-Cache · 清华大学 &amp; 无问芯穹等 · ICLR 2026</div>
    <h1>Cache-to-Cache<br>论文与源码解读</h1>
    <p class="lede">这份文件把论文与源码放在同一条流水线上核对：每一项先读<b>论文主张</b>（附原文证词），再看<b>代码实况</b>（逐字源码 + 右缘解读，全部行 100% 覆盖），最后给出<b>核对结论</b>。顶部「阅读」可切换层次：<b>速读</b>≈8 分钟（只留主张、图表与结论，论文式流）· <b>精读</b>（默认，含全部代码注解）· <b>全量</b>（再展开核对台账）。</p>
    <p class="subtitle-en">"Direct Semantic Communication Between Large Language Models — a claim-by-claim reading against the open-source implementation"</p>
    <div class="seal" id="seal">解读</div>
  </section>
  <section class="stat-band" aria-label="关键数字">
    <div class="stat-cell"><div class="stat-num">2.5<em>×</em></div><div class="stat-label">平均推理延迟加速（对比文字通信 T2T，v2 摘要口径）</div></div>
    <div class="stat-cell"><div class="stat-num">14.2<em>%</em></div><div class="stat-label">单模型最高平均精度增益（区间 6.4–14.2%）</div></div>
    <div class="stat-cell"><div class="stat-num">90<em>ms</em></div><div class="stat-label">KV 缓存融合耗时，替代 1312ms 的逐字解码开销</div></div>
    <div class="stat-cell"><div class="stat-num">0</div><div class="stat-label">Sharer 侧生成的中间文本 token 数</div></div>
  </section>
  <section class="auditband" aria-label="核对统计">
    <div><div class="an">8</div><div class="al">项机制核对</div></div>
    <div><div class="an">15</div><div class="al">段逐字源码</div></div>
    <div><div class="an">5</div><div class="al">吻合</div></div>
    <div><div class="an">2</div><div class="al">修正</div></div>
    <div><div class="an">1</div><div class="al">补充</div></div>
  </section>
  <nav class="toc">
    <div class="toc-title">目录 · Contents</div>
    <ol>__TOC__</ol>
    <p class="toc-note">放大镜：悬停代码行或右缘注解 → 该区间被一张「毛玻璃卡片」托起并放大，其余行缩略失焦（iOS 玻璃质感）；点击钉住，Esc 或点空白复位。</p>
  </nav>
  __INTRO__
  __BODY__
  __PEV__
  __PECO__
  __PBD__
  __PCK__
  <section class="finale">
    <h2>尾声 · 核对一览</h2>
    <table class="checktab">
      <thead><tr><th style="width:6%">项</th><th style="width:30%">核对项</th><th style="width:46%">代码实况（摘要）</th><th>结论</th></tr></thead>
      <tbody>__CHECKLIST__</tbody>
    </table>
    <h2 style="margin-top:44px">记住三行</h2>
    <div class="cards">__CARDS__</div>
    <div class="archive"><b>档案柜</b>
      <a href="C2C-缓存到缓存-深读.html">论文深读副本（18 章 · 9 图）</a> ·
      <a href="C2C-源码浏览器.html" target="_blank">全量源码浏览器（81 文件 · 39 脚注）</a> ·
      <a href="C2C-代码仓库-投射.html">代码仓库总览</a> ·
      <a href="C2C-源码详解.html">代码优先版（前一版设计 · 存档）</a>
    </div>
    <div class="colophon">源码逐字摘自 <a href="https://github.com/thu-nics/C2C" target="_blank" rel="noopener">thu-nics/C2C</a> commit 113c3a9（行号即源文件真实行号）；论文引文逐字摘自 arXiv:2510.03215v2。主张解读与核对结论为本文档观点，不代表论文作者及任何机构；数字口径以论文 v2 为准。</div>
  </section>
</main>
<script>
(function(){
  "use strict";
  var progress=document.getElementById('progress');
  function onScroll(){
    var h=document.documentElement,m=h.scrollHeight-h.clientHeight;
    progress.style.transform='scaleX('+(m>0?h.scrollTop/m:0)+')';
  }
  window.addEventListener('scroll',onScroll,{passive:true});onScroll();
  var seal=document.getElementById('seal');
  setTimeout(function(){seal.classList.add('stamped')},500);
  var modeBtns = {skim:document.getElementById('m-skim'), read:document.getElementById('m-read'), full:document.getElementById('m-full')};
  function setMode(m){
    document.body.classList.remove('mode-skim','mode-read','mode-full');
    document.body.classList.add('mode-' + m);
    for(var k in modeBtns){ modeBtns[k].setAttribute('aria-pressed', String(k === m)); }
  }
  for(var mk in modeBtns){ (function(k){ modeBtns[k].addEventListener('click', function(){ setMode(k); }); })(mk); }
  var pin = null, hoverTimer = null, clearTimer = null, active = null;
  function positionLens(box, g){
    if(!box || !g){ return; }
    var codeEl = box.querySelector('.code');
    if(!codeEl){ return; }
    var lines = box.querySelectorAll('.cl[data-g="' + g + '"]');
    if(!lines.length){ return; }
    var lens = codeEl.querySelector('.glass-lens');
    if(!lens){ lens = document.createElement('div'); lens.className = 'glass-lens'; codeEl.insertBefore(lens, codeEl.firstChild); }
    var cr = codeEl.getBoundingClientRect();
    var f = lines[0].getBoundingClientRect();
    var l = lines[lines.length - 1].getBoundingClientRect();
    lens.style.left = (codeEl.scrollLeft + 10) + 'px';
    lens.style.width = Math.max(120, codeEl.clientWidth - 20) + 'px';
    lens.style.top = (f.top - cr.top + codeEl.scrollTop - 4) + 'px';
    lens.style.height = (l.bottom - f.top + 8) + 'px';
    lens.classList.add('on');
  }
  function removeFocus(){
    active = null;
    Array.prototype.forEach.call(document.querySelectorAll('.codebox.focused, .marg.focused, .cl.zoom, .pt.zoom'), function(el){
      el.classList.remove('focused','zoom');
      if(el.classList.contains('codebox')){ el.removeAttribute('data-focus'); }
    });
    Array.prototype.forEach.call(document.querySelectorAll('.glass-lens.on'), function(el){ el.classList.remove('on'); });
  }
  function applyFocus(g, box, marg){
    if(!box || !g){ return; }
    removeFocus();
    active = {g: g, box: box};
    box.classList.add('focused');
    box.setAttribute('data-focus', g);
    Array.prototype.forEach.call(box.querySelectorAll('.cl[data-g="' + g + '"]'), function(l){ l.classList.add('zoom'); });
    if(marg){
      marg.classList.add('focused');
      Array.prototype.forEach.call(marg.querySelectorAll('.pt[data-g="' + g + '"]'), function(p){ p.classList.add('zoom'); });
    }
    positionLens(box, g);
  }
  document.addEventListener('scroll', function(e){
    if(active && e.target && e.target.classList && e.target.classList.contains('code')){ positionLens(active.box, active.g); }
  }, true);
  function groupTarget(e){
    var t = e.target;
    if(!t || !t.closest){ return null; }
    var el = t.closest('.cl[data-g]') || t.closest('.pt[data-g]');
    if(!el){ return null; }
    var pair = el.closest('.pair');
    if(!pair){ return null; }
    return {g: el.getAttribute('data-g'), pair: pair};
  }
  document.addEventListener('mouseover', function(e){
    if(pin){ return; }
    var hit = groupTarget(e);
    clearTimeout(clearTimer);
    if(!hit){
      clearTimeout(hoverTimer);
      clearTimer = setTimeout(function(){ if(!pin){ removeFocus(); } }, 240);
      return;
    }
    var box = hit.pair.querySelector('.codebox');
    if(box && box.classList.contains('focused') && box.getAttribute('data-focus') === hit.g){ return; }
    clearTimeout(hoverTimer);
    hoverTimer = setTimeout(function(){
      if(pin){ return; }
      applyFocus(hit.g, hit.pair.querySelector('.codebox'), hit.pair.querySelector('.marg'));
    }, 90);
  });
  document.addEventListener('click', function(e){
    var hit = groupTarget(e);
    if(hit){
      if(pin && pin.g === hit.g && pin.pair === hit.pair){
        pin = null; removeFocus();
      } else {
        pin = hit;
        applyFocus(hit.g, hit.pair.querySelector('.codebox'), hit.pair.querySelector('.marg'));
      }
      return;
    }
    pin = null;
    removeFocus();
  });
  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape'){ pin = null; removeFocus(); }
  });
})();
</script>
</body>
</html>"""
    if UNCOVERED:
        for rel, lines in UNCOVERED:
            print("UNCOVERED", rel, "lines:", lines)
        raise SystemExit("coverage incomplete: %d block(s) with gaps" % len(UNCOVERED))

    page = (page.replace("__STYLE__", STYLE).replace("__TOC__", toc)
                .replace("__INTRO__", intro).replace("__BODY__", "".join(body))
                .replace("__PEV__", pev).replace("__PECO__", peco).replace("__PBD__", pbd).replace("__PCK__", pck)
                .replace("__CHECKLIST__", checklist).replace("__CARDS__", cards))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("out:", OUT, "| size:", round(len(page.encode("utf-8"))/1024), "KB | units:", len(UNITS),
          "| coverage:", "%d/%d lines" % (COV_STAT[0], COV_STAT[1]))

if __name__ == "__main__":
    build()

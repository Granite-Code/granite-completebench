import json
from functools import cache, partial
from typing import Literal, TypedDict

import torch.multiprocessing as mp
from tqdm import tqdm
from tree_sitter import Language, Parser

from eval_utils import (
    postprocess_code_lines,
    extract_identifiers,
    cal_edit_sim,
    remove_comments
)
import os

class Metrics(TypedDict):
    em: float
    es: float
    stop: float
    id_em: float
    id_precision: float
    id_recall: float
    id_f1: float
    total: int


def compute_id_match(pred_ids, target_ids):
    pred_ids = list(set(pred_ids))
    target_ids = list(set(target_ids))
    tp = 0
    fp = 0
    fn = 0
    for pid in pred_ids:
        if pid in target_ids:
            tp += 1
        else:
            fp += 1
    for tid in target_ids:
        if tid not in pred_ids:
            fn += 1
    return tp, fp, fn


def compute_edit_sim(samples):
    refs, hyps = [], []
    for s in samples:
        refs.append(s["target"])
        hyps.append(s["pred"])
    return cal_edit_sim(refs, hyps)


TruncationList = list[Literal['expression', 'suffix', 'close']]


def truncate_at_suffix(prediction: str, suffix: str):
    # This duplicates the handling in
    # continue/autocomplete/filtering/streamTransforms/charStream.ts:stopAtStartOf

    sequence_length = 20
    if len(suffix) < sequence_length:
        return prediction

    targetPart = suffix.lstrip()[0:int(sequence_length * 1.5)]

    for i in range(0, len(prediction) - sequence_length):
        if prediction[i:i + sequence_length] in targetPart:
            return prediction[0:i]

    return prediction


def check_for_errors(tree):
    cursor = tree.walk()
    has_error: bool = False

    def traverse():
        nonlocal has_error

        node = cursor.node
        if node.is_error or node.is_missing:
            has_error = True

        if cursor.goto_first_child():
            traverse()
            while not has_error and cursor.goto_next_sibling():
                traverse()

            cursor.goto_parent()

    traverse()
    return has_error


def truncate_to_close(parser: Parser, prefix, prediction: str, suffix: str):
    suffix_stripped = suffix.lstrip()
    if len(suffix_stripped) == 0:
        return prediction
    close_char = suffix_stripped[0]
    if close_char not in "]})":
        return prediction

    prefix_bytes = bytes(prefix, "utf8")
    pred_bytes = bytes(prediction, "utf8")
    close_bytes = bytes(close_char, "utf8")
    suffix_bytes = bytes(suffix, "utf8")
    suffix_close_offset = suffix_bytes.find(close_bytes)

    pred_close_offset = pred_bytes.find(close_bytes)
    while pred_close_offset >= 0:
        pred_selection = pred_bytes[0:pred_close_offset]
        contents = prefix_bytes + pred_selection + suffix_bytes[suffix_close_offset:]
        tree = parser.parse(contents)
        if not check_for_errors(tree):
            if pred_selection.endswith(suffix_bytes[0:suffix_close_offset]):
                pred_selection = pred_selection[0:-suffix_close_offset]
            return pred_selection.decode("utf-8")

        pred_close_offset = pred_bytes.find(close_bytes, pred_close_offset + 1)

    return prediction


def truncate_to_dedent(prefix, pred, suffix):
    prefix_bytes = bytes(prefix, "utf8")
    pred_bytes = bytes(pred, "utf8")
    suffix_bytes = bytes(pred, "utf8")

    last_prefix_line = prefix.split("\n")[-1]
    try:
        first_suffix_line = next(l for l in suffix.split("\n") if l.strip() != "")
    except StopIteration:
        first_suffix_line = None

    indent = len(last_prefix_line) - len(last_prefix_line.lstrip())
    next_indent = len(first_suffix_line) - len(first_suffix_line.lstrip()) if first_suffix_line is not None else 0

    pos = 0
    for line in pred.split("\n"):
        if pos > 0 and line.strip() != "":
            line_indent = len(line) - len(line.lstrip())
            if line_indent <= next_indent and next_indent < indent:
                return pred[0:pos].rstrip()
        pos += len(line) + 1

    return pred


def get_treesitter_language(lang: str):
    if lang == "python":
        import tree_sitter_python
        return Language(tree_sitter_python.language())
    elif lang == "csharp":
        import tree_sitter_c_sharp
        return Language(tree_sitter_c_sharp.language())
    elif lang == "java":
        import tree_sitter_java
        return Language(tree_sitter_java.language())
    elif lang == "cpp":
        import tree_sitter_cpp
        return Language(tree_sitter_cpp.language())
    elif lang == "typescript":
        import tree_sitter_typescript
        return Language(tree_sitter_typescript.language_typescript())
    elif lang == "tsx":
        import tree_sitter_typescript
        return Language(tree_sitter_typescript.language_tsx())
    else:
        raise RuntimeError(f"Unknown language {lang}")


@cache
def get_parser(lang: str):
    return Parser(get_treesitter_language(lang))


def process_examples(lang: str, truncate: TruncationList, args):
    sample, ex = args
    if lang == 'typescript' and sample["metadata"]["file"].endswith(".tsx"):
        lang = "tsx"

    prediction: str = sample["pred"]
    assert prediction is not None
    for method in truncate:
        if method == 'expression':
            prediction = postprocess_code_lines(ex["prompt"], prediction, get_parser(lang), lang)
        elif method == 'suffix':
            prediction = truncate_at_suffix(prediction, sample["right_context"])
        elif method == 'close':
            if lang == "python":
                prediction = truncate_to_dedent(ex["prompt"], prediction, sample["right_context"])
            else:
                prediction = truncate_to_close(get_parser(lang), ex["prompt"], prediction, sample["right_context"])

    stopped = sample["stop_reason"] != "length" or len(prediction) < len(sample["pred"])

    prediction = remove_comments(prediction)
    target = ex["groundtruth"]
    target = remove_comments(target)

    pred_lines = [l.strip() for l in prediction.split("\n") if l.strip()]
    gt_lines = [l.strip() for l in target.split("\n") if l.strip()]
    em_label = int(pred_lines == gt_lines)

    pred_ids = extract_identifiers(prediction, lang)
    target_ids = extract_identifiers(target, lang)

    trunc_s = {
        "task_id": sample["task_id"],
        "pred": prediction,
        "target": target,
        "stop": stopped,
        "pred_ids": pred_ids,
        "target_ids": target_ids
    }
    return trunc_s, em_label


def compute_metric_stmt(infile: str, results_base: str, prompt_file: str, language: str,
                        truncate: TruncationList = ['expression']):
    with open(infile, "r") as f_pred:
        samples = []
        for l in f_pred.readlines():
            samples.append(json.loads(l))

    examples = {}
    with open(prompt_file, "r") as f_in:
        for l in f_in.readlines():
            ex = json.loads(l)
            examples[ex["metadata"]["task_id"]] = {
                "prompt": ex["prompt"],
                "groundtruth": ex["groundtruth"]
            }

    assert len(samples) == len(examples), f"{len(samples)} != {len(examples)}"

    truncated_samples = []
    em_labels = []

    print("post-processing samples ...")

    # Avoid races betweeen workers
    get_parser(language)
    if language == "typescript":
        get_parser("tsx")

    pool = mp.Pool(mp.cpu_count() - 1)
    worker = partial(process_examples, language, truncate)

    with tqdm(total=len(samples)) as pbar:
        for output in pool.imap_unordered(worker, zip(samples, [examples[s["task_id"]] for s in samples])):
            trunc_s, em_label = output
            em_labels.append(em_label)
            truncated_samples.append(trunc_s)
            pbar.update()

    exact_match = 0
    stop = 0
    with open(results_base + "_prediction_truncated.jsonl", 'w', encoding="utf-8") as pt, \
            open(results_base + "_exact_match_idx.jsonl", 'w') as em:
        for trunc_s, em_label in zip(truncated_samples, em_labels):
            pt.write(json.dumps(trunc_s) + "\n")
            if em_label == 1:
                em.write(f'{trunc_s["task_id"]}\n')
                exact_match += 1
            if trunc_s["stop"]:
                stop += 1

    ### Score calculation

    id_em = []
    edit_similarities = []
    detailed_results = []

    for idx, trunc_s in enumerate(truncated_samples):
        identifier_em = int(trunc_s["pred_ids"] == trunc_s["target_ids"])
        es = cal_edit_sim([trunc_s["target"]], [trunc_s["pred"]])
        id_tp, id_fp, id_fn = compute_id_match(trunc_s["pred_ids"], trunc_s["target_ids"])
        id_em.append(identifier_em)
        edit_similarities.append(es)

        detailed_results.append({
            "task_id": trunc_s["task_id"],
            "em": em_labels[idx],
            "es": es,
            "stop": trunc_s["stop"],
            "id_em": identifier_em,
            "id_precision": id_tp / (id_tp + id_fp) if (id_tp + id_fp) != 0 else 0,
            "id_recall": id_tp / (id_tp + id_fn) if (id_tp + id_fn) != 0 else 0,
            "id_f1": 2 * id_tp / (2 * id_tp + id_fp + id_fn) if (2 * id_tp + id_fp + id_fn) != 0 else 0,
        })

    em_ratio = round(exact_match / len(samples) * 100, 2)
    stop_ratio = round(stop / len(samples) * 100, 2)
    edit_sim = round(sum(edit_similarities) / len(edit_similarities), 2)

    id_em_ratio = round(
        sum(detailed_results[idx]['id_em'] for idx in range(len(detailed_results))) / len(detailed_results) * 100, 2)
    id_precision = round(sum(detailed_results[idx]['id_precision'] for idx in range(len(detailed_results))) / len(
        detailed_results) * 100, 2)
    id_recall = round(
        sum(detailed_results[idx]['id_recall'] for idx in range(len(detailed_results))) / len(detailed_results) * 100,
        2)
    id_f1 = round(
        sum(detailed_results[idx]['id_f1'] for idx in range(len(detailed_results))) / len(detailed_results) * 100, 2)

    print(
        f"Code Matching: "
        f"EM {em_ratio:.2f}, "
        f"ES {edit_sim:.2f}"
    )

    print(
        f"ID matching: "
        f"EM {id_em_ratio}, "
        #f"Precision {id_precision}, "
        #f"Recall {id_recall}, "
        f"F1 {id_f1}"
    )

    with open(os.path.join(results_base + "_detailed_results.json"), 'w') as f:
        for dr in detailed_results:
            f.write(json.dumps(dr) + "\n")

    res: Metrics = {
        "em": em_ratio,
        "es": edit_sim,
        "stop": stop_ratio,
        "id_em": id_em_ratio,
        "id_precision": id_precision,
        "id_recall": id_recall,
        "id_f1": id_f1,
        "total": len(truncated_samples)
    }

    # write the results to a file
    print(f'writing results to {results_base}_results.json")')
    with open(results_base + "_results.json", 'w') as f:
        f.write(json.dumps(res, indent=2))

    return res

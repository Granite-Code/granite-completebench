import json
from functools import cache, partial
from pathlib import Path
from venv import create

import torch.multiprocessing as mp
from tqdm import tqdm

from .eval_utils import postprocess_code_lines, extract_identifiers, cal_edit_sim, remove_comments
from .file_utils import read_jsonl, write_json, write_jsonl
from .postprocess import PostProcessor
from .types import Example, Metrics, Prediction
import os


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


def process_examples(lang: str, postprocessor: PostProcessor, args: tuple[Prediction, Example]):
    prediction, ex = args
    if lang == "typescript" and ex["metadata"]["file"].endswith(".tsx"):
        lang = "tsx"

    output = postprocessor.postprocess(ex, prediction["output"])

    stopped = prediction["stop_reason"] != "length" or len(output) < len(prediction["output"])

    output = remove_comments(output)
    target = ex["groundtruth"]
    target = remove_comments(target)

    pred_lines = [l.strip() for l in output.split("\n") if l.strip()]
    gt_lines = [l.strip() for l in target.split("\n") if l.strip()]
    em_label = int(pred_lines == gt_lines)

    pred_ids = extract_identifiers(output, lang)
    target_ids = extract_identifiers(target, lang)

    trunc_s = {
        "task_id": prediction["task_id"],
        "pred": output,
        "target": target,
        "stop": stopped,
        "pred_ids": pred_ids,
        "target_ids": target_ids,
    }
    return trunc_s, em_label


def compute_metric_stmt(
    infile: Path, results_base: Path, prompt_file: Path, language: str, postprocessor: PostProcessor
) -> Metrics:
    samples = [d for d in read_jsonl(infile)]

    examples = {}
    for ex in read_jsonl(prompt_file):
        examples[ex["metadata"]["task_id"]] = {
            "metadata": ex["metadata"],
            "prompt": ex["prompt"],
            "groundtruth": ex["groundtruth"],
            "right_context": ex["right_context"],
        }

    assert len(samples) == len(examples), f"{len(samples)} != {len(examples)}"

    truncated_samples = []
    em_labels = []

    print("post-processing samples ...")

    pool = mp.Pool(mp.cpu_count() - 1)
    worker = partial(process_examples, language, postprocessor)

    with tqdm(total=len(samples)) as pbar:
        for output in pool.imap_unordered(
            worker, zip(samples, [examples[s["task_id"]] for s in samples])
        ):
            trunc_s, em_label = output
            em_labels.append(em_label)
            truncated_samples.append(trunc_s)
            pbar.update()

    exact_match = 0
    stop = 0
    with write_jsonl(results_base / "prediction_truncated.jsonl", create_parents=True) as pt:
        for trunc_s, em_label in zip(truncated_samples, em_labels):
            pt.append(trunc_s)
            if em_label == 1:
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

        detailed_results.append(
            {
                "task_id": trunc_s["task_id"],
                "em": em_labels[idx],
                "es": es,
                "stop": trunc_s["stop"],
                "id_em": identifier_em,
                "id_precision": id_tp / (id_tp + id_fp) if (id_tp + id_fp) != 0 else 0,
                "id_recall": id_tp / (id_tp + id_fn) if (id_tp + id_fn) != 0 else 0,
                "id_f1": (
                    2 * id_tp / (2 * id_tp + id_fp + id_fn)
                    if (2 * id_tp + id_fp + id_fn) != 0
                    else 0
                ),
            }
        )

    em_ratio = round(exact_match / len(samples) * 100, 2)
    stop_ratio = round(stop / len(samples) * 100, 2)
    edit_sim = round(sum(edit_similarities) / len(edit_similarities), 2)

    id_em_ratio = round(
        sum(detailed_results[idx]["id_em"] for idx in range(len(detailed_results)))
        / len(detailed_results)
        * 100,
        2,
    )
    id_precision = round(
        sum(detailed_results[idx]["id_precision"] for idx in range(len(detailed_results)))
        / len(detailed_results)
        * 100,
        2,
    )
    id_recall = round(
        sum(detailed_results[idx]["id_recall"] for idx in range(len(detailed_results)))
        / len(detailed_results)
        * 100,
        2,
    )
    id_f1 = round(
        sum(detailed_results[idx]["id_f1"] for idx in range(len(detailed_results)))
        / len(detailed_results)
        * 100,
        2,
    )

    print(f"Code Matching: " f"EM {em_ratio:.2f}, " f"ES {edit_sim:.2f}")

    print(
        f"ID matching: "
        f"EM {id_em_ratio}, "
        # f"Precision {id_precision}, "
        # f"Recall {id_recall}, "
        f"F1 {id_f1}"
    )

    with write_jsonl(results_base / "detailed_results.jsonl", create_parents=True) as writer:
        for dr in detailed_results:
            writer.append(dr)

    res: Metrics = {
        "em": em_ratio,
        "es": edit_sim,
        "stop": stop_ratio,
        "id_em": id_em_ratio,
        "id_precision": id_precision,
        "id_recall": id_recall,
        "id_f1": id_f1,
        "total": len(truncated_samples),
    }

    # write the results to a file
    print(f'writing results to {results_base}/results.json")')
    write_json(results_base / "results.json", res, create_parents=True)
               
    return res

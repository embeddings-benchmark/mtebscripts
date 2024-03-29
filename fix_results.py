"""
Iterates over json results for custom fixes
Usage: python fix_results.py results_folder_path
"""
import glob
import json
import sys
import os

from mteb import MTEB

results_folder = sys.argv[1]
files = glob.glob(f'{results_folder.strip("/")}/*/*.json')

print("Found files: ", files)

for file_name in files:
    with open(file_name, 'r', encoding='utf-8') as f:
        results = json.load(f)
        if "dataset_version" in results:
            results.pop("dataset_version")
        if "mteb_version" not in results:
            results["mteb_version"] = "0.0.2"
        if "mteb_dataset_name" not in results:
            results["mteb_dataset_name"] = file_name.split("/")[-1].replace(".json", "")
        if "dataset_revision" not in results:
            print(file_name)
            mteb_desc = (
                MTEB(tasks=[file_name.split("/")[-1].replace(".json", "").replace("CQADupstackRetrieval", "CQADupstackAndroidRetrieval")])
                .tasks[0]
                .description
            )
            import huggingface_hub
            if "hf_hub_name" in mteb_desc:
                hf_hub_name = mteb_desc.get("hf_hub_name")
            else:
                hf_hub_name = "BeIR/" + mteb_desc.get("beir_name")
            if "cqadupstack" in hf_hub_name:
                hf_hub_name = "BeIR/cqadupstack-qrels"
            results["dataset_revision"] = huggingface_hub.hf_api.dataset_info(hf_hub_name).sha

        if "STS22" in file_name:
            for split, split_results in results.items():
                if isinstance(split_results, dict):
                    for metric, score in split_results.items():
                        if isinstance(score, dict):
                            for sub_metric, sub_score in score.items():
                                if isinstance(sub_score, dict):
                                    for sub_sub_metric, sub_sub_score in sub_score.items():
                                        results[split][metric][sub_metric][sub_sub_metric] = abs(sub_sub_score)
                                else:
                                    results[split][metric][sub_metric] = abs(sub_score)
                        else:
                            results[split][metric] = abs(score)
                results.setdefault(split, {})
        # Merge MSMARCO dev & test split runs
        elif "MSMARCO." in file_name and os.path.exists(file_name.replace("MSMARCO.", "MSMARCO-test.")):
            with open(file_name.replace("MSMARCO.", "MSMARCO-test."), 'r', encoding='utf-8') as f:
                results_test = json.load(f)
            results["test"] = results_test["test"]

        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)


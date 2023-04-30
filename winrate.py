import argparse
import json
import os
import time

import requests
import openai
import tqdm
import re

import shortuuid
import logging
import glob

from datetime import datetime

logging.basicConfig(level=logging.INFO)

logFormatter = logging.Formatter("%(asctime)s %(message)s")
logger = logging.getLogger()

def get_json_list_dir(dir_path):
    files = glob.glob(os.path.expanduser(dir_path) + "/*.jsonl")

    jsonl=[]
    for f in files:
        jsonl.extend(get_json_list(f))

    return jsonl

def get_json_list(file_path):
    file_path = os.path.expanduser(file_path)
    with open(file_path, "r") as f:
        json_list = []
        for line in f:
            json_list.append(json.loads(line, strict=False))
        return json_list

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChatGPT-based QA evaluation.")
    parser.add_argument("-m", "--model", default="vicuna-13b:20230322-new-hp-fp16")
    parser.add_argument("-r", "--review-dir", default="table/review/vicuna-13b_20230322-new-hp-fp16")
    parser.add_argument("-a", "--answer-dir", default="table/answer")
    args = parser.parse_args()

    reviews_json = get_json_list_dir(args.review_dir)
    answers_json = get_json_list_dir(args.answer_dir)
    model=args.model

    print(answers_json[0])

    total=len(reviews_json)
    wins=0
    for i in range(len(reviews_json)):
        answer1 = next(item for item in answers_json if item["answer_id"] == reviews_json[i]["answer1_id"])
        answer2 = next(item for item in answers_json if item["answer_id"] == reviews_json[i]["answer2_id"])
        assert(answer1["model_id"] == model or answer2["model_id"] == model)

        scores = reviews_json[i]["score"]
        winner = answer1["model_id"] if scores[0]>scores[1] else answer2["model_id"]
        if model == winner:
            wins=wins +1

        print("Review #{i}/{total}: {model1} ({score1}) versus {model2} ({score2}): {winner}".format(
            i=i,
            total=len(reviews_json),
            model1=answer1["model_id"],
            model2=answer2["model_id"],
            score1=reviews_json[i]["score"][0],
            score2=reviews_json[i]["score"][1],
            winner=winner
            ))

    print("Model {model}: {rate}% ({wins}/{total})".format(
        model=model,
        wins=wins,
        rate=wins/total*100,
        total=total
        ))





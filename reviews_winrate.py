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
    parser.add_argument("-m", "--model", default=None)
    parser.add_argument("-r", "--review-dir", default="table/review/vicuna-13b_20230322-clean-lang")
    parser.add_argument("-a", "--answer-dir", default="table/answer")
    args = parser.parse_args()

    assert(args.model != None and args.review_dir != None and args.answer_dir != None)

    reviews_json = get_json_list_dir(args.review_dir)
    answers_json = get_json_list_dir(args.answer_dir)
    model=args.model

    wins={"overall": 0}
    ties={"overall": 0}
    total_comparisons={"overall": 0}
    for i in range(len(reviews_json)):
        answer1 = next(item for item in answers_json if item["answer_id"] == reviews_json[i]["answer1_id"])
        answer2 = next(item for item in answers_json if item["answer_id"] == reviews_json[i]["answer2_id"])
        
        if(answer1["model_id"] != model and answer2["model_id"] != model):
            continue

        answer_model = answer1 if answer1["model_id"] == model else answer2
        answer_competitor = answer2 if answer1["model_id"] == model else answer1
        competitor=answer_competitor["model_id"]

        scores = reviews_json[i]["scores"]

        if scores[0]==scores[1]:
            winner = None 
        else:
            winner = answer1["model_id"] if scores[0]>scores[1] else answer2["model_id"]

        if not competitor in wins:
            wins[competitor]=0
        if not competitor in ties:
            ties[competitor]=0
        if not competitor in total_comparisons:
            total_comparisons[competitor]=0

        if model == winner:
            wins[competitor]=wins[competitor]+1 
            wins["overall"]=wins["overall"]+1
        elif winner == None:
            ties[competitor]=ties[competitor]+1 
            ties["overall"]=ties["overall"]+1
        total_comparisons[competitor]=total_comparisons[competitor]+1 
        total_comparisons["overall"]=total_comparisons["overall"]+1

        print("Review #{i}/{total}: {model1} ({score1}) versus {model2} ({score2}): {winner}".format(
            i=i,
            total=len(reviews_json),
            model1=answer1["model_id"],
            model2=answer2["model_id"],
            score1=reviews_json[i]["scores"][0],
            score2=reviews_json[i]["scores"][1],
            winner=winner
            ))

    for competitor in total_comparisons:
        print("Model {model} against {competitor}: {rate}% ({wins}/{total}), ties: {ties}".format(
            model=model,
            competitor=competitor,
            wins=wins[competitor],
            ties=ties[competitor] if competitor in ties else 0,
            rate=wins[competitor]/total_comparisons[competitor]*100,
            total=total_comparisons[competitor]
            ))

    # print("Model {model} OVERALL: {rate}% ({wins}/{total}), ties: {ties}".format(
    #     model=model,
    #     wins=wins["overall"],
    #     ties=ties["overall"],
    #     rate=wins["overall"]/total*100,
    #     total=total
    #     ))





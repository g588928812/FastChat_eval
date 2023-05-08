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
    parser.add_argument("-r", "--review-dir", default=None)
    parser.add_argument("-rf", "--review-file", default=None)
    parser.add_argument("-a", "--answer-dir", default="table/answer")
    args = parser.parse_args()

    assert((args.review_dir != None or args.review_file != None) and args.answer_dir != None)

    if args.review_file != None:
        reviews_json = get_json_list(args.review_file)
    else:
        reviews_json = get_json_list_dir(args.review_dir)

    answers_json = get_json_list_dir(args.answer_dir)
    model=args.model

    model_scores={}
    # wins={"overall": 0}
    # ties={"overall": 0}
    # total_comparisons={"overall": 0}
    for i in range(len(reviews_json)):
        answers=[]
        answers.append(next(item for item in answers_json if item["answer_id"] == reviews_json[i]["answer1_id"]))
        answers.append(next(item for item in answers_json if item["answer_id"] == reviews_json[i]["answer2_id"]))
        scores = reviews_json[i]["scores"]

        for f in [0,1]:
            answer=answers[f]
            if not answer["model_id"] in model_scores:
                model_scores[answer["model_id"]]={
                    "wins":0, "ties":0, "overall":0
                }        
            model_scores[answer["model_id"]]["overall"]+=1

        if scores[0] == scores[1]:
            model_scores[answers[0]["model_id"]]["ties"]+=1
            model_scores[answers[1]["model_id"]]["ties"]+=1
        else:
            if scores[0] > scores[1]:
                model_scores[answers[0]["model_id"]]["wins"]+=1
            else:
                model_scores[answers[1]["model_id"]]["wins"]+=1

        # print("Review #{i}/{total}: {model1} ({score1}) versus {model2} ({score2})".format(
        #     i=i,
        #     total=len(reviews_json),
        #     model1=answers[0]["model_id"],
        #     model2=answers[1]["model_id"],
        #     score1=scores[0],
        #     score2=scores[1]
        #     ))

    for model in model_scores:
        # print(f"Model {model}")
        print("Model {model}: {rate}% ({wins}/{total}), ties: {ties}".format(
            model=model,
            wins=model_scores[model]["wins"],
            ties=model_scores[model]["ties"],
            rate=model_scores[model]["wins"]/model_scores[model]["overall"]*100,
            total=model_scores[model]["overall"]
            ))

    # print("Model {model} OVERALL: {rate}% ({wins}/{total}), ties: {ties}".format(
    #     model=model,
    #     wins=wins["overall"],
    #     ties=ties["overall"],
    #     rate=wins["overall"]/total*100,
    #     total=total
    #     ))





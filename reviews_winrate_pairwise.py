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
    nowinner=0
    for i in range(len(reviews_json)):
        answers=[]
        answers.append(next(item for item in answers_json if item["answer_id"] == reviews_json[i]["answer1_id"]))
        answers.append(next(item for item in answers_json if item["answer_id"] == reviews_json[i]["answer2_id"]))
        scores = reviews_json[i]["scores"]
        model1=answers[0]["model_id"]
        model2=answers[1]["model_id"]
        winner=reviews_json[i]["winner"]

        if not model1 in model_scores:
            model_scores[model1]={"wins":0, "ties":0, "overall":0}        
        if not model2 in model_scores:
            model_scores[model2]={"wins":0, "ties":0, "overall":0}        

        if winner==0:
            model_scores[model1]["ties"]+=1
            model_scores[model2]["ties"]+=1
        elif winner==1:
            model_scores[model1]["wins"]+=1
        elif winner==2:
            model_scores[model2]["wins"]+=1
        elif winner==-1:
            nowinner+=1
            continue
        else:
            log.error(f"Unknown winner value: {winner}")
            continue

        model_scores[model1]["overall"]+=1
        model_scores[model2]["overall"]+=1

    print("WINRATE")
    for model in model_scores:
        # print(f"Model {model}")
        print("Model {model}\t{rate}%\t({wins}/{total})\tties:\t{ties}".format(
            model=model,
            wins=model_scores[model]["wins"],
            ties=model_scores[model]["ties"],
            rate=model_scores[model]["wins"]/model_scores[model]["overall"]*100,
            total=model_scores[model]["overall"]
            ))

    print("\nWINNING PERCENTAGE")
    for model in model_scores:
        # print(f"Model {model}")
        print("Model {model}\t{rate}".format(
            model=model,
            rate=(2*model_scores[model]["wins"]+model_scores[model]["ties"])/(2*model_scores[model]["overall"])*100,
            ))

    print(f"\nWinner could not be determined in {nowinner} cases")


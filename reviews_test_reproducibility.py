import argparse
import json
import os
import time

import shortuuid
import logging


def get_json_list(file_path):
    file_path = os.path.expanduser(file_path)
    with open(file_path, "r") as f:
        json_list = []
        for line in f:
            json_list.append(json.loads(line, strict=False))
        return json_list

questions = {}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChatGPT-based QA evaluation.")
    parser.add_argument("-r", "--review-file", default=None)
    args = parser.parse_args()

    assert(args.review_file)

    review_jsonl=get_json_list(args.review_file)

    for review in review_jsonl:
        qid=review["question_id"]
        scores=review["scores"]

        if not qid in questions:
            questions[qid]=[]

        questions[qid].append(scores)

    for qid in questions:
        for scores in questions[qid]:
            print(f"{qid}\t{scores[0]}\t{scores[1]}")

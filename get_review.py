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

from datetime import datetime

logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

logFormatter = logging.Formatter("%(asctime)s %(message)s")
logger = logging.getLogger()


logger_logfn = "log_"+datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
fileHandler = logging.FileHandler("{0}/{1}.log".format("./logs/", logger_logfn))
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

MAX_API_RETRY = 5
REQ_TIME_GAP = 10

oaikey = None

def get_eval_OAI(reviewer, prompt: str, max_tokens: int):
    logging.basicConfig(level=logging.INFO)

    assert(oaikey is not None)

    for i in range(MAX_API_RETRY):
        try:
            openai.api_key = oaikey

            completion = openai.ChatCompletion.create(
              model=reviewer["params"]["model"],
              temperature=reviewer["metadata"]["temperature"],
              messages=[
                {"role": "user", 
                "content": prompt}
              ],
              max_tokens=max_tokens,
            )

            content = completion.choices[0].message.content

            # logger.info(content)
            return content
        except Exception as e:
            logger.error(e)
            time.sleep(5)
    logger.error(f"Failed after {MAX_API_RETRY} retries.")
    return "error"

def get_eval_OOB(reviewer, prompt: str, max_tokens: int):
    logging.basicConfig(level=logging.INFO)
    for i in range(MAX_API_RETRY):
        # try:
        params=reviewer["metadata"]

        payload = json.dumps([prompt, params])

        server=reviewer["params"]["oobabooga-server"]
        response = requests.post(f"http://{server}/run/textgen", json={
            "data": [
                payload
            ]
        }).json()

        raw_reply = response["data"][0]
        content = raw_reply[len(prompt):]

        logger.info(content)
        return content
        # except Exception as e:
        #     logger.error(e)
        #     time.sleep(5)
    logger.error(f"Failed after {MAX_API_RETRY} retries.")
    return "error"

def parse_score(review, reviewer):
    try:
        regex = reviewer["score-regex"]

        matches = re.search(regex, review)

        mg = matches.groups()

        return [float(mg[0]), float(mg[1])]
    except Exception as e:
        logger.error(
            f"{e}\nContent: {review}\n" "You must manually fix the score pair."
        )
        return [-1, -1]

def gen_prompt(reviewer, ques, cat, ans1, ans2):
    prompt_template = reviewer["prompt_templates"][cat] if cat in reviewer["prompt_templates"] else reviewer["prompt_templates"]["default"]

    prompt = prompt_template.format(
        question=ques, answer_1=ans1, answer_2=ans2
    )

    return prompt

def get_json_list(file_path):
    file_path = os.path.expanduser(file_path)
    with open(file_path, "r") as f:
        json_list = []
        for line in f:
            json_list.append(json.loads(line, strict=False))
        return json_list

def import_json(file_path):
    file_path = os.path.expanduser(file_path)
    f = open(file_path)
    data = json.load(f)
    f.close()

    return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChatGPT-based QA evaluation.")
    parser.add_argument("-q", "--question-file", default="table/question.json")
    parser.add_argument("-a", "--answer-file-list", nargs="+", default=[])
    parser.add_argument("-p", "--prompt-file")
    parser.add_argument("-rf", "--reviewer-file", default="table/reviewer.json")
    parser.add_argument("-r", "--reviewer", default="gpt-3.5-turbo")
    parser.add_argument("-o", "--output-review-file")
    parser.add_argument("-k", "--openaikey", type=str)
    parser.add_argument("-dr", "--do-repetitions", type=int, default=1)
    parser.add_argument("-lc", "--limit-category", type=str, default=None)
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="maximum number of tokens produced in the output",
    )
    args = parser.parse_args()

    oaikey = args.openaikey
    question_jsons = import_json(args.question_file)
    reviewer_jsons = import_json(args.reviewer_file)
    answer1_jsons = get_json_list(args.answer_file_list[0])
    answer2_jsons = get_json_list(args.answer_file_list[1])

    reviewers = list(filter(lambda reviewer_jsons: reviewer_jsons['reviewer_id'] == args.reviewer, reviewer_jsons))

    if(len(reviewers)==0):
        logger.error(f"reviewer {args.reviewer} not found in {args.reviewer_file}")
        quit()
    else:
        reviewer=reviewers[0]

    # check if # of questions, answers are the same
    # assert len(question_jsons) == len(answer1_jsons) == len(answer2_jsons)

    review_jsons = []
    total_len = len(question_jsons)
    question_idx_list = list(range(total_len))

    for rep in range(args.do_repetitions):
        logger.info(f"Doing repetition {rep+1} of {args.do_repetitions}")

        # for i in question_idx_list:
        for i in range(10):
            assert (
                answer1_jsons[i]["question_id"]
                == question_jsons[i]["question_id"]
                == answer2_jsons[i]["question_id"]
            )

            ques = question_jsons[i]["text"]
            cat = question_jsons[i]["category"]
            ans1 = answer1_jsons[i]["text"]
            ans2 = answer2_jsons[i]["text"]
            model1 = answer1_jsons[i]["model_id"]
            model2 = answer2_jsons[i]["model_id"]

            if args.limit_category is not None:
                logger.info(f"Limiting to category '{args.limit_category}'")
                if cat != args.limit_category:
                    continue

            prompt = gen_prompt(reviewer, ques, cat, ans1, ans2)

            if reviewer["type"] == "OpenAI":
                review = get_eval_OAI( reviewer, prompt, args.max_tokens)
            elif reviewer["type"] == "oobabooga-api" :
                review = get_eval_OOB( reviewer, prompt, args.max_tokens)
            else:            
                logger.error("unknown reviewer type " + reviewer["type"])
                quit()

            review_id = shortuuid.uuid()
            review_jsons.append(
                {
                    "review_id": review_id,
                    "question_id": question_jsons[i]["question_id"],
                    "answer1_id": answer1_jsons[i]["answer_id"],
                    "answer2_id": answer2_jsons[i]["answer_id"],
                    "reviewer_id": reviewer["reviewer_id"],
                    "metadata": reviewer["metadata"],
                    "text": review,
                    "scores": parse_score(review, reviewer)
                }
            )

            # print("#### PROMPT " + prompt )
            # print("#### REVIEW " + review )

            logger.info("Review for question {qid}, {m1} vs. {m2}, reviewer {reviewer}. Scores: A1: {s1}, A2 {s2}. Review: {review}".format(
                qid=question_jsons[i]["question_id"],
                reviewer=reviewer["reviewer_id"],
                review="",
                s1=review_jsons[len(review_jsons)-1]["scores"][0],
                s2=review_jsons[len(review_jsons)-1]["scores"][1],
                m1=answer1_jsons[i]["model_id"],
                m2=answer2_jsons[i]["model_id"]
                ))

            # To avoid the rate limit set by OpenAI
            logger.info(f"Waiting for {REQ_TIME_GAP} seconds before sending the next request.")
            # time.sleep(10)

        outfn=args.output_review_file if rep==0 else args.output_review_file + "_" + str(rep)
        outfn=outfn + ".jsonl"

        logger.info(f"writing output of {model1} vs {model2} to file {outfn}")
        with open(f"{outfn}", "w+") as output_review_file:
            for review in review_jsons:
                output_review_file.write(json.dumps(review) + "\n")

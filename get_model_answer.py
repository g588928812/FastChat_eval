import argparse
import os
import json
import shortuuid
import logging
import requests
from tqdm import tqdm

from datetime import datetime

logging.basicConfig(level=logging.INFO)

logFormatter = logging.Formatter("%(asctime)s %(message)s")
logger = logging.getLogger()

logger_logfn = "log_getModelAnswer_"+datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
fileHandler = logging.FileHandler("{0}/{1}.log".format("./logs/", logger_logfn))
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

oaikey = None

def import_json(file_path):
    file_path = os.path.expanduser(file_path)
    f = open(file_path)
    data = json.load(f)
    f.close()

    return data

def run_eval(model_id, model_file, question_file, answer_file):
    models_jsons = import_json(model_file)

    models = list(filter(lambda models_jsons: models_jsons['model_id'] == model_id, models_jsons))

    if(len(models)==0):
        logger.error(f"model {model_id} not found in {model_file}")
        quit()
    else:
        model=models[0]

    logger.info(f"Model: {model_id}")

    ques_jsons = import_json(question_file)
    ans_jsons = []

    for i in range(len(ques_jsons)):
        logger.info(f"Question {i+1}/{len(ques_jsons)}")
        answer=get_model_answer(model, ques_jsons[i])
        ans_jsons.append(answer)

    logger.info(f"Writing answers to file {os.path.expanduser(answer_file)}")

    with open(os.path.expanduser(answer_file), "w") as ans_file:
        for line in ans_jsons:
            ans_file.write(json.dumps(line) + "\n")

def askOpenAI(model, question):
    assert(oaikey is not None)

    logger.error("askOpenAI not implemented yet")

    return "error"

def askObabooga(model, question):
    try:
        params=model["metadata"]
        server=model["params"]["oobabooga-server"]
        question=question["text"]
        prompt=model["params"]["prompt_template"].format(
            question=question
            )
        logger.info("Asking {mid} on {server}: {prompt}".format(
            mid=model["model_id"],
            server=server,
            prompt=prompt))

        payload = json.dumps([prompt, params])

        response = requests.post(f"http://{server}/run/textgen", json={
            "data": [
                payload
            ]
        }).json()

        raw_reply = response["data"][0]
        content = raw_reply[len(prompt):]
        
        return content

    except Exception as e:
        logger.error(e)
        return "error"

def get_model_answer(model, question):
    if model["type"] == "OpenAI":
        answer=askOpenAI(model, question)
    elif model["type"] == "oobabooga-api":
        answer=askObabooga(model, question)
    else:
        logger.error(f"unknown model type {mt}".format(mt=model["type"]))
        quit()

    # logger.info(answer)

    answer_json= {
        "question_id": question["question_id"],
        "text": answer,
        "answer_id": shortuuid.uuid(),
        "model_id": model["model_id"],
        "metadata": model["metadata"],
    }

    return answer_json

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", type=str, required=True)
    parser.add_argument("--model-file", type=str, default="table/model.json")
    parser.add_argument("--answer-file", type=str, default=None)
    parser.add_argument("--question-file", type=str, default="table/question.json")
    parser.add_argument("-k", "--openaikey", type=str)
    args = parser.parse_args()

    oaikey = args.openaikey

    if args.answer_file is None:
        answer_file = "table/answer/answer_" + args.model_id.replace(":","_") + ".jsonl"
    else:
        answer_file=args.answer_file

    run_eval(
        args.model_id,
        args.model_file,
        args.question_file,
        answer_file
    )

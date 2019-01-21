import io
import os
import json
import re
import pprint

from google.cloud import vision
from google.cloud.vision import types
from googleapiclient.discovery import build

def get_cse_info(info_type):
    with io.open(os.path.join(
        os.path.dirname(__file__),
        'cse_info.json'), 'r') as to_parse:
        content = to_parse.read()

    return json.loads(content)[info_type]

def get_question(text_annotations):
    question = []
    for text in text_annotations:
        question.append(text.description)
        if text.description.endswith('?'):
            del question[0]
            return ' '.join(question)

def get_answers(text_annotations):
    answers = []
    record = False
    texts = re.split(r'\n', text_annotations[0].description)
    del texts[-1]
    for text in texts:
        if record == True:
            answers.append(text)
        elif text.endswith('?'):
            record = True
    return answers

def get_text(image_path):
    client = vision.ImageAnnotatorClient()

    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    response = client.text_detection(image=image)
    return response.text_annotations

def search(service, question, answers):
    input = '"' + question + '"' + ' (' + ' OR '.join(answers) + ')'
    cse_id = get_cse_info("cse_id")
    response = service.cse().list(
        q=input,
        cx=cse_id,
        num=10
    ).execute()
    return response


def find_answers():
    text_annotations = get_text(os.path.join(
        os.path.dirname(__file__),
        'screenshot/question.png'))
    question = get_question(text_annotations)
    answers = get_answers(text_annotations)
    cse_developerkey = get_cse_info("cse_developerkey")
    service=build("customsearch", "v1", developerKey=cse_developerkey)
    results = search(service, question, answers)

    pprint.pprint(results)

    items = json.dumps(results['items']).lower()
    answer1_count = items.count(answers[0].lower())
    answer2_count = items.count(answers[1].lower())
    answer3_count = items.count(answers[2].lower())

    if answer1_count > answer2_count and answer1_count > answer3_count:
        print("Choose: %s" % answers[0] )
    elif answer2_count > answer1_count and answer2_count > answer3_count:
        print("Choose: %s" % answers[1] )
    elif answer3_count > answer1_count and answer3_count > answer2_count:
        print("Choose: %s" % answers[2] )
    else:
        print("Something happened")

find_answers()

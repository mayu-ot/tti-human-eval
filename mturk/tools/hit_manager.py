import boto3
import pandas as pd
import os
import shutil
import click
import time
from tqdm import tqdm
from datetime import datetime
from yaml import load, dump
from yaml import Loader
from parse import findall, search

QUESTION_XML = """<?xml version="1.0"?>
<HTMLQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2011-11-11/HTMLQuestion.xsd">
<HTMLContent><![CDATA[{html}]]>
</HTMLContent>
<FrameHeight>0</FrameHeight>
</HTMLQuestion>
"""


@click.group()
def cli():
    pass


def load_cfg(cfg_file):
    with open(cfg_file, "r") as f:
        cfg = load(f.read(), Loader=Loader)

    return cfg


def get_client(is_live=False):
    if is_live:
        endpoint_url = "https://mturk-requester.us-east-1.amazonaws.com"
        print("Preparing LIVE client")
    else:
        endpoint_url = (
            "https://mturk-requester-sandbox.us-east-1.amazonaws.com"
        )
        print("Preparing SANDBOX client")

    region_name = "us-east-1"
    aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
    aws_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]

    client = boto3.client(
        "mturk",
        endpoint_url=endpoint_url,
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
    return client


def create_hit_type(client, hit_cfgfile, qual_cfgfile):
    hit_cfg = load_cfg(hit_cfgfile)
    qual_cfgs = [load_cfg(x) for x in qual_cfgfile]
    hit_cfg["QualificationRequirements"] = qual_cfgs
    response = client.create_hit_type(**hit_cfg)
    print(f"HITTypeId: {response['HITTypeId']}")
    return response["HITTypeId"]


@cli.command()
@click.argument("question_file", type=click.File("r"), nargs=1)
@click.argument("answer_file", type=click.File("r"), nargs=1)
@click.argument(
    "cfg_file", type=click.Path(file_okay=True, dir_okay=False), nargs=1
)
@click.option("--live", is_flag=True)
def create_qualification(question_file, answer_file, cfg_file, live):
    client = get_client(is_live=live)
    qual_test_cfg = load_cfg(cfg_file)
    question = question_file.read()
    answer = answer_file.read()
    res = client.create_qualification_type(
        Test=question, AnswerKey=answer, **qual_test_cfg
    )
    print(
        f"QualificationTypeId: {res['QualificationType']['QualificationTypeId']}"
    )
    qual_cfg = {
        "QualificationTypeId": res["QualificationType"]["QualificationTypeId"],
        "Comparator": "EqualTo",
        "IntegerValues": [100],
    }
    endpoint = "live" if live else "sandbox"
    with open(
        f"mturk/configs/custom_qual/{endpoint}-qualification_test.yaml", "w"
    ) as f:
        dump(qual_cfg, f)

    return res["QualificationType"]["QualificationTypeId"]


@cli.command()
@click.argument("worker_id", type=str)
@click.option("-m", "--comment", type=str)
@click.option("--live", is_flag=True)
def block_worker(worker_id, comment, live):
    client = get_client(is_live=live)
    client.create_worker_block(WorkerId=worker_id, Reason=comment)
    with open("data/mturk/block_list.txt", "a") as f:
        f.write(f'{worker_id},"{comment}"\n')


@cli.command()
@click.argument("message_file", type=click.File("r"))
@click.argument("worker_id", type=str)
def send_alert(message_file, worker_id):
    """Send a message to a worker.

    Args:
        message_file (file name): First line is used as a subject of the message.
                                  The main text has to start at the second line.
        worker_id (str): ID of a worker who should get the message.
    """
    client = get_client(is_live=True)
    subject = message_file.readline().strip()
    message = message_file.read()

    client.notify_workers(
        Subject=subject, MessageText=message, WorkerIds=[worker_id]
    )


def parse_assignments(assignment):
    out_assignment = dict()
    for k, v in assignment.items():
        if k.endswith("Time"):
            out_assignment[k] = assignment[k].strftime(
                "%a %b %d %H:%M:%S PDT %Y"
            )
        elif k == "Answer":
            ans = pd.read_xml(v, parser="etree")
            for i, j in ans.values:
                out_assignment["Answer." + i] = j
        else:
            out_assignment[k] = v
    return out_assignment


@cli.command()
@click.argument(
    "hit_file", type=click.Path(file_okay=True, dir_okay=False), nargs=1
)
@click.option("-s", "--save", is_flag=True)
@click.option("--max-assignment", type=int, default=3)
def get_status(hit_file, save, max_assignment):
    """Count completed HITs and download annotations.

    Args:
        hit_file (str): hits.csv file generated by publish cmd.
        save (flag): Download annotations.
        max_assignment (int): # assignments per HIT
    """
    log_dir = os.path.dirname(hit_file)

    check_existing_log = False
    if os.path.exists(os.path.join(log_dir, "results.csv")):
        log = pd.read_csv(os.path.join(log_dir, "results.csv"))
        check_existing_log = True

    client = get_client(is_live=True)

    if save:
        data = []

    total = 0
    n_assign = 0
    df = pd.read_csv(hit_file)

    for _, row in tqdm(df.iterrows()):
        hit_id = row.HITId
        model_name = row.model_name
        file_name = row.file_name
        caption = row.caption

        if check_existing_log:
            if (log["HITId"] == hit_id).sum() == max_assignment:
                total += max_assignment
                n_assign += max_assignment
                continue

        hit_info = client.get_hit(HITId=hit_id)["HIT"]
        total += hit_info["MaxAssignments"]

        res = client.list_assignments_for_hit(HITId=hit_id)
        res_assign = res["Assignments"]
        while len(res_assign):
            n_assign += len(res_assign)

            if save:
                for x in res_assign:
                    assign = parse_assignments(x)
                    assign.update(
                        {
                            "Input.model_name": model_name,
                            "Input.file_name": file_name,
                            "Input.caption": caption,
                        }
                    )
                    data.append(assign)

            res = client.list_assignments_for_hit(
                HITId=hit_id, NextToken=res["NextToken"]
            )
            res_assign = res["Assignments"]
    print(f"{n_assign}/{total}")

    if save:
        res_df = pd.DataFrame.from_records(data)
        if check_existing_log:
            res_df = pd.concat([log, res_df])
        res_df.to_csv(os.path.join(log_dir, "results.csv"), index=False)


@cli.command()
@click.argument(
    "hit_file", type=click.Path(file_okay=True, dir_okay=False), nargs=1
)
@click.option("--live", is_flag=True)
def delete(hit_file, live):
    client = get_client(is_live=live)
    df = pd.read_csv(hit_file)

    for hit_id in tqdm(df["HITId"].values):
        client.update_expiration_for_hit(
            HITId=hit_id, ExpireAt=datetime(2015, 1, 1)
        )


@cli.command()
@click.argument("question-file", type=click.File("r"), nargs=1)
@click.argument(
    "input-file", type=click.Path(file_okay=True, dir_okay=False), nargs=1
)
@click.argument(
    "hit-cfgfile", type=click.Path(file_okay=True, dir_okay=False), nargs=1
)
@click.argument(
    "qual-cfgfile", type=click.Path(file_okay=True, dir_okay=False), nargs=-1
)
@click.option("--max-assignment", type=int, default=3)
@click.option("--live", is_flag=True)
def publish(
    question_file, input_file, hit_cfgfile, qual_cfgfile, max_assignment, live
):
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    log_dir = f"data/mturk/logs/{timestamp}"
    if not live:
        log_dir += "_sandbox"
    os.mkdir(log_dir)

    # save config files
    shutil.copyfile(
        hit_cfgfile, os.path.join(log_dir, os.path.basename(hit_cfgfile))
    )
    for file_name in qual_cfgfile:
        shutil.copyfile(
            file_name, os.path.join(log_dir, os.path.basename(file_name))
        )

    client = get_client(is_live=live)
    print(client.get_account_balance()["AvailableBalance"])

    hit_type_id = create_hit_type(client, hit_cfgfile, qual_cfgfile)

    question_template = QUESTION_XML.format(html=question_file.read())
    # save question file
    with open(os.path.join(log_dir, "question.xml"), "w") as f:
        f.write(question_template)

    data = pd.read_csv(input_file)

    with open(os.path.join(log_dir, "hits.csv"), "w") as f:
        f.write("HITId,model_name,file_name,caption\n")
        for row in tqdm(data.iterrows()):
            model_name = row[1]["model_name"]
            file_name = row[1]["file_name"]
            caption = row[1]["caption"]

            question = (
                question_template.replace("${model_name}", model_name)
                .replace("${file_name}", file_name)
                .replace("${caption}", caption)
            )

            res = client.create_hit_with_hit_type(
                HITTypeId=hit_type_id,
                MaxAssignments=max_assignment,
                LifetimeInSeconds=172800,
                Question=question,
            )
            f.write(
                f"""{res['HIT']['HITId']},{model_name},{file_name},"{caption}"\n"""
            )


if __name__ == "__main__":
    cli()

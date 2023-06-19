import pandas as pd
import numpy as np
import datetime as dt
import krippendorff
import matplotlib.pyplot as plt
import click


@click.group()
def cli():
    pass


def worker_stats(data, ax):
    _ = ax.pie(data["worker"].value_counts().values)
    ax.text(
        -1,
        -1.3,
        f"""#unique worker: {len(data["worker"].unique())}\n{len(data)/len(data["worker"].unique()):.1f} annos/worker""",
    )

    alpha_text = []
    for i, q in enumerate(["faithfull", "quality"]):
        annotation_table = data.pivot_table(
            index="worker", columns="hit", values=f"ans_{q}"
        ).values
        alpha = krippendorff.alpha(
            annotation_table, level_of_measurement="ordinal"
        )
        print(f"{q}-alpha: {alpha:.2f}")
        alpha_text.append(f"{q}-alpha: {alpha:.2f}")
    ax.set_title("\n".join(alpha_text))


def worktime_stats(data, ax, verbose=False):
    work_time_list = []
    for worker_id in data["worker"].unique():
        submit_time = data[data["worker"] == worker_id]["submit_time"].values
        submit_time = [
            dt.datetime.strptime(x, "%a %b %d %H:%M:%S PDT %Y")
            for x in submit_time
        ]
        submit_time.sort()
        approx_work_time = map(
            lambda x1, x2: (x2 - x1).total_seconds(),
            submit_time[:-1],
            submit_time[1:],
        )
        approx_work_time = list(approx_work_time)
        work_time_list += approx_work_time
        n = len(submit_time)
        if verbose:
            print(
                f"{worker_id:16} #sample:{n:>3}, med.:{np.median(approx_work_time):>5.1f} sec"
            )
    _ = ax.hist(np.clip(work_time_list, 0, 300), bins=20)

    submit_time = [
        dt.datetime.strptime(x, "%a %b %d %H:%M:%S PDT %Y")
        for x in data["submit_time"].values
    ]
    submit_time.sort()
    total_time = submit_time[-1] - submit_time[0]
    total_time = total_time.total_seconds()
    _ = ax.set_title(
        f"Approx. work time in sec. (med. {np.median(work_time_list):.1f})\n total time: {total_time:.1f}"
    )


def label_stats(data, axes):
    for i, q in enumerate(["faithfull", "quality"]):
        scores = data[["hit", f"ans_{q}"]].groupby("hit").mean()
        axes[i].hist(scores.values)
        axes[i].set_title(f"{q}: avr. {np.nanmean(scores.values):.2f}")
        print(f"{q}: avr. {np.nanmean(scores.values):.2f}")


def generate_report(data, saveto):
    _ = plt.figure(figsize=(10, 8))
    ax0 = plt.subplot(221)
    ax1 = plt.subplot(222)
    axes = plt.subplot(223), plt.subplot(224)
    worker_stats(data, ax0)
    worktime_stats(data, ax1)
    label_stats(data, axes)
    plt.savefig(saveto)


def load_data(data_file):
    df = pd.read_csv(data_file)
    data = {
        "hit": [],
        "worker": [],
        "ans_faithfull": [],
        "lack_confidence_q1": [],
        "ans_quality": [],
        "model_name": [],
        "submit_time": [],
    }

    for _, row in df.iterrows():
        data["hit"].append(row["HITId"])
        data["worker"].append(row["WorkerId"])
        if row["Answer.lack-confidence.on"]:
            data["ans_faithfull"].append(np.nan)
        else:
            data["ans_faithfull"] += [
                i + 1 for i in range(5) if row[f"Answer.faithfull.{i+1}"]
            ]
        data["lack_confidence_q1"].append(row["Answer.lack-confidence.on"])
        data["ans_quality"] += [
            i + 1 for i in range(5) if row[f"Answer.quality.{i+1}"]
        ]
        data["model_name"].append(row["Input.model_name"])
        data["submit_time"].append(row["SubmitTime"])

    data = pd.DataFrame(data)
    return data


@cli.command()
@click.argument("res-file", type=click.Path(file_okay=True, dir_okay=False))
def overview(res_file):
    data = load_data(res_file)
    generate_report(data, res_file + ".png")


if __name__ == "__main__":
    cli()

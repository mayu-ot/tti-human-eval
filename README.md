# Human Evaluation of Text2Images on AMT
Toward Verifiable and Reproducible Human Evaluation for Text-to-Image Generation

[project page](https://mayu-ot.github.io/tti-human-eval/)

## Installation
```shell
poetry install
```

# Setting Up Your Amazon Mechanical Turk (AMT) Account
```shell
export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXX
export AWS_ACCESS_KEY_ID=XXXXXXXXXXXX
```

## Preparing Input Data for GitHub Project
This guide will help you prepare the input data for AMT HITs.

### Input Data Format
The input data should be in the form of a CSV file.
Here's a sample structure of the CSV file:
| model_name      | file_name        | caption                                      |
|-----------------|------------------|----------------------------------------------|
| stable_diffusion| 000000000139.png | A room with chairs, a table, and a woman in it. |

#### CSV Columns
- **model_name**: The name of the text2image model being used.
- **file_name**: The name of the image file.
- **caption**: Input caption being used to generate the image.

Please make sure that the image file specified in the `file_name` column is accessible on the internet.

## Publishing HITs
The main command template for publishing HITs is as follows:
```shell
poetry run python mturk/tools/hit_manager.py publish $LAYOUT_HTML $DATA_CSV $HIT_CFG_YML $QUAL_CFG_YML_1 ... --live
```

- $LAYOUT_HTML: The path to the HTML file containing the layout of the HIT.
- $DATA_CSV: The path to the CSV file containing the data to be used in the HIT.
- $QUAL_CFG_YML_1, $HIT_CFG_YML_2, ...: One or more paths to YAML configuration files containing the qualification settings.
- --max-assignment: (Optional, default 3) Specify the number of annotators to be assigned for each sample.
- --live: (Optional) Include this flag to publish the HITs to the live MTurk environment. If not specified, the HITs will be published to the MTurk sandbox environment for testing purposes.

For example,
```shell
poetry run python mturk/tools/hit_manager.py publish mturk/layouts/HIT_layout.html data/mturk/input/hit_data.csv mturk/configs/hit_cfg.yaml mturk/configs/sys_qual/adult_content.yaml mturk/configs/sys_qual/master_worker.yaml --live
```

The `hits.csv` file is required to access the annotation results and will be saved in the `data/mturk/logs/` directory.

## Downloading Annotation Results
To download the annotation results, use the following command:
```shell
poetry run python mturk/tools/hit_manager.py get-status data/mturk/logs/%Y%m%d_%H%M%S/hits.csv --max-assignment 3
```

The submitted annotations will be saved in a `results.csv` file located in the same directory as the `hits.csv` file.

# Generate a Summary Report of the Results

Use the command below to generate a PNG image displaying key statistics, such as Krippendorff's alpha, task completion time, and label distributions.

```shell
poetry run python mturk/tools/reporter.py overview $RESULT_CSV
```

# Human Annotation Dataset
The human annotations for the experiments presented in our paper can be found here ([annotations](https://storage.googleapis.com/ailab-public/tti-human-eval/human_annos.zip), [images]()).



## Citation
```bibtex
@inproceedings{text2img_eval_2023,
title={Toward Verifiable and Reproducible Human Evaluation for Text-to-Image Generation},
author={Otani, Mayu and Togashi, Riku and Sawai, Yu and Ishigami, Ryosuke and Nakashima, Yuta and Rahtu, Esa and Heikkilä, Janne and Satoh, Shin’ichi},
booktitle={The IEEE/CVF Conference on Computer Vision and Pattern Recognition},
year={2023}
}
```

## License
Licensed under GPL-3.0 license.

## TODOs
- [ ] Publish notebooks
- [ ] Solve license issue
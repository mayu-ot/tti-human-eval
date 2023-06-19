# Human Evaluation of Text2Images on AMT
Toward Verifiable and Reproducible Human Evaluation for Text-to-Image Generation

[project page](https://mayu-ot.github.io/tti-human-eval/)

## Installation
```shell
poetry install
```

## Setting up AMT account
```shell
export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXX
export AWS_ACCESS_KEY_ID=XXXXXXXXXXXX
```

## Publishing HITs
```shell
poetry run python mturk/tools/hit_manager.py publish $LAYOUT_HTML $DATA_CSV $HIT_CFG_YML_1 $HIT_CFG_YML_2 ... --live
```

## Publish qualification test
```shell
poetry run python mturk/tools/hit_manager.py create-qualification $QUAL_TEST_QUESTION_XML $QUAL_TEST_ANSWER_XML $QUAL_TEST_CFG_YML
```

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
- [ ] Publish collected human annotations and generated images
- [ ] Solve license issue

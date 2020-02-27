# coding=utf-8
# Copyright 2020 The TensorFlow Datasets Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The Multi-Genre NLI Corpus."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

import tensorflow.compat.v2 as tf
import tensorflow_datasets.public_api as tfds

_CITATION = """\
@InProceedings{N18-1101,
  author = "Williams, Adina
            and Nangia, Nikita
            and Bowman, Samuel",
  title = "A Broad-Coverage Challenge Corpus for
           Sentence Understanding through Inference",
  booktitle = "Proceedings of the 2018 Conference of
               the North American Chapter of the
               Association for Computational Linguistics:
               Human Language Technologies, Volume 1 (Long
               Papers)",
  year = "2018",
  publisher = "Association for Computational Linguistics",
  pages = "1112--1122",
  location = "New Orleans, Louisiana",
  url = "http://aclweb.org/anthology/N18-1101"
}
"""

_DESCRIPTION = """\
The Multi-Genre Natural Language Inference (MultiNLI) corpus is a
crowd-sourced collection of 433k sentence pairs annotated with textual
entailment information. The corpus is modeled on the SNLI corpus, but differs in
that covers a range of genres of spoken and written text, and supports a
distinctive cross-genre generalization evaluation. The corpus served as the
basis for the shared task of the RepEval 2017 Workshop at EMNLP in Copenhagen.
"""


class MultiNLIConfig(tfds.core.BuilderConfig):
  """BuilderConfig for MultiNLI."""

  @tfds.core.disallow_positional_args
  def __init__(self, text_encoder_config=None, **kwargs):
    """BuilderConfig for MultiNLI.

    Args:
      text_encoder_config: `tfds.features.text.TextEncoderConfig`, configuration
        for the `tfds.features.text.TextEncoder` used for the features feature.
      **kwargs: keyword arguments forwarded to super.
    """
    super(MultiNLIConfig, self).__init__(
        version=tfds.core.Version(
            "1.0.0", "New split API (https://tensorflow.org/datasets/splits)"),
        supported_versions=[
            tfds.core.Version(
                "0.0.2", experiments={tfds.core.Experiment.S3: False}),
        ],
        **kwargs)
    self.text_encoder_config = (
        text_encoder_config or tfds.features.text.TextEncoderConfig())


class MultiNLI(tfds.core.GeneratorBasedBuilder):
  """MultiNLI: The Stanford Question Answering Dataset. Version 1.1."""

  BUILDER_CONFIGS = [
      MultiNLIConfig(
          name="plain_text",
          description="Plain text",
      ),
  ]

  def _info(self):
    return tfds.core.DatasetInfo(
        builder=self,
        description=_DESCRIPTION,
        features=tfds.features.FeaturesDict({
            "premise":
                tfds.features.Text(
                    encoder_config=self.builder_config.text_encoder_config),
            "hypothesis":
                tfds.features.Text(
                    encoder_config=self.builder_config.text_encoder_config),
            "label":
                tfds.features.ClassLabel(
                    names=["entailment", "neutral", "contradiction"]),
        }),
        # No default supervised_keys (as we have to pass both premise
        # and hypothesis as input).
        supervised_keys=None,
        homepage="https://www.nyu.edu/projects/bowman/multinli/",
        citation=_CITATION,
    )

  def _vocab_text_gen(self, filepath):
    for _, ex in self._generate_examples(filepath):
      yield " ".join([ex["premise"], ex["hypothesis"]])

  def _split_generators(self, dl_manager):

    downloaded_dir = dl_manager.download_and_extract(
        "http://storage.googleapis.com/tfds-data/downloads/multi_nli/"
        "multinli_1.0.zip")
    mnli_path = os.path.join(downloaded_dir, "multinli_1.0")
    train_path = os.path.join(mnli_path, "multinli_1.0_train.txt")
    matched_validation_path = os.path.join(mnli_path,
                                           "multinli_1.0_dev_matched.txt")
    mismatched_validation_path = os.path.join(
        mnli_path, "multinli_1.0_dev_mismatched.txt")
    # Generate shared vocabulary
    # maybe_build_from_corpus uses SubwordTextEncoder if that's configured
    self.info.features["premise"].maybe_build_from_corpus(
        self._vocab_text_gen(train_path))
    encoder = self.info.features["premise"].encoder
    # Use maybe_set_encoder because the encoder may have been restored from
    # package data.
    self.info.features["premise"].maybe_set_encoder(encoder)
    self.info.features["hypothesis"].maybe_set_encoder(encoder)

    return [
        tfds.core.SplitGenerator(
            name=tfds.Split.TRAIN,
            gen_kwargs={"filepath": train_path}),
        tfds.core.SplitGenerator(
            name="validation_matched",
            gen_kwargs={"filepath": matched_validation_path}),
        tfds.core.SplitGenerator(
            name="validation_mismatched",
            gen_kwargs={"filepath": mismatched_validation_path}),
    ]

  def _generate_examples(self, filepath):
    """Generate mnli examples.

    Args:
      filepath: a string

    Yields:
      dictionaries containing "premise", "hypothesis" and "label" strings
    """
    for idx, line in enumerate(tf.io.gfile.GFile(filepath, "rb")):
      if idx == 0:
        continue  # skip header
      line = tf.compat.as_text(line.strip())
      split_line = line.split("\t")
      # Examples not marked with a three out of five consensus are marked with
      # "-" and should not be used in standard evaluations.
      if split_line[0] == "-":
        continue
      # Works for both splits even though dev has some extra human labels.
      yield idx, {
          "premise": split_line[5],
          "hypothesis": split_line[6],
          "label": split_line[0]
      }

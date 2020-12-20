import os
import pickle

import constants as con

# from models.use_multilingual_models import use_multilingual_v3_model
from models.sententense_transformers_models import sentence_transformers_model, sentence_transformers_model_xlm_100, sentence_transformers_model_labse

models = {
    "sentence_transformer_multilingual": sentence_transformers_model,
    "sentence_transformer_multilingual_xlm_100": sentence_transformers_model_xlm_100,
    "sentence_transformer_multilingual_labse": sentence_transformers_model_labse,
    # "use_multilingual_v3": use_multilingual_v3_model
}

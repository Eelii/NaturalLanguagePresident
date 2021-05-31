from aitextgen.TokenDataset import TokenDataset
from aitextgen.tokenizers import train_tokenizer
from aitextgen.utils import GPT2ConfigCPU
from aitextgen import aitextgen

def init_ai():
     ai = aitextgen(model_folder="trained_model",tokenizer_file="aitextgen.tokenizer.json")
     return ai

def generateTweet(ai, prompt=None, temperature=0.5):

    if not prompt:
        tweet = ai.generate_one(temperature=temperature)
        print(tweet)
        return tweet

    elif prompt:
        tweet = ai.generate_one(temperature=temperature, prompt=prompt)
        return tweet
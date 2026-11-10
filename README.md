---
language:
- tl
pipeline_tag: text-generation
tags:
- tagalog
- taglish
- conversational
- research
---

# TagaLLM

TagaLLM is a local chat app for everyday Metro Manila Tagalog and Taglish. It is designed for short conversations about family, food, errands, Filipino culture, and changing plans.

## Live configuration

The local demo uses original Google Gemma 4 E2B in Q4 with a Tagalog conversation prompt and a 4,096-token context window. The application adds curated cultural references and uses a separate SEA-LION backend for language and scope checks. The scratch checkpoints and their tokenizer are separate artifacts.

The saved adapter training assets pin [Google Gemma 4 E2B IT revision 4adf15748de9e1a0097b6274cee9c15836c41c37](https://huggingface.co/google/gemma-4-E2B-it/tree/4adf15748de9e1a0097b6274cee9c15836c41c37). The live Q4 GGUF matches the launcher SHA-256 1b71213c391f309cd3775c2fb489591d5806d2f2e59eccf6400d2b96f42fed47. [Google’s model card](https://huggingface.co/google/gemma-4-E2B-it) lists Apache 2.0 for upstream Gemma 4.

## Fine-tuning and evaluation

The culture LoRA pilot used 22 reviewed dialogues. Held-out assistant loss fell from 4.44 to 3.72. Base Gemma and the experimental adapter each fully answered 2 of 6 final requests on the TV development set. The app configuration with cultural references fully answered 4 of 6. The live demo uses base Gemma weights.

In the separate 20-chat E2B development run, 110 of 120 replies received full naturalness marks, 67 of 120 received full relevance marks, and 37 of 72 scored state checks received full marks. Three conversations passed all six exchanges. These scores come from editorial development review. The model can miss updated people, places, and plans, and short Tagalog inputs can occasionally trigger the language check.

A six-exchange pass requires all six replies to earn 2 out of 2 for naturalness and relevance, plus 2 out of 2 on every applicable state-tracking check. Reviewers record a note when state tracking does not apply. The harness requires a nonempty reply on every turn.

Across the 120 logged replies in the reference-enabled E2B development run, the local app took a median of 2.16 seconds per reply. The 95th percentile was 3.03 seconds. These timings come from the guarded development endpoint on the test machine.

## Research artifacts

| Artifact | Release contents |
| --- | --- |
| Scratch checkpoints | 3.75M and 15.5M at 256 tokens, plus 15.52M at 512 tokens. Pair each checkpoint with its tokenizer and dataset snapshot. |
| Custom tokenizer | [Original 2K byte-level BPE](original-bpe-2048.json) for the 256-token runs and [4K BPE](bpe_4096.json) for the 512-token copy comparison. The benchmark covers 721 held-out chats. Gemma uses its own tokenizer. |
| Culture adapter | Experimental LoRA, pinned base revision, training manifest, and matched development outputs. |
| Data and credits | Identify original, adapted, and third-party data by source, role, split, and redistribution status. |

## Historical training datasets

The frozen 256-token snapshot contains 6,142 training conversations and 815 validation conversations. The 15.5M prose-first run also used 84 prose passages. The later 512-token copy comparison used a separately pinned mixture. [Checkpoint and data inventory](evidence.html#frozen-splits)

The public dataset excludes four Voice of America Learning English source families because redistribution permission for the adaptations could not be independently verified. The earlier public staging export already omitted them. The historical 256-token training snapshot contains all four adaptations. Existing weights and reported results belong to their original runs, and the public dataset is a separate release copy.

## Setup

See [local installation](INSTALL.md) and [downloads](downloads.html).

# Embedding Models Directory

This folder stores local embedding models for offline use.

## Setup Instructions

### Download all-MiniLM-L6-v2

1. Go to: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/main
2. Download these files:
   - `config.json`
   - `config_sentence_transformers.json`
   - `modules.json`
   - `pytorch_model.bin` (or `model.safetensors`)
   - `sentence_bert_config.json`
   - `special_tokens_map.json`
   - `tokenizer_config.json`
   - `tokenizer.json`
   - `vocab.txt`

3. Place them in: `models/all-MiniLM-L6-v2/`

### Alternative: Use Git LFS

```bash
git lfs install
git clone https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 models/all-MiniLM-L6-v2
```

### Verify Structure

```
models/
└── all-MiniLM-L6-v2/
    ├── config.json
    ├── config_sentence_transformers.json
    ├── modules.json
    ├── pytorch_model.bin
    ├── sentence_bert_config.json
    ├── special_tokens_map.json
    ├── tokenizer_config.json
    ├── tokenizer.json
    └── vocab.txt
```

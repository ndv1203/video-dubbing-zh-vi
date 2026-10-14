from pathlib import Path
import sentencepiece as spm
import torch

from app.ml.translator.model import TransformerMT


class Translator:
    def __init__(
        self,
        model: TransformerMT,
        src_tokenizer: spm.SentencePieceProcessor,
        tgt_tokenizer: spm.SentencePieceProcessor,
        device: torch.device,
        max_src_len: int = 128,
        max_tgt_len: int = 128,
    ):
        self.model = model
        self.src_tokenizer = src_tokenizer
        self.tgt_tokenizer = tgt_tokenizer
        self.device = device
        self.max_src_len = max_src_len
        self.max_tgt_len = max_tgt_len

    @classmethod
    def load_from_dir(
        cls,
        model_dir: str | Path,
        checkpoint_name: str = "best.pt",
        device: str = "cpu",
    ) -> "Translator":
        dir_path = Path(model_dir)
        checkpoint_path = dir_path / checkpoint_name
        zh_tokenizer_path = dir_path / "tokenizers" / "zh.model"
        vi_tokenizer_path = dir_path / "tokenizers" / "vi.model"

        # Kiểm tra nếu tokenizers nằm cùng thư mục hoặc trong subfolder tokenizers
        if not zh_tokenizer_path.exists():
            zh_tokenizer_path = dir_path / "zh.model"
        if not vi_tokenizer_path.exists():
            vi_tokenizer_path = dir_path / "vi.model"

        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found at: {checkpoint_path}")
        if not zh_tokenizer_path.exists():
            raise FileNotFoundError(f"Chinese tokenizer not found at: {zh_tokenizer_path}")
        if not vi_tokenizer_path.exists():
            raise FileNotFoundError(f"Vietnamese tokenizer not found at: {vi_tokenizer_path}")

        dev = torch.device(device)

        src_tokenizer = spm.SentencePieceProcessor(model_file=str(zh_tokenizer_path))
        tgt_tokenizer = spm.SentencePieceProcessor(model_file=str(vi_tokenizer_path))

        model = TransformerMT(
            src_vocab_size=src_tokenizer.get_piece_size(),
            tgt_vocab_size=tgt_tokenizer.get_piece_size(),
            d_model=256,
            nhead=8,
            num_encoder_layers=4,
            num_decoder_layers=4,
            dim_feedforward=1024,
            dropout=0.1,
            max_src_len=128,
            max_tgt_len=128,
        )

        checkpoint = torch.load(checkpoint_path, map_location=dev, weights_only=True)
        if "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        else:
            model.load_state_dict(checkpoint)

        model.to(dev)
        model.eval()

        return cls(
            model=model,
            src_tokenizer=src_tokenizer,
            tgt_tokenizer=tgt_tokenizer,
            device=dev,
            max_src_len=128,
            max_tgt_len=128,
        )

    def translate_batch(self, sentences: list[str], max_len: int = 100) -> list[str]:
        if not sentences:
            return []

        self.model.eval()
        bos_id = self.tgt_tokenizer.bos_id()
        eos_id = self.tgt_tokenizer.eos_id()
        pad_id = self.tgt_tokenizer.pad_id()

        encoded_batch = []
        for s in sentences:
            ids = self.src_tokenizer.encode(s, out_type=int, add_bos=True, add_eos=True)
            if len(ids) > self.max_src_len:
                ids = ids[: self.max_src_len]
                ids[-1] = self.src_tokenizer.eos_id()
            encoded_batch.append(ids)

        max_batch_len = max(len(seq) for seq in encoded_batch)
        padded_batch = [
            seq + [pad_id] * (max_batch_len - len(seq)) for seq in encoded_batch
        ]

        src_tensor = torch.tensor(padded_batch, dtype=torch.long, device=self.device)
        batch_size = src_tensor.size(0)

        tgt_input = torch.full((batch_size, 1), bos_id, dtype=torch.long, device=self.device)
        finished = torch.zeros(batch_size, dtype=torch.bool, device=self.device)
        src_padding_mask = (src_tensor == pad_id)

        with torch.inference_mode():
            for _ in range(max_len):
                tgt_padding_mask = (tgt_input == pad_id)

                logits = self.model(
                    src=src_tensor,
                    tgt=tgt_input,
                    src_key_padding_mask=src_padding_mask,
                    tgt_key_padding_mask=tgt_padding_mask,
                )

                next_token_logits = logits[:, -1, :]
                next_tokens = next_token_logits.argmax(dim=-1)
                next_tokens = torch.where(finished, pad_id, next_tokens)
                finished = finished | (next_tokens == eos_id)

                tgt_input = torch.cat([tgt_input, next_tokens.unsqueeze(1)], dim=1)

                if finished.all():
                    break

        results = []
        for token_ids in tgt_input.tolist():
            cleaned_ids = [t for t in token_ids if t not in {bos_id, eos_id, pad_id}]
            results.append(self.tgt_tokenizer.decode(cleaned_ids))

        return results

    def translate(self, sentence: str, max_len: int = 100) -> str:
        batch_results = self.translate_batch([sentence], max_len=max_len)
        return batch_results[0] if batch_results else ""


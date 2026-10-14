import math
import torch
import torch.nn as nn


class InputEmbedding(nn.Module):
    def __init__(self, vocab_size: int, d_model: int):
        super().__init__()
        self.d_model = d_model
        self.embedding = nn.Embedding(vocab_size, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.embedding(x) * math.sqrt(self.d_model)


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, seq_len: int, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        pe = torch.zeros(seq_len, d_model)
        position = torch.arange(seq_len).float().unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)

        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:, : x.size(1), :]
        return self.dropout(x)


class TransformerMT(nn.Module):
    def __init__(
        self,
        src_vocab_size: int = 16000,
        tgt_vocab_size: int = 16000,
        d_model: int = 256,
        nhead: int = 8,
        num_encoder_layers: int = 4,
        num_decoder_layers: int = 4,
        dim_feedforward: int = 1024,
        dropout: float = 0.1,
        max_src_len: int = 128,
        max_tgt_len: int = 128,
    ):
        super().__init__()

        self.src_embedding = InputEmbedding(src_vocab_size, d_model)
        self.tgt_embedding = InputEmbedding(tgt_vocab_size, d_model)

        self.src_pos_encoding = PositionalEncoding(d_model, max_src_len, dropout)
        self.tgt_pos_encoding = PositionalEncoding(d_model, max_tgt_len, dropout)

        self.transformer = nn.Transformer(
            d_model=d_model,
            nhead=nhead,
            num_encoder_layers=num_encoder_layers,
            num_decoder_layers=num_decoder_layers,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
            norm_first=True,
        )

        self.projection_layer = nn.Linear(d_model, tgt_vocab_size)

    def forward(
        self,
        src: torch.Tensor,
        tgt: torch.Tensor,
        src_key_padding_mask: torch.Tensor | None = None,
        tgt_key_padding_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        src = self.src_embedding(src)
        src = self.src_pos_encoding(src)

        tgt = self.tgt_embedding(tgt)
        tgt = self.tgt_pos_encoding(tgt)

        tgt_len = tgt.size(1)
        tgt_mask = nn.Transformer.generate_square_subsequent_mask(
            tgt_len, device=tgt.device
        )

        output = self.transformer(
            src=src,
            tgt=tgt,
            tgt_mask=tgt_mask,
            src_key_padding_mask=src_key_padding_mask,
            tgt_key_padding_mask=tgt_key_padding_mask,
            memory_key_padding_mask=src_key_padding_mask,
        )

        return self.projection_layer(output)


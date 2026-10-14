import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.ml.translator import Translator


def main():
    repo_root = Path(__file__).resolve().parent.parent
    model_dir = repo_root / "models" / "translator_zh_vi"

    print(f"Loading translator from: {model_dir}")
    translator = Translator.load_from_dir(
        model_dir=model_dir,
        checkpoint_name="best.pt",
        device="cpu",
    )
    print("Model loaded successfully onto CPU!\n")

    test_sentences = [
        "你好，世界！",
        "今天天气怎么样？",
        "我是越南人。",
    ]

    for sentence in test_sentences:
        translation = translator.translate(sentence)
        print(f"🇨🇳 Input:  {sentence}")
        print(f"🇻🇳 Output: {translation}")
        print("-" * 40)


if __name__ == "__main__":
    main()


"""Execute com: python main.py"""
import argparse
from pathlib import Path

import httpx
from dotenv import load_dotenv

from app.llm.llm_client import Conversation, LLMClient, LLMError, Settings


def main() -> int:
    load_dotenv(Path(__file__).with_name(".env"))
    parser = argparse.ArgumentParser(description="AI Technical Assistant — Fase 1")
    parser.add_argument("--question", help="Faz uma pergunta e encerra.")
    args = parser.parse_args()
    try:
        settings = Settings.from_env()
    except ValueError as exc:
        print(f"Configuração inválida: {exc}")
        return 1
    print(f"AI Technical Assistant | {settings.model}")
    print("Sem RAG: respostas ainda não consultam documentação própria.")
    with httpx.Client() as http:
        conversation = Conversation(LLMClient(settings, http))
        if not args.question:
            print("Comandos: /clear limpa o histórico; /exit encerra.")
        while True:
            try:
                question = args.question if args.question is not None else input("\n> ")
                question = question.strip()
                if question == "/exit":
                    return 0
                if question == "/clear":
                    conversation.clear()
                    print("Histórico limpo.")
                    if args.question is not None:
                        return 0
                    continue
                if not question:
                    if args.question is not None:
                        print("A pergunta não pode estar vazia.")
                        return 1
                    continue
                reply = conversation.ask(question)
                print(f"\nAssistant:\n{reply.text}")
                print(f"\n[tokens: entrada={reply.prompt_tokens}, saída={reply.output_tokens}; "
                      f"tempo Ollama={reply.seconds:.2f}s]")
                if reply.truncated:
                    print("[Resposta atingiu NUM_PREDICT; pode estar incompleta.]")
            except LLMError as exc:
                print(f"Erro: {exc}")
                if args.question is not None:
                    return 1
            except (EOFError, KeyboardInterrupt):
                print("\nAté mais!")
                return 0
            if args.question is not None:
                return 0


if __name__ == "__main__":
    raise SystemExit(main())

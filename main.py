import asyncio
import click


class CLI:
    def __init__(self):
        pass

    def run_single(self):
        pass


@click.command()
@click.argument("prompt", required=False)
def main(prompt: str | None):
    print(prompt)
    message = [{"role": "user", "content": prompt}]
    asyncio.run(run(message))
    print("Done")


if __name__ == "__main__":
    main()

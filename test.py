import click

@click.command()
@click.option('--count', default=1, help='Số lần lặp lại lời chào.')
@click.argument('name')
def hello(count, name):
    """Chương trình chào hỏi đơn giản dùng Click."""
    for _ in range(count):
        click.echo(f"Xin chào, {name}!")

if __name__ == "__main__":
    hello()
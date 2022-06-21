import io
import re

from PIL import Image
import click
import requests

from cli.app import App


@click.group()
def cli():
    pass


@cli.group()
def books():
    pass


@books.command()
def add():
    click.clear()

    # Setup resource providers
    app = App()
    categories = app.the_base_client.categories.get()

    # click.echo("Enter input file .txt, same directory as running script, format isbn,book_id")

    isbn = input("Enter ISBN: \n")
    simple_info = app.google_books.search_by_isbn(isbn)

    book_id = input("Book ID: \n")
    book_cat = re.sub(r'\d+', '', book_id)
    book_cat_id = categories[book_cat]

    if simple_info is None:
        click.echo(f"Book {isbn} not found. Maybe try different ISBN format (ISBN10, ISBN13)?")
        exit(0)

    click.echo()
    title = simple_info["title"]
    authors = simple_info["authors"]
    click.echo(f"Title: {title}")
    click.echo(f"Author(s): {', '.join(authors)}")

    click.echo()
    click.echo("Add or modify the description as you see fit, SAVE the text file before close it")
    description = click.edit(simple_info['description'])
    click.echo(f"Description: {description}")

    click.echo()
    img_link = simple_info.get("image")
    if img_link is None:
        click.echo("Finding book covers with Google image search...")
        links = app.cse_image.search_for_links(f"{title} {authors[0]} books")

        response = requests.get(links[0])
        image_bytes = io.BytesIO(response.content)
        img = Image.open(image_bytes)
        img.show()

        click.echo("Is this cover OK? (y)es/(n)o")
        while True:
            c = click.getchar()
            if c == 'y':
                img_link = links[0]
                break
            elif c == 'n':
                click.echo("You can: (1) paste an image link or (2) continue without an image")
                while True:
                    c = click.getchar()
                    if c == '1':
                        img_link = input("Image link: \n")
                        break
                    elif c == '2':
                        click.echo("Continuing without book cover")
                        break
                break

        click.echo("Creating item...")
        resp = app.the_base_client.items.add({
            "title": title,
            "detail": description
        })
        item_id = resp["item"]["item_id"]

        click.echo("Adding category to item...")
        app.the_base_client.item_categories.add(item_id, book_cat_id)

        if img_link is not None:
            click.echo("Adding image to item...")
            app.the_base_client.items.add_image(item_id, img_link)

        click.echo("終了しました！")

#!/usr/bin/env python
from bs4 import BeautifulSoup
from click import command
from utz import *


@command()
def main():
    n = now()
    df = (
        pd.DataFrame([
            dict(
                unit=u,
                **{
                    b: c(getattr(n, u))
                    for b, c in { 'b62': b62, 'b64': b64, 'b90': b90 }.items()
                }
            )
            for u in ['s', 'ds', 'cs', 'ms', 'us']
        ])
        .set_index('unit')
    )
    html = df.to_html()
    soup = BeautifulSoup(html, 'html.parser')

    # Find the table and its header rows
    table = soup.find('table')
    header_rows = table.find_all('tr')[:2]

    # Combine the content of the two header rows
    combined_headers = []
    for i in range(len(header_rows[0].find_all('th'))):
        header1 = header_rows[0].find_all('th')[i].text.strip()
        header2 = header_rows[1].find_all('th')[i].text.strip()
        combined_header = f"{header1} {header2}".strip()
        combined_headers.append(combined_header)

    # Remove the second header row
    header_rows[1].decompose()

    # Update the first header row with the combined content
    for i, th in enumerate(header_rows[0].find_all('th')):
        th.string = combined_headers[i]

    print(soup)


if __name__ == '__main__':
    main()

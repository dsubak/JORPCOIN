import argparse
import os
import traceback
import urllib

from bs4 import BeautifulSoup
import requests
import textract


# Dumb script to grab PDFs from the posts on https://whitepaperdatabase.com
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d',
                        '--download',
                        help='Download whitepapers',
                        action='store_true',
                        default=False)
    parser.add_argument('-e',
                        '--extract',
                        help='Extract text from whitepapers',
                        action='store_true',
                        default=False)
    parser.add_argument('-c',
                        '--clean',
                        help='Clean extracted text',
                        action='store_true',
                        default=False)
    args = parser.parse_args()
    if args.download:
        download_pdfs()
    if args.extract:
        extract_text()
    if args.clean:
        clean_extracted_text()


def download_pdfs():
    pdf_dir = os.path.join(os.path.dirname(__file__), 'raw_whitepapers')
    already_downloaded = os.listdir(pdf_dir)
    with open(os.path.join(os.path.dirname(__file__), 'whitepapers.txt'), 'r') as whitepaper_urls:
        for line in whitepaper_urls:
            print('Processing {}'.format(line))
            whitepaper_page_response = requests.get(line)
            if whitepaper_page_response.status_code == 200:
                print('Parsing HTML for {}'.format(line))
                soup = BeautifulSoup(whitepaper_page_response.text)
                potential_source_links = soup.find_all('a')
                for link in potential_source_links:
                    pdf_link = link.get('href')
                    if pdf_link and pdf_link.endswith('pdf'):
                        print('Downloading {}'.format(pdf_link))
                        # Download the PDF
                        local_filename = pdf_link.split('/')[-1]
                        if local_filename in already_downloaded:
                            print('Skipping {}'.format(local_filename))
                            continue
                        try:
                            urllib.request.urlretrieve(pdf_link, '{}/{}'.format(pdf_dir, local_filename))
                        except (urllib.error.HTTPError, UnicodeEncodeError) as exc:
                            print('Couldn\'t get file {}'.format(pdf_link))
                            traceback.print_exc()
                        print('Saved {}'.format(local_filename))

def extract_text():
    raw_pdf_dir = os.path.join(os.path.dirname(__file__), 'raw_whitepapers')
    processed_pdf_dir = os.path.join(os.path.dirname(__file__), 'processed_whitepapers')
    pdf_filenames = os.listdir(raw_pdf_dir)
    for item in pdf_filenames:
        print('OUTPUT {}'.format(item))
        try:
            text = textract.process('{}/{}'.format(raw_pdf_dir, item))
        except textract.exceptions.ShellError as exc:
            traceback.print_exc()
            print('Skipping {}'.format(item))
            continue
        with open('{}/{}'.format(processed_pdf_dir, item.replace('.pdf', '')), 'w') as output_file:
            output_file.write(str(text, 'utf-8'))

def retrieve_references(raw_text):
    # TODO: This still can't handle 2-column PDFs. Will probably need bespoke handling
    references = []
    possible_multiline_reference = False
    for line in raw_text.splitlines():
        if line.startswith('[') and len(line) > 2 and line[1].isnumeric():
            references.append(line.strip())
            possible_multiline_reference = True
        elif possible_multiline_reference and not line.startswith('['):
            references[-1] = references[-1] + line.strip()
            possible_multiline_reference = False
        else:
            possible_multiline_reference = False
    return references

def is_single_column(raw_text):
    # TODO: This is gonna be difficult to solve, but try to come up with a reasonable heuristic.
    # 2 Column PDFs are much harder to clean up.
    return True

def strip_figures(raw_text):
    # TODO: Actually strip text of figures and other mathematical constructs that dont make for a good corpus
    return raw_text

def clean_extracted_text():
    processed_pdf_dir = os.path.join(os.path.dirname(__file__), 'processed_whitepapers')
    cleaned_text_dir = os.path.join(os.path.dirname(__file__), 'cleaned_text')
    text_filenames = os.listdir(processed_pdf_dir)
    for item in text_filenames:
        print('Processing {}'.format(item))
        with open('{}/{}'.format(processed_pdf_dir, item), 'r') as input_file:
            raw_text = input_file.read()
        if is_single_column(raw_text):
            references = retrieve_references(raw_text)
            processed_text = strip_figures(raw_text)
            # TODO: Do the rest of the single column processing
            print(references)
        else:
            # TODO: Figure out if it's tractable to process the 2 column PDFs. If not, skip em.
            pass

        # Write it out if we get here - probably as good as we'll be able to do.
        with open('{}/{}_cleaned'.format(cleaned_text_dir, item)) as output_file:
            output_file.write(processed_text)



if __name__ == '__main__':
    main()
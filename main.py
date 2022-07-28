from PyPDF2 import PdfFileReader, PdfFileWriter
import os
import logging
from collections import defaultdict
import argparse

PAGE_KEY = '/P'
logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("--input-path", type=str, dest="in_path", required=True)
parser.add_argument("--output-path", type=str, dest="out_path", default=None, required=False)



def get_pages_map(pdf):
    raw_trailer = pdf.trailer["/Root"]["/PageLabels"]["/Nums"]
    total_pages = int(raw_trailer[-1][PAGE_KEY])
    result = defaultdict(list)
    i = 0
    # Assume len(raw_trailer) is even
    while i < len(raw_trailer):
        pdf_page_num = raw_trailer[i]
        pdf_actual_page = raw_trailer[i+1]
        i = i + 2

        if not PAGE_KEY in pdf_actual_page:
            continue

        actual_page_num = int(pdf_actual_page[PAGE_KEY])
        result[actual_page_num].append(pdf_page_num)

    logging.debug("Raw pages map: %s", result)

    # post process to get real result
    post_processed_result = {}
    for real_page_num in range(1,total_pages):
        # check if slide has stops
        if max(result[real_page_num+1]) - max(result[real_page_num]) > 1:
            post_processed_result[real_page_num] = max(result[real_page_num+1])-1
        else:
            post_processed_result[real_page_num] = max(result[real_page_num])

    post_processed_result[total_pages] = pdf.getNumPages()-1

    return post_processed_result

def get_extraction_list_in_order(pages_map, total_pages):
    extraction_list = []
    for i in range(1, total_pages+1):
        extraction_list.append(pages_map[i])

    return extraction_list

if __name__ == "__main__":
    args = parser.parse_args()

    in_path = args.in_path
    out_path = args.out_path
    if out_path is None:
        out_path = get_default_out_path(in_path)

    logging.info("Reading [%s] and writing to [%s]", in_path, out_path)

    pdf = PdfFileReader(in_path)
    out = PdfFileWriter()

    pm = get_pages_map(pdf)
    el = get_extraction_list_in_order(pm, max(pm.keys()))

    for el_page in el:
        out.addPage(pdf.pages[el_page])

    logging.info("Writing output pdf with %d pages. Reduced from %d total pages", len(el), pdf.getNumPages())
    with open(out_path, "wb") as out_file:
        out.write(out_file)
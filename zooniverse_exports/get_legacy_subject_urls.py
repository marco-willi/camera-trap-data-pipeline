""" Get Zooniverse urls from Oruborous API
    # pip install --user aiohttp
"""
import aiohttp
import asyncio
from aiohttp.client_exceptions import ContentTypeError
from contextlib import closing
import time
import os
import pandas as pd
import textwrap
import traceback
import argparse

from utils import (
    slice_generator,
    read_config_file, estimate_remaining_time, set_file_permission)


def get_oroboros_api_data(subject_ids, quality='standard', batch_size=1000):
    api_path = 'https://api.zooniverse.org/projects/serengeti/subjects/'
    res_dict = dict()
    time_start = time.time()
    n_total = len(subject_ids)
    n_remaining = n_total
    n_finished = 0
    url_list = [api_path + x for x in subject_ids]
    n_blocks = int(n_total/ batch_size)
    slices = slice_generator(n_total, n_blocks)
    # loop over chunks
    for i, (start_i, end_i) in enumerate(slices):
        print("    Starting with sub-batch {}".format(i))
        batch_urls = url_list[start_i: end_i]
        n_batch = len(batch_urls)
        tasks = []
        res = []
        for url in batch_urls:
            tasks.append(fetch_page(url, res))
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(*tasks))
        # extract data
        data = [extract_image_urls(x, quality) for x in res if x is not None]
        n_batch_success = len(data)
        print("    Sub-Batch {} finished {:5}/{:5}".format(
            i, n_batch_success, len(batch_urls)))
        data_dict = {k:v for k, v in data}
        # add data
        res_dict = {**res_dict, **data_dict}
    return res_dict


async def fetch(session, url):
    async with session.get(url) as response:
        try:
            return await response.json()
        except ContentTypeError:
            print("Failed to extract url: {}".format(url))
        except Exception:
            print(traceback.format_exc())

async def fetch_page(url, res):
    async with aiohttp.ClientSession() as session:
        page = await fetch(session, url)
        res.append(page)

def extract_image_urls(page, quality):
    """ extract relevant info from pages """
    _id = page['zooniverse_id']
    try:
        url_list = page['location'][quality]
    except:
        url_list = page['location']['standard']
    if len(url_list) > 3:
        url_list = url_list[0:3]
    return _id, url_list


# for season in range(1, 11):
#     input_path = '/home/packerc/shared/zooniverse/Exports/SER/SER_S{}_subjects_extracted.csv'.format(season)
#     output_path = '/home/packerc/shared/zooniverse/Exports/SER/SER_S{}_subjects_urls.csv'.format(season)
#     df = pd.read_csv(input_path,na_values=str)
#     subject_ids = df['subject_id']
#     api_path = 'https://api.zooniverse.org/projects/serengeti/subjects/'
#     urls = get_oroboros_api_data(subject_ids, quality='large', batch_size=50)
#     df_out = pd.DataFrame.from_dict(urls, orient='index')
#     cols = df_out.columns.tolist()
#     df_out.columns = ['zooniverse_url_0', 'zooniverse_url_1', 'zooniverse_url_2']
#     df_out.sort_index(inplace=True)
#     df_out.index.name = 'subject_id'
#     df_out.to_csv(output_path, index=True)
#     set_file_permission(output_path)

# args = dict()
# args['subjects_extracted'] = '/home/packerc/shared/zooniverse/Exports/SER/SER_S1_subjects_extracted.csv'
# args['subjects_urls'] = '/home/packerc/shared/zooniverse/Exports/SER/SER_S1_subjects_urls.csv'

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects_extracted", type=str, required=True)
    parser.add_argument("--subjects_urls", type=str, required=True)
    args = vars(parser.parse_args())
    # read subject data, fetch urls via oroboros API and save to disk
    input_path = args['subjects_extracted']
    output_path = args['subjects_urls']
    df = pd.read_csv(input_path, na_values=str)
    subject_ids = df['subject_id']
    api_path = 'https://api.zooniverse.org/projects/serengeti/subjects/'
    # read from disk if already exists
    if os.path.isfile(output_path):
        print("reading file {}".format(output_path))
        df_out = pd.read_csv(output_path, na_values=str)
        # remove already processed
        df.drop(df.index[df_out.index], inplace=True)
        print("Remaining records to process: {}".format(df.size))
        output_file_exists = True
    else:
        output_file_exists = False
    # read in batches
    time_start = time.time()
    n_total = df.size
    n_finished = 0
    n_blocks = int(n_total / 5000)
    slices = slice_generator(n_total, n_blocks)
    for batch_id, (i_start, i_end) in enumerate(slices):
        subjects_batch = subject_ids[i_start:i_end]
        finished_batch = False
        # re-try on timeouts
        while not finished_batch:
            try:
                urls = get_oroboros_api_data(
                    subjects_batch, quality='large', batch_size=50)
                finished_batch = True
            except KeyboardInterrupt:
                finished_batch = True
            except:
                pass
        df_out = pd.DataFrame.from_dict(urls, orient='index')
        cols = df_out.columns.tolist()
        df_out.columns = [
            'zooniverse_url_0', 'zooniverse_url_1', 'zooniverse_url_2']
        df_out.sort_index(inplace=True)
        df_out.index.name = 'subject_id'
        if output_file_exists:
            df_out.to_csv(output_path, index=True, mode='a', header=False)
            print("Append data to {}".format(output_path))
        else:
            df_out.to_csv(output_path, index=True)
            output_file_exists = True
            print("Write data to {}".format(output_path))
        set_file_permission(output_path)
        # print progress information
        ts = time.time()
        n_finished += len(subjects_batch)
        tr = estimate_remaining_time(
            time_start, n_total, n_finished)
        msg = "Saved %s/%s (%s %%) - \
               Estimated Time Remaining: %s" % \
              (n_finished, n_total,
               round((n_finished/n_total) * 100, 2), tr)
        print(textwrap.shorten(msg, width=99))

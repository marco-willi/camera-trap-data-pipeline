""" Get Zooniverse Data from Ouroboros API
    # pip install --user aiohttp
"""
import aiohttp
import asyncio
import time
import os
import pandas as pd
import json
import textwrap
import argparse
import math

from utils import (
    slice_generator,
    estimate_remaining_time, set_file_permission)


async def fetch(session, url):
    async with session.get(url) as response:
        assert response.status == 200
        return await response.json()


async def fetch_urls(urls):
    tasks = []
    async with aiohttp.ClientSession() as session:
        for url in urls:
            tasks.append(fetch(session, url))
        results = await asyncio.gather(*tasks)
        return results


def get_oroboros_api_data(subject_ids, quality='standard', batch_size=1000):
    api_path = 'https://api.zooniverse.org/projects/serengeti/subjects/'
    res_dict = dict()
    n_total = len(subject_ids)
    url_list = [api_path + x for x in subject_ids]
    n_blocks = math.ceil(n_total / batch_size)
    slices = slice_generator(n_total, n_blocks)
    # loop over chunks
    for i, (start_i, end_i) in enumerate(slices):
        print("    Starting with sub-batch {}".format(i))
        batch_urls = url_list[start_i: end_i]
        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(fetch_urls(batch_urls))
        res_batch_dict = {r['zooniverse_id']: r for r in res}
        n_batch_success = len(res_batch_dict)
        print("    Sub-Batch {} finished {:5}/{:5}".format(
            i, n_batch_success, len(batch_urls)))
        res_dict = {**res_dict, **res_batch_dict}
    return res_dict

# args = dict()
# args['subjects_extracted'] = '/home/packerc/shared/zooniverse/Exports/SER/SER_S1_subjects_extracted.csv'
# args['subjects_ouroboros'] = '/home/packerc/shared/zooniverse/Exports/SER/SER_S1_subjects_ouroboros.json'


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects_extracted", type=str, required=True)
    parser.add_argument("--subjects_ouroboros", type=str, required=True)
    args = vars(parser.parse_args())
    # read subject data, fetch urls via oroboros API and save to disk
    input_path = args['subjects_extracted']
    output_path = args['subjects_ouroboros']
    df = pd.read_csv(input_path, na_values=str, index_col='subject_id')
    subject_ids = df.index
    print("Total {} subjects found".format(len(subject_ids)))
    # read from disk if already exists
    if os.path.isfile(output_path):
        with open(output_path, 'r') as f:
            df_out = json.load(f)
        print("reading file {}".format(output_path))
        print("read {} records".format(len(df_out)))
        processed_subjects = df_out.keys()
        res_dict_all = df_out
    else:
        res_dict_all = {}
    # remove already processed
    subject_ids = list(set(subject_ids) - res_dict_all.keys())
    print("Records remaining for processing: {}".format(len(subject_ids)))
    # read in batches
    time_start = time.time()
    n_total = df.shape[0]
    n_finished = 0
    n_blocks = math.ceil(n_total / 5000)
    slices = slice_generator(n_total, n_blocks)
    for batch_id, (i_start, i_end) in enumerate(slices):
        subjects_batch = subject_ids[i_start:i_end]
        finished_batch = False
        # re-try on timeouts
        while not finished_batch:
            try:
                urls_dict = get_oroboros_api_data(
                    subjects_batch, batch_size=50)
                finished_batch = True
            except KeyboardInterrupt:
                finished_batch = True
            except TimeoutError:
                print("Timeout error... sleep for 60s")
                time.sleep(60)
            except:
                print("Unkown error ocurred... try again..")
                pass
        res_dict_all = {**res_dict_all, **urls_dict}
        with open(output_path, 'w') as f:
            json.dump(res_dict_all, f)
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
